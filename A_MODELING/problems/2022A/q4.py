"""Question 4: joint constant heave and pitch PTO damping optimization."""

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
from core.optimization import coarse_to_fine, optimize_global, optimize_local, optimize_scalar
from physics import (
    coupled_rhs,
    harmonic_state,
    heave_frequency_response,
    linear_heave_average_power,
    linear_pitch_average_power,
    nonlinear_coupled_rhs,
    pitch_frequency_response,
)
from power import heave_power, nonlinear_coupled_power_summary, rotational_power
from problem_data import wave_case
from steady_state import simulate_periodic_steady, solve_periodic_orbit


RESULTS = ROOT / "results" / "2022A"


def frequency_power(parameters) -> float:
    linear_damping, rotational_damping = map(float, np.asarray(parameters))
    if not (0.0 <= linear_damping <= 100000.0 and 0.0 <= rotational_damping <= 100000.0):
        return -1e30
    wave = wave_case(4)
    return linear_heave_average_power(wave, linear_damping) + linear_pitch_average_power(wave, rotational_damping)


def _periodic_coupled_power(linear_damping: float, rotational_damping: float, *, samples, rtol, atol):
    wave = wave_case(4)
    heave_guess = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, linear_damping))[:, 0]
    pitch_guess = harmonic_state([0.0], wave.omega, pitch_frequency_response(wave, rotational_damping))[:, 0]
    guess = np.array(
        [
            heave_guess[1] - heave_guess[0],
            heave_guess[0],
            pitch_guess[0],
            pitch_guess[1],
            heave_guess[3] - heave_guess[2],
            heave_guess[2],
            pitch_guess[2],
            pitch_guess[3],
        ]
    )
    orbit = solve_periodic_orbit(
        nonlinear_coupled_rhs(wave, linear_damping, rotational_damping),
        wave.omega,
        guess,
        samples_per_cycle=samples,
        rtol=rtol,
        atol=atol,
        root_tolerance=max(5e-10, 5.0 * rtol),
    )
    relative_velocity = orbit.ode.state[4]
    relative_omega = orbit.ode.state[7] - orbit.ode.state[6]
    heave_values = heave_power(relative_velocity, linear_damping)
    rotation_values = rotational_power(relative_omega, rotational_damping)
    heave_average = integrate_samples(orbit.ode.time, heave_values, method="simpson") / orbit.period
    rotation_average = integrate_samples(orbit.ode.time, rotation_values, method="simpson") / orbit.period
    return {
        "heave_power_w": heave_average,
        "rotation_power_w": rotation_average,
        "total_power_w": heave_average + rotation_average,
        "periodic_residual": orbit.periodic_residual,
        "root_residual": orbit.root_result.residual,
        "nfev": orbit.ode.nfev,
    }


class NonlinearCoupledObjective:
    def __init__(self, *, samples=48, rtol=1e-7, atol=1e-9):
        self.samples = samples
        self.rtol = rtol
        self.atol = atol
        self.cache: dict[tuple, float] = {}
        self.evaluations = 0
        self.cache_hits = 0

    def __call__(self, parameters):
        linear_damping, rotational_damping = map(float, np.asarray(parameters))
        if not (0.0 <= linear_damping <= 100000.0 and 0.0 <= rotational_damping <= 100000.0):
            return -1e30
        key = (
            round(linear_damping, 7),
            round(rotational_damping, 7),
            self.samples,
            self.rtol,
            self.atol,
            "nonlinear_mass_matrix_symmetric_lagrange",
        )
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        value = _periodic_coupled_power(
            linear_damping,
            rotational_damping,
            samples=self.samples,
            rtol=self.rtol,
            atol=self.atol,
        )["total_power_w"]
        self.cache[key] = value
        self.evaluations += 1
        return value


