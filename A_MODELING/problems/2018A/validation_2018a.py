"""Convergence, cross-method, sensitivity, and performance validation for 2018 A."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.fitting import fit_metrics
from core.performance import benchmark

from calibration import CalibrationResult, predict_skin_temperature
from common import (
    assemble_heat_system,
    build_grid,
    explicit_stable_dt,
    interface_diagnostics,
    load_official_data,
    make_system,
    official_layers,
    safety_metrics,
    simulate,
    simulate_explicit,
    single_layer_sine_benchmark,
)
from q2 import CriticalThicknessResult, solve_q2
from q3 import Q3Result, solve_q3


@dataclass(frozen=True)
class Validation2018A:
    analytic_benchmark: pd.DataFrame
    explicit_cn: pd.DataFrame
    interface: pd.DataFrame
    q1_spatial_convergence: pd.DataFrame
    q1_temporal_convergence: pd.DataFrame
    q2_convergence: pd.DataFrame
    q3_convergence: pd.DataFrame
    parameter_sensitivity: pd.DataFrame
    performance: pd.DataFrame
    final_q2: CriticalThicknessResult
    final_q3: Q3Result
    elapsed_seconds: float


def _q1_row(h_out: float, h_skin: float, dx: float, dt: float) -> dict:
    _, measurements = load_official_data()
    observed = measurements.iloc[:, 1].to_numpy(float)
    system = make_system(75.0, h_out, h_skin, target_dx_m=dx)
    store_every = int(round(1.0 / dt))
    result = simulate(system, 5400.0, dt_s=dt, store_every=store_every)
    metrics = fit_metrics(observed, result.skin_temperature_c)
    return {
        "target_dx_m": dx,
        "dt_s": result.dt_s,
        "nodes": len(system.grid.centers_m),
        "final_skin_temperature_c": result.skin_temperature_c[-1],
        "max_skin_temperature_c": result.skin_temperature_c.max(),
        "rmse_to_experiment_c": metrics["rmse"],
    }


def _design_row(label: str, dx: float, dt: float, result: CriticalThicknessResult) -> dict:
    return {
        "level": label,
        "target_dx_m": dx,
        "dt_s": dt,
        "critical_d_ii_mm": result.critical_d_ii_m * 1000.0,
        "reported_d_ii_mm": result.d_ii_m * 1000.0,
        "max_skin_temperature_c": result.metrics["max_skin_temperature_c"],
        "duration_above_44_s": result.metrics["duration_above_44_s"],
        "margin_47_c": result.metrics["margin_47_c"],
        "margin_duration_s": result.metrics["margin_duration_s"],
        "elapsed_seconds": result.elapsed_seconds,
    }


def _sensitivity(h_out: float, h_skin: float, q2: CriticalThicknessResult) -> pd.DataFrame:
    baseline_d = q2.d_ii_m
    rows = []
    for parameter, changes in {
        "h_out": (-0.05, 0.0, 0.05),
        "h_skin": (-0.05, 0.0, 0.05),
        "environment_temperature": (-0.05, 0.0, 0.05),
        "k_IV": (-0.05, 0.0, 0.05),
    }.items():
        for relative in changes:
            env, local_h_out, local_h_skin = 65.0, h_out, h_skin
            layers = list(official_layers(baseline_d, 0.0055))
            if parameter == "h_out":
                local_h_out *= 1.0 + relative
            elif parameter == "h_skin":
                local_h_skin *= 1.0 + relative
            elif parameter == "environment_temperature":
                env = 37.0 + (65.0 - 37.0) * (1.0 + relative)
            elif parameter == "k_IV":
                layers[-1] = replace(layers[-1], conductivity_w_mk=layers[-1].conductivity_w_mk * (1.0 + relative))
            system = assemble_heat_system(build_grid(tuple(layers), 5e-5), env, local_h_out, local_h_skin)
            metrics = safety_metrics(simulate(system, 3600.0, dt_s=0.25, store_every=4))
            rows.append({"parameter": parameter, "relative_change": relative, **metrics})
    return pd.DataFrame(rows)


def run_validation(calibration: CalibrationResult) -> Validation2018A:
    started = perf_counter()
    h_out, h_skin = calibration.h_out_w_m2k, calibration.h_skin_w_m2k

    analytic_rows = []
    for nx in (51, 101, 201):
        dx = 0.01 / (nx - 1)
        value = single_layer_sine_benchmark(final_time_s=0.02, nx=nx, dt_s=0.1 * dx**2 / 1e-5, method="cn")
        analytic_rows.append({"method": "CN", "nx": nx, "dx_m": value["dx_m"], "dt_s": value["dt_s"], "max_error": value["max_error"]})
    explicit_value = single_layer_sine_benchmark(final_time_s=0.02, nx=101, dt_s=0.4 * (0.01 / 100) ** 2 / 1e-5, method="explicit")
    analytic_rows.append({"method": "explicit", "nx": 101, "dx_m": explicit_value["dx_m"], "dt_s": explicit_value["dt_s"], "max_error": explicit_value["max_error"]})
    analytic = pd.DataFrame(analytic_rows)

    cross_system = make_system(75.0, h_out, h_skin, target_dx_m=5e-4)
    explicit_dt = explicit_stable_dt(cross_system, safety=0.8)
    explicit_result = simulate_explicit(cross_system, 10.0, explicit_dt)
    cn_result = simulate(cross_system, 10.0, explicit_dt)
    difference = explicit_result.temperature_c[-1] - cn_result.temperature_c[-1]
    explicit_cn = pd.DataFrame(
        [{
            "target_dx_m": 5e-4,
            "explicit_dt_limit_s": explicit_stable_dt(cross_system),
            "used_dt_s": explicit_result.dt_s,
            "field_rmse_c": float(np.sqrt(np.mean(difference**2))),
            "field_max_abs_error_c": float(np.max(np.abs(difference))),
            "skin_abs_error_c": float(abs(explicit_result.skin_temperature_c[-1] - cn_result.skin_temperature_c[-1])),
        }]
    )

    interface_system = make_system(75.0, h_out, h_skin, target_dx_m=5e-5)
    interface_result = simulate(interface_system, 5400.0, dt_s=0.25, store_every=4)
    interface = interface_diagnostics(interface_system, interface_result.temperature_c[-1])

    spatial = pd.DataFrame([_q1_row(h_out, h_skin, dx, 0.25) for dx in (2e-4, 1e-4, 5e-5)])
    temporal = pd.DataFrame([_q1_row(h_out, h_skin, 5e-5, dt) for dt in (1.0, 0.5, 0.25)])

    levels = (("coarse", 2e-4, 1.0), ("medium", 1e-4, 0.5), ("fine", 5e-5, 0.25))
    q2_results = [solve_q2(h_out, h_skin, target_dx_m=dx, dt_s=dt) for _, dx, dt in levels]
    q2_table = pd.DataFrame([_design_row(label, dx, dt, result) for (label, dx, dt), result in zip(levels, q2_results)])
    q3_results = [solve_q3(h_out, h_skin, target_dx_m=dx, dt_s=dt, coarse_points=11) for _, dx, dt in levels]
    q3_table = pd.DataFrame(
        [
            {
                **_design_row(label, dx, dt, result.critical_result),
                "d_iv_mm": result.d_iv_m * 1000.0,
                "total_mm": result.total_thickness_m * 1000.0,
                "q3_elapsed_seconds": result.elapsed_seconds,
            }
            for (label, dx, dt), result in zip(levels, q3_results)
        ]
    )
    sensitivity = _sensitivity(h_out, h_skin, q2_results[-1])

    cn_benchmark = benchmark(lambda: simulate(make_system(65.0, h_out, h_skin, d_ii_m=q2_results[-1].d_ii_m, d_iv_m=0.0055, target_dx_m=1e-4), 3600.0, dt_s=1.0), repeats=3, warmup=1)
    explicit_benchmark = benchmark(lambda: simulate_explicit(cross_system, 10.0, explicit_dt), repeats=3, warmup=1)
    fit_call = benchmark(lambda: predict_skin_temperature((h_out, h_skin), target_dx_m=1e-4, dt_s=1.0), repeats=3, warmup=1)
    performance = pd.DataFrame(
        [
            {"stage": "single_CN_3600s", **cn_benchmark},
            {"stage": "single_explicit_10s", **explicit_benchmark},
            {"stage": "single_fit_objective", **fit_call},
            {"stage": "calibration_total", "runs": 1, "min_seconds": calibration.elapsed_seconds, "mean_seconds": calibration.elapsed_seconds, "median_seconds": calibration.elapsed_seconds, "all_seconds": [calibration.elapsed_seconds]},
            {"stage": "Q2_FINAL_search", "runs": 1, "min_seconds": q2_results[-1].elapsed_seconds, "mean_seconds": q2_results[-1].elapsed_seconds, "median_seconds": q2_results[-1].elapsed_seconds, "all_seconds": [q2_results[-1].elapsed_seconds]},
            {"stage": "Q3_FINAL_search", "runs": 1, "min_seconds": q3_results[-1].elapsed_seconds, "mean_seconds": q3_results[-1].elapsed_seconds, "median_seconds": q3_results[-1].elapsed_seconds, "all_seconds": [q3_results[-1].elapsed_seconds]},
        ]
    )
    performance["all_seconds"] = performance["all_seconds"].map(str)
    return Validation2018A(
        analytic,
        explicit_cn,
        interface,
        spatial,
        temporal,
        q2_table,
        q3_table,
        sensitivity,
        performance,
        q2_results[-1],
        q3_results[-1],
        perf_counter() - started,
    )
