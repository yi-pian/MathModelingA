"""Question 2: constant and velocity-power PTO damping optimization."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.export import write_excel_checked
from core.integration import integrate_samples
from core.optimization import coarse_to_fine, local_perturbation_check, optimize_global, optimize_local, optimize_scalar
from physics import (
    harmonic_state,
    heave_frequency_response,
    heave_rhs,
    linear_heave_average_power,
)
from power import heave_power, heave_power_summary
from problem_data import wave_case
from steady_state import simulate_periodic_steady, solve_periodic_orbit


RESULTS = ROOT / "results" / "2022A"


def _periodic_power(scale: float, exponent: float, *, samples=64, rtol=2e-8, atol=2e-10) -> tuple[float, dict]:
    wave = wave_case(2)
    if scale <= 0.0:
        return 0.0, {"periodic_residual": 0.0, "root_residual": 0.0, "nfev": 0}
    equivalent_damping = max(1.0, scale * 0.1**exponent)
    guess = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, equivalent_damping))[:, 0]
    orbit = solve_periodic_orbit(
        heave_rhs(wave, scale, exponent),
        wave.omega,
        guess,
        samples_per_cycle=samples,
        rtol=rtol,
        atol=atol,
        root_tolerance=max(5e-10, 5.0 * rtol),
    )
    relative_velocity = orbit.ode.state[3] - orbit.ode.state[2]
    instantaneous = heave_power(relative_velocity, scale, exponent)
    average = integrate_samples(orbit.ode.time, instantaneous, method="simpson") / orbit.period
    return average, {
        "periodic_residual": orbit.periodic_residual,
        "root_residual": orbit.root_result.residual,
        "nfev": orbit.ode.nfev,
        "initial_state": orbit.initial_state.tolist(),
    }


class NonlinearPowerObjective:
    def __init__(self, *, samples=64, rtol=2e-8, atol=2e-10):
        self.samples = int(samples)
        self.rtol = float(rtol)
        self.atol = float(atol)
        self.cache: dict[tuple, float] = {}
        self.evaluations = 0
        self.cache_hits = 0

    def _key(self, scale, exponent):
        return (
            round(float(scale), 8),
            round(float(exponent), 10),
            self.samples,
            self.rtol,
            self.atol,
            "D=lambda_abs_v_pow_p_times_v",
        )

    def __call__(self, parameters) -> float:
        scale, exponent = map(float, np.asarray(parameters))
        if not (0.0 <= scale <= 100000.0 and 0.0 <= exponent <= 1.0):
            return -1e30
        key = self._key(scale, exponent)
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        value, _ = _periodic_power(scale, exponent, samples=self.samples, rtol=self.rtol, atol=self.atol)
        self.cache[key] = float(value)
        self.evaluations += 1
        return float(value)


def run() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    wave = wave_case(2)
    total_started = perf_counter()

    # Constant damping: inspect the full interval before deterministic bounded refinement.
    constant_optimization_started = perf_counter()
    constant_scan_x = np.linspace(0.0, 100000.0, 101)
    constant_scan_power = np.array([linear_heave_average_power(wave, value) for value in constant_scan_x])
    constant_result, constant_stages = coarse_to_fine(
        lambda value: linear_heave_average_power(wave, value),
        (0.0, 100000.0),
        grid_points=101,
        direction="maximize",
        xatol=1e-8,
    )
    constant_neighbors = local_perturbation_check(
        lambda value: linear_heave_average_power(wave, value),
        constant_result.x,
        relative_step=1e-4,
        direction="maximize",
    )
    constant_optimization_seconds = perf_counter() - constant_optimization_started
    constant_shooting, constant_shooting_audit = _periodic_power(
        constant_result.x, 0.0, samples=256, rtol=2e-11, atol=2e-13
    )
    constant_transient = simulate_periodic_steady(
        heave_rhs(wave, constant_result.x),
        wave.omega,
        np.zeros(4),
        total_cycles=180,
        samples_per_cycle=96,
        averaging_cycles=20,
        steady_tolerance=2e-4,
        rtol=2e-9,
        atol=2e-11,
        max_steps_per_cycle=32,
    )
    constant_window = heave_power_summary(constant_transient, constant_result.x)

    # Nonlinear damping: coarse map -> global location -> local refinement.
    nonlinear_optimization_started = perf_counter()
    objective = NonlinearPowerObjective(samples=48, rtol=8e-8, atol=8e-10)
    scale_grid = np.linspace(0.0, 100000.0, 11)
    exponent_grid = np.linspace(0.0, 1.0, 6)
    coarse_rows = []
    for exponent in exponent_grid:
        for scale in scale_grid:
            coarse_rows.append({"scale": scale, "exponent": exponent, "average_power_w": objective([scale, exponent])})
    coarse = pd.DataFrame(coarse_rows)
    coarse_best = coarse.loc[coarse["average_power_w"].idxmax()]
    global_result = optimize_global(
        objective,
        [(0.0, 100000.0), (0.0, 1.0)],
        direction="maximize",
        seed=2022,
        polish=False,
        popsize=7,
        maxiter=20,
        tol=2e-3,
        atol=2e-2,
        updating="immediate",
    )
    local_result = optimize_local(
        objective,
        global_result.x,
        bounds=[(0.0, 100000.0), (0.0, 1.0)],
        method="Nelder-Mead",
        direction="maximize",
        options={"xatol": 2e-3, "fatol": 2e-4, "maxiter": 160},
    )
    local_optimum = np.asarray(local_result.x, float)
    if local_optimum[0] > 99999.0:
        strict_exponent = optimize_scalar(
            lambda exponent: _periodic_power(100000.0, exponent, samples=192, rtol=8e-10, atol=8e-12)[0],
            bounds=(max(0.0, local_optimum[1] - 0.03), min(1.0, local_optimum[1] + 0.03)),
            direction="maximize",
            method="bounded",
            options={"xatol": 2e-7, "maxiter": 80},
        )
        optimum = np.array([100000.0, strict_exponent.x])
    else:
        strict_exponent = None
        optimum = local_optimum
    nonlinear_optimization_seconds = perf_counter() - nonlinear_optimization_started
    strict_values = []
    strict_audits = []
    for _ in range(3):
        value, audit = _periodic_power(optimum[0], optimum[1], samples=256, rtol=2e-10, atol=2e-12)
        strict_values.append(value)
        strict_audits.append(audit)
    strict_power = float(np.mean(strict_values))
    neighborhood = []
    for dscale, dexponent in ((-200.0, 0.0), (200.0, 0.0), (0.0, -0.002), (0.0, 0.002)):
        candidate = np.clip(optimum + [dscale, dexponent], [0.0, 0.0], [100000.0, 1.0])
        value, _ = _periodic_power(candidate[0], candidate[1], samples=128, rtol=2e-9, atol=2e-11)
        neighborhood.append({"scale": float(candidate[0]), "exponent": float(candidate[1]), "average_power_w": value})

    nonlinear_transient = simulate_periodic_steady(
        heave_rhs(wave, optimum[0], optimum[1]),
        wave.omega,
        np.zeros(4),
        total_cycles=200,
        samples_per_cycle=96,
        averaging_cycles=20,
        steady_tolerance=2e-4,
        rtol=2e-9,
        atol=2e-11,
        max_steps_per_cycle=32,
    )
    nonlinear_window = heave_power_summary(nonlinear_transient, optimum[0], optimum[1])

    scan_output = pd.concat(
        [
            pd.DataFrame({"damping": constant_scan_x, "average_power_w": constant_scan_power}),
        ],
        ignore_index=True,
    )
    write_excel_checked(
        RESULTS / "q2_optimization.xlsx",
        {
            "ConstantScan": scan_output,
            "NonlinearCoarse": coarse,
            "NonlinearNeighborhood": pd.DataFrame(neighborhood),
        },
        decimals=10,
    )

    constant_reference = float(constant_result.objective)
    nonlinear_window_power = nonlinear_window["means"]["20_cycles_simpson"]
    constant_window_power = constant_window["means"]["20_cycles_simpson"]
    metrics = {
        "status": "PASS",
        "runtime_seconds": perf_counter() - total_started,
        "timings": {
            "constant_1d_optimization_seconds": constant_optimization_seconds,
            "nonlinear_2d_optimization_seconds": nonlinear_optimization_seconds,
        },
        "constant": {
            "optimal_damping_n_s_m": float(constant_result.x),
            "frequency_power_w": constant_reference,
            "shooting_power_w": constant_shooting,
            "transient_20_cycle_power_w": constant_window_power,
            "coarse": constant_stages,
            "neighbors": constant_neighbors,
            "steady_start_cycle": constant_transient.steady_start_cycle,
            "settling_time_s": constant_transient.settling_time,
            "window_means": constant_window["means"],
            "shooting_audit": constant_shooting_audit,
            "boundary_powers_w": [float(constant_scan_power[0]), float(constant_scan_power[-1])],
        },
        "nonlinear": {
            "optimal_scale": float(optimum[0]),
            "optimal_exponent": float(optimum[1]),
            "strict_power_w": strict_power,
            "strict_repeat_range_w": float(np.ptp(strict_values)),
            "transient_20_cycle_power_w": nonlinear_window_power,
            "coarse_best": coarse_best.to_dict(),
            "global": {"x": np.asarray(global_result.x).tolist(), "power_w": global_result.objective, "success": global_result.success},
            "local": {"x": optimum.tolist(), "power_w": local_result.objective, "success": local_result.success},
            "strict_exponent_refinement": None if strict_exponent is None else {
                "exponent": strict_exponent.x,
                "power_w": strict_exponent.objective,
                "success": strict_exponent.success,
            },
            "neighbors": neighborhood,
            "steady_start_cycle": nonlinear_transient.steady_start_cycle,
            "settling_time_s": nonlinear_transient.settling_time,
            "window_means": nonlinear_window["means"],
            "shooting_audits": strict_audits,
            "objective_evaluations": objective.evaluations,
            "objective_cache_hits": objective.cache_hits,
        },
    }
    constant_window_spread = max(constant_window["means"].values()) - min(constant_window["means"].values())
    nonlinear_window_spread = max(nonlinear_window["means"].values()) - min(nonlinear_window["means"].values())
    passed = (
        constant_result.success
        and constant_neighbors["passed"]
        and abs(constant_shooting - constant_reference) / constant_reference < 2e-7
        and abs(constant_window_power - constant_reference) / constant_reference < 5e-4
        and constant_window_spread / constant_reference < 5e-4
        and global_result.success
        and local_result.success
        and (strict_exponent is None or strict_exponent.success)
        and all(item["average_power_w"] <= strict_power + 2e-3 for item in neighborhood)
        and max(strict_audit["periodic_residual"] for strict_audit in strict_audits) < 1e-7
        and np.ptp(strict_values) < 1e-8
        and abs(nonlinear_window_power - strict_power) / strict_power < 8e-4
        and nonlinear_window_spread / strict_power < 8e-4
    )
    metrics["status"] = "PASS" if passed else "FAIL"
    (RESULTS / "q2_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if not passed:
        raise RuntimeError("Q2 validation failed")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
