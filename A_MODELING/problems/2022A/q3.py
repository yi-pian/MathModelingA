"""Question 3: unified heave-pitch transient response and result3.xlsx."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.export import write_excel_checked
from core.ode import solve_ode, tolerance_convergence
from deliverables import RESULTS, write_official_result
from physics import (
    coupled_rhs,
    harmonic_state,
    heave_frequency_response,
    heave_rhs,
    nonlinear_coupled_rhs,
    nonlinear_observables,
    pitch_frequency_response,
    pitch_rhs,
)
from problem_data import PHYSICAL, wave_case
from steady_state import solve_periodic_orbit


SELECTED_TIMES = np.array([10.0, 20.0, 40.0, 60.0, 100.0])


def official_times(omega: float, cycles: int = 40, interval: float = 0.2) -> np.ndarray:
    stop = cycles * 2.0 * np.pi / omega
    return np.arange(int(np.floor(stop / interval + 1e-12)) + 1, dtype=float) * interval


def solve_formal(*, rtol=2e-10, atol=2e-12):
    wave = wave_case(3)
    times = official_times(wave.omega)
    result = solve_ode(
        nonlinear_coupled_rhs(wave, 10000.0, 1000.0),
        (0.0, 40.0 * wave.period),
        np.zeros(8),
        sample_times=times,
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=wave.period / 40.0,
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result


def _official_matrix(result) -> np.ndarray:
    observed = nonlinear_observables(result.state)
    return np.column_stack(
        [
            result.time,
            observed[0],
            observed[4],
            observed[2],
            observed[6],
            observed[1],
            observed[5],
            observed[3],
            observed[7],
        ]
    )


def _selected_table(result) -> pd.DataFrame:
    indices = [int(np.flatnonzero(np.isclose(result.time, time, atol=1e-12))[0]) for time in SELECTED_TIMES]
    data = _official_matrix(result)[indices]
    return pd.DataFrame(
        data,
        columns=[
            "time_s",
            "float_heave_m",
            "float_heave_velocity_m_s",
            "float_pitch_rad",
            "float_pitch_rate_rad_s",
            "oscillator_heave_m",
            "oscillator_heave_velocity_m_s",
            "oscillator_pitch_rad",
            "oscillator_pitch_rate_rad_s",
        ],
    )


def run() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    wave = wave_case(3)
    started = perf_counter()
    formal = solve_formal()
    runtime = perf_counter() - started

    convergence_times = np.linspace(0.0, 40.0 * wave.period, 2401)
    convergence = tolerance_convergence(
        nonlinear_coupled_rhs(wave, 10000.0, 1000.0),
        (0.0, 40.0 * wave.period),
        np.zeros(8),
        convergence_times,
        tolerances=(1e-7, 1e-9, 1e-11),
        method="DOP853",
        atol_ratio=0.01,
    )
    delivery_convergence = bool(
        convergence["max_differences"][-1] < 3e-7
        and convergence["max_differences"][-1] < convergence["max_differences"][0]
    )

    # Exact degeneration: with pitch excitation removed, the nonlinear generalized
    # coordinates must reproduce the Q1-style two-body heave model.
    no_pitch_wave = replace(wave, excitation_moment=0.0)
    no_pitch = solve_ode(
        nonlinear_coupled_rhs(no_pitch_wave, 10000.0, 1000.0),
        (0.0, formal.time[-1]),
        np.zeros(8),
        sample_times=formal.time,
        method="DOP853",
        rtol=2e-10,
        atol=2e-12,
        max_step=wave.period / 40.0,
    )
    heave = solve_ode(
        heave_rhs(no_pitch_wave, 10000.0),
        (0.0, formal.time[-1]),
        np.zeros(4),
        sample_times=formal.time,
        method="DOP853",
        rtol=2e-10,
        atol=2e-12,
        max_step=wave.period / 40.0,
    )
    no_pitch_observed = nonlinear_observables(no_pitch.state)
    degeneration_error = float(np.max(np.abs(no_pitch_observed[[0, 1, 4, 5]] - heave.state)))

    # Independent linear small-signal baseline: nonlinear-minus-linear error must
    # decrease with forcing amplitude, rather than forcing the formal nonlinear run
    # to equal its first-order approximation.
    small_scale = 1e-3
    small_wave = replace(wave, excitation_force=wave.excitation_force * small_scale, excitation_moment=wave.excitation_moment * small_scale)
    small_time = np.linspace(0.0, 20.0 * wave.period, 1201)
    nonlinear_small = solve_ode(
        nonlinear_coupled_rhs(small_wave, 10000.0, 1000.0),
        (0.0, small_time[-1]),
        np.zeros(8),
        sample_times=small_time,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        max_step=wave.period / 48.0,
    )
    linear_small = solve_ode(
        coupled_rhs(small_wave, 10000.0, 1000.0),
        (0.0, small_time[-1]),
        np.zeros(8),
        sample_times=small_time,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        max_step=wave.period / 48.0,
    )
    nonlinear_small_observed = nonlinear_observables(nonlinear_small.state)
    small_signal_error = float(np.max(np.abs(nonlinear_small_observed - linear_small.state)))
    small_signal_relative = small_signal_error / max(float(np.max(np.abs(linear_small.state))), 1e-15)

    # The long-run transient must converge to the independently solved nonlinear
    # periodic shooting orbit.
    validation_cycles = 240
    long_time = np.linspace((validation_cycles - 1.0) * wave.period, validation_cycles * wave.period, 257)
    long_solution = solve_ode(
        nonlinear_coupled_rhs(wave, 10000.0, 1000.0),
        (0.0, validation_cycles * wave.period),
        np.zeros(8),
        sample_times=long_time,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        max_step=wave.period / 48.0,
    )
    harmonic_heave = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, 10000.0))[:, 0]
    harmonic_pitch = harmonic_state([0.0], wave.omega, pitch_frequency_response(wave, 1000.0))[:, 0]
    shooting_guess = np.array(
        [
            harmonic_heave[1] - harmonic_heave[0],
            harmonic_heave[0],
            harmonic_pitch[0],
            harmonic_pitch[1],
            harmonic_heave[3] - harmonic_heave[2],
            harmonic_heave[2],
            harmonic_pitch[2],
            harmonic_pitch[3],
        ]
    )
    orbit = solve_periodic_orbit(
        nonlinear_coupled_rhs(wave, 10000.0, 1000.0),
        wave.omega,
        shooting_guess,
        samples_per_cycle=256,
        rtol=2e-10,
        atol=2e-12,
        root_tolerance=1e-8,
    )
    periodic_error = float(np.max(np.abs(long_solution.state - orbit.ode.state)))
    periodic_relative = periodic_error / max(float(np.max(np.abs(orbit.ode.state))), 1e-15)

    selected = _selected_table(formal)
    write_excel_checked(RESULTS / "q3_selected_results.xlsx", {"Selected": selected}, decimals=10)
    excel = write_official_result("result3.xlsx", _official_matrix(formal), expected_columns=9)
    inertia = PHYSICAL.audit_dict()
    inertia["float_components"] = PHYSICAL.float_pitch_inertia_components()
    metrics = {
        "status": "PASS",
        "runtime_seconds": runtime,
        "official_rows": len(formal.time),
        "official_time_end_s": float(formal.time[-1]),
        "period_s": wave.period,
        "nfev": formal.nfev,
        "state_order": ["x_rel", "z_f", "theta_f", "theta_o", "x_dot_rel", "v_f", "omega_f", "omega_o"],
        "official_observable_order": ["z_f", "z_o", "theta_f", "theta_o", "v_f", "v_o", "omega_f", "omega_o"],
        "angle_unit": "rad",
        "convergence": {
            "tolerances": convergence["tolerances"],
            "max_differences": convergence["max_differences"],
            "core_convergent": convergence["convergent"],
            "delivery_accuracy_pass": delivery_convergence,
            "nfev": [solution.nfev for solution in convergence["solutions"]],
        },
        "heave_degeneration_max_abs_error": degeneration_error,
        "small_signal_scale": small_scale,
        "small_signal_linearization_max_abs_error": small_signal_error,
        "small_signal_linearization_relative_error": small_signal_relative,
        "periodic_validation_cycles": validation_cycles,
        "periodic_shooting_residual": orbit.periodic_residual,
        "periodic_long_transient_max_abs_error": periodic_error,
        "periodic_long_transient_relative_error": periodic_relative,
        "inertia_audit": inertia,
        "excel": excel,
        "selected": selected.to_dict(orient="records"),
    }
    passed = (
        delivery_convergence
        and degeneration_error < 2e-8
        and small_signal_relative < 5e-3
        and orbit.periodic_residual < 1e-7
        and periodic_relative < 2e-5
        and excel["valid"]
        and np.all(np.isfinite(formal.state))
        and np.max(np.abs(nonlinear_observables(formal.state)[2:4])) < 0.5
    )
    metrics["status"] = "PASS" if passed else "FAIL"
    (RESULTS / "q3_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if not passed:
        raise RuntimeError("Q3 validation failed")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