def run() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    wave = wave_case(4)
    started = perf_counter()

    objective = NonlinearCoupledObjective(samples=48, rtol=1e-7, atol=1e-9)
    damping_grid = np.linspace(0.0, 100000.0, 7)
    coarse_rows = []
    for linear_damping in damping_grid:
        for rotational_damping in damping_grid:
            total_value = objective([linear_damping, rotational_damping])
            coarse_rows.append(
                {
                    "linear_damping": linear_damping,
                    "rotational_damping": rotational_damping,
                    "total_power_w": total_value,
                }
            )
    coarse = pd.DataFrame(coarse_rows)
    coarse_best = coarse.loc[coarse["total_power_w"].idxmax()]

    global_result = optimize_global(
        objective,
        [(0.0, 100000.0), (0.0, 100000.0)],
        direction="maximize",
        seed=2022,
        popsize=5,
        maxiter=8,
        tol=2e-3,
        atol=2e-2,
        polish=False,
    )
    local_result = optimize_local(
        objective,
        global_result.x,
        bounds=[(0.0, 100000.0), (0.0, 100000.0)],
        method="Nelder-Mead",
        direction="maximize",
        options={"xatol": 0.1, "fatol": 2e-4, "maxiter": 140},
    )
    optimum = np.asarray(local_result.x, float)

    strict_local = optimize_local(
        lambda parameters: _periodic_coupled_power(*np.asarray(parameters, float), samples=128, rtol=2e-9, atol=2e-11)["total_power_w"],
        optimum,
        bounds=[(0.0, 100000.0), (0.0, 100000.0)],
        method="Nelder-Mead",
        direction="maximize",
        options={"xatol": 1e-2, "fatol": 2e-9, "maxiter": 120},
    )
    strict_optimum = np.asarray(strict_local.x, float)

    independent_heave, heave_stages = coarse_to_fine(
        lambda value: linear_heave_average_power(wave, value),
        (0.0, 100000.0),
        grid_points=101,
        direction="maximize",
        xatol=1e-8,
    )
    independent_pitch, pitch_stages = coarse_to_fine(
        lambda value: linear_pitch_average_power(wave, value),
        (0.0, 100000.0),
        grid_points=101,
        direction="maximize",
        xatol=1e-8,
    )
    linear_baseline_optimum = np.array([independent_heave.x, independent_pitch.x])
    strict_frequency_baseline = frequency_power(strict_optimum)

    shooting_levels = [
        _periodic_coupled_power(*strict_optimum, samples=samples, rtol=rtol, atol=atol)
        for samples, rtol, atol in ((64, 2e-7, 2e-9), (128, 2e-9, 2e-11), (256, 2e-11, 2e-13))
    ]
    strict_shooting = shooting_levels[-1]

    transient = simulate_periodic_steady(
        nonlinear_coupled_rhs(wave, *strict_optimum),
        wave.omega,
        np.zeros(8),
        total_cycles=240,
        samples_per_cycle=96,
        averaging_cycles=20,
        steady_tolerance=2e-4,
        rtol=2e-9,
        atol=2e-11,
        max_steps_per_cycle=40,
    )
    transient_power = nonlinear_coupled_power_summary(transient, *strict_optimum)

    neighborhood = []
    for delta in ((-10.0, 0.0), (10.0, 0.0), (0.0, -10.0), (0.0, 10.0), (-10.0, -10.0), (10.0, 10.0)):
        candidate = np.clip(strict_optimum + delta, 0.0, 100000.0)
        neighborhood.append(
            {
                "linear_damping": float(candidate[0]),
                "rotational_damping": float(candidate[1]),
                "total_power_w": _periodic_coupled_power(*candidate, samples=128, rtol=2e-9, atol=2e-11)["total_power_w"],
            }
        )
    boundary = []
    for linear_damping, rotational_damping in (
        (0.0, 0.0),
        (100000.0, 0.0),
        (0.0, 100000.0),
        (100000.0, 100000.0),
        (strict_optimum[0], 0.0),
        (0.0, strict_optimum[1]),
    ):
        boundary.append(
            {
                "linear_damping": float(linear_damping),
                "rotational_damping": float(rotational_damping),
                "total_power_w": _periodic_coupled_power(linear_damping, rotational_damping, samples=96, rtol=2e-8, atol=2e-10)["total_power_w"],
            }
        )

    write_excel_checked(
        RESULTS / "q4_optimization.xlsx",
        {
            "CoarseSurface": coarse,
            "Neighborhood": pd.DataFrame(neighborhood),
            "Boundary": pd.DataFrame(boundary),
        },
        decimals=10,
    )

    strict_heave = strict_shooting["heave_power_w"]
    strict_rotation = strict_shooting["rotation_power_w"]
    strict_total = strict_shooting["total_power_w"]
    window = transient_power["means"]
    total_window_values = [value for key, value in window.items() if key.startswith("total_")]
    metrics = {
        "status": "PASS",
        "runtime_seconds": perf_counter() - started,
        "optimal_linear_damping_n_s_m": float(strict_optimum[0]),
        "optimal_rotational_damping_n_m_s": float(strict_optimum[1]),
        "heave_power_w": strict_heave,
        "rotation_power_w": strict_rotation,
        "total_power_w": strict_total,
        "power_sum_residual_w": abs(strict_total - strict_heave - strict_rotation),
        "coarse_best": coarse_best.to_dict(),
        "global": {"x": np.asarray(global_result.x).tolist(), "power_w": global_result.objective, "success": global_result.success},
        "local": {"x": optimum.tolist(), "power_w": local_result.objective, "success": local_result.success},
        "linear_baseline": {
            "x": linear_baseline_optimum.tolist(),
            "power_w": frequency_power(linear_baseline_optimum),
            "heave_stages": heave_stages,
            "pitch_stages": pitch_stages,
        },
        "strict_local": {
            "x": strict_optimum.tolist(),
            "power_w": strict_local.objective,
            "success": strict_local.success,
        },
        "linear_frequency_power_at_nonlinear_optimum_w": strict_frequency_baseline,
        "nonlinear_coupling_gain_w": strict_total - strict_frequency_baseline,
        "shooting_levels": shooting_levels,
        "steady_start_cycle": transient.steady_start_cycle,
        "settling_time_s": transient.settling_time,
        "window_means": window,
        "neighborhood": neighborhood,
        "boundary": boundary,
        "objective_evaluations": objective.evaluations,
        "objective_cache_hits": objective.cache_hits,
    }
    passed = (
        global_result.success
        and local_result.success
        and strict_local.success
        and metrics["power_sum_residual_w"] < 1e-10
        and all(item["total_power_w"] <= strict_total + 2e-4 for item in neighborhood)
        and strict_shooting["periodic_residual"] < 1e-8
        and abs(window["total_20_cycles_simpson"] - strict_total) / strict_total < 8e-4
        and (max(total_window_values) - min(total_window_values)) / strict_total < 8e-4
    )
    metrics["status"] = "PASS" if passed else "FAIL"
    (RESULTS / "q4_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if not passed:
        raise RuntimeError("Q4 validation failed")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
