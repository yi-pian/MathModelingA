"""Question 1: 40-period heave responses and official workbook export."""

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
from core.ode import solve_ode, tolerance_convergence
from core.validation import check_finite, check_monotonic_time
from deliverables import RESULTS, write_official_result
from physics import harmonic_state, heave_frequency_response, heave_rhs
from problem_data import wave_case
from steady_state import cycle_change_metrics


SELECTED_TIMES = np.array([10.0, 20.0, 40.0, 60.0, 100.0])


def official_times(omega: float, cycles: int = 40, interval: float = 0.2) -> np.ndarray:
    stop = cycles * 2.0 * np.pi / omega
    count = int(np.floor(stop / interval + 1e-12))
    return np.arange(count + 1, dtype=float) * interval


def solve_case(damping_scale: float, exponent: float, *, rtol=2e-10, atol=2e-12):
    wave = wave_case(1)
    times = official_times(wave.omega)
    result = solve_ode(
        heave_rhs(wave, damping_scale, exponent),
        (0.0, 40.0 * wave.period),
        np.zeros(4),
        sample_times=times,
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=wave.period / 32.0,
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result


def selected_table(result) -> pd.DataFrame:
    indices = [int(np.flatnonzero(np.isclose(result.time, time, atol=1e-12))[0]) for time in SELECTED_TIMES]
    values = result.state[:, indices].T
    return pd.DataFrame(
        np.column_stack([SELECTED_TIMES, values]),
        columns=["time_s", "float_displacement_m", "oscillator_displacement_m", "float_velocity_m_s", "oscillator_velocity_m_s"],
    )


def _official_matrix(result) -> np.ndarray:
    return np.column_stack([result.time, result.state[0], result.state[2], result.state[1], result.state[3]])


def run() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    wave = wave_case(1)
    started = perf_counter()
    linear = solve_case(10000.0, 0.0)
    nonlinear = solve_case(10000.0, 0.5)
    runtime = perf_counter() - started

    convergence_times = np.linspace(0.0, 40.0 * wave.period, 2401)
    convergence = {}
    for name, scale, exponent in (("linear", 10000.0, 0.0), ("nonlinear", 10000.0, 0.5)):
        study = tolerance_convergence(
            heave_rhs(wave, scale, exponent),
            (0.0, 40.0 * wave.period),
            np.zeros(4),
            convergence_times,
            tolerances=(1e-7, 1e-9, 1e-11),
            method="DOP853",
            atol_ratio=0.01,
        )
        convergence[name] = {
            "tolerances": study["tolerances"],
            "max_differences": study["max_differences"],
            "acceptance_threshold": study["acceptance_threshold"],
            "convergent": study["convergent"],
            "delivery_accuracy_pass": bool(
                study["max_differences"][-1] < 2e-7
                and study["max_differences"][-1] < study["max_differences"][0]
            ),
            "nfev": [solution.nfev for solution in study["solutions"]],
        }

    response = heave_frequency_response(wave, 10000.0)
    last_cycle_time = np.linspace(39.0 * wave.period, 40.0 * wave.period, 257)
    transient_last = solve_ode(
        heave_rhs(wave, 10000.0),
        (0.0, 40.0 * wave.period),
        np.zeros(4),
        sample_times=last_cycle_time,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        max_step=wave.period / 40.0,
    )
    harmonic = harmonic_state(last_cycle_time, wave.omega, response)
    frequency_error = float(np.max(np.abs(transient_last.state - harmonic)))
    frequency_scale = float(np.max(np.abs(harmonic)))

    long_time = np.linspace(119.0 * wave.period, 120.0 * wave.period, 257)
    long_transient = solve_ode(
        heave_rhs(wave, 10000.0),
        (0.0, 120.0 * wave.period),
        np.zeros(4),
        sample_times=long_time,
        method="DOP853",
        rtol=1e-10,
        atol=1e-12,
        max_step=wave.period / 40.0,
    )
    long_harmonic = harmonic_state(long_time, wave.omega, response)
    long_frequency_error = float(np.max(np.abs(long_transient.state - long_harmonic)))

    phase_times = np.linspace(0.0, 40.0 * wave.period, 40 * 64 + 1)
    phase_solution = solve_ode(
        heave_rhs(wave, 10000.0),
        (0.0, phase_times[-1]),
        np.zeros(4),
        sample_times=phase_times,
        method="DOP853",
        rtol=1e-9,
        atol=1e-11,
        max_step=wave.period / 32.0,
    )
    cycle_metrics = cycle_change_metrics(phase_solution.state, 40, 64)

    excel_linear = write_official_result("result1-1.xlsx", _official_matrix(linear), expected_columns=5)
    excel_nonlinear = write_official_result("result1-2.xlsx", _official_matrix(nonlinear), expected_columns=5)
    selected = pd.concat(
        [selected_table(linear).assign(case="linear"), selected_table(nonlinear).assign(case="velocity_power")],
        ignore_index=True,
    )
    write_excel_checked(RESULTS / "q1_selected_results.xlsx", {"Selected": selected}, decimals=9)

    metrics = {
        "status": "PASS",
        "runtime_seconds": runtime,
        "official_rows": len(linear.time),
        "official_time_end_s": float(linear.time[-1]),
        "period_s": wave.period,
        "linear_nfev": linear.nfev,
        "nonlinear_nfev": nonlinear.nfev,
        "convergence": convergence,
        "frequency_domain_max_abs_error": frequency_error,
        "frequency_domain_relative_error": frequency_error / max(frequency_scale, 1e-15),
        "frequency_domain_120_cycle_max_abs_error": long_frequency_error,
        "frequency_domain_120_cycle_relative_error": long_frequency_error / max(frequency_scale, 1e-15),
        "last_cycle_change_metric": float(cycle_metrics[-1]),
        "excel": {"result1-1.xlsx": excel_linear, "result1-2.xlsx": excel_nonlinear},
        "finite": bool(check_finite(linear.state) and check_finite(nonlinear.state)),
        "monotonic_time": bool(check_monotonic_time(linear.time) and check_monotonic_time(nonlinear.time)),
        "selected": selected.to_dict(orient="records"),
    }
    passed = (
        metrics["finite"]
        and metrics["monotonic_time"]
        and all(value["delivery_accuracy_pass"] for value in convergence.values())
        and excel_linear["valid"]
        and excel_nonlinear["valid"]
        and metrics["frequency_domain_120_cycle_relative_error"] < 2e-5
    )
    metrics["status"] = "PASS" if passed else "FAIL"
    (RESULTS / "q1_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if not passed:
        raise RuntimeError("Q1 validation failed")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
