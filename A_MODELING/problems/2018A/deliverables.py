"""Generate and reread all 2018A Excel, Origin, figure, and summary artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from time import perf_counter

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.export import export_origin_table, verify_excel, write_excel_checked
from core.fitting import fit_metrics

from calibration import calibrate
from common import interface_diagnostics, load_official_data, make_system, safety_metrics, simulate
from validation_2018a import run_validation

OUTPUT = ROOT / "results" / "2018A"
FIGURES = OUTPUT / "figures"
ORIGIN = OUTPUT / "origin_data"


def _style():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans", "Arial"],
            "axes.unicode_minus": False,
            "font.size": 9,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.5,
        }
    )


def _save_figure(fig, name: str):
    fig.tight_layout()
    fig.savefig(FIGURES / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def _interface_time_series(system, field: np.ndarray, time_s: np.ndarray) -> pd.DataFrame:
    data: dict[str, np.ndarray] = {"time_s": time_s}
    grid = system.grid
    faces = np.flatnonzero(grid.layer_index[:-1] != grid.layer_index[1:])
    for face in faces:
        left_r = 0.5 * grid.widths_m[face] / grid.conductivity_w_mk[face]
        right_r = 0.5 * grid.widths_m[face + 1] / grid.conductivity_w_mk[face + 1]
        flux = (field[:, face] - field[:, face + 1]) / (left_r + right_r)
        name = f"T_interface_{grid.layer_names[grid.layer_index[face]]}_{grid.layer_names[grid.layer_index[face + 1]]}_C"
        data[name] = field[:, face] - flux * left_r
    return pd.DataFrame(data)


def _neighbor_table(environment, final_time, d_ii, d_iv, h_out, h_skin, *, vary="II") -> pd.DataFrame:
    rows = []
    for offset_mm in (-0.5, -0.2, -0.1, 0.0, 0.1, 0.2, 0.5):
        local_ii, local_iv = d_ii, d_iv
        if vary == "II":
            local_ii = float(np.clip(d_ii + offset_mm / 1000.0, 0.0006, 0.025))
        else:
            local_iv = float(np.clip(d_iv + offset_mm / 1000.0, 0.0006, 0.0064))
        system = make_system(environment, h_out, h_skin, d_ii_m=local_ii, d_iv_m=local_iv, target_dx_m=5e-5)
        result = simulate(system, final_time, dt_s=0.25, store_every=4)
        rows.append({"offset_mm": offset_mm, "d_ii_mm": local_ii * 1000.0, "d_iv_mm": local_iv * 1000.0, **safety_metrics(result)})
    frame = pd.DataFrame(rows)
    frame["first_crossing_44_s"] = frame["first_crossing_44_s"].fillna(-1.0)
    return frame


def _make_figures(q1_time, q1_profiles, validation, q2_time, q3_time):
    _style()
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.2), sharex=True)
    axes[0].plot(q1_time["time_s"] / 60, q1_time["measured_skin_C"], color="black", lw=1.0, label="Experiment")
    axes[0].plot(q1_time["time_s"] / 60, q1_time["predicted_skin_C"], color="#D55E00", label="Model")
    axes[0].set_ylabel("Skin-side temperature (°C)")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.25)
    axes[1].plot(q1_time["time_s"] / 60, q1_time["residual_C"], color="#0072B2")
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set(xlabel="Time (min)", ylabel="Experiment - model (°C)")
    axes[1].grid(alpha=0.25)
    _save_figure(fig, "experiment_fit_residual")

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for column in q1_profiles.columns[1:]:
        ax.plot(q1_profiles["x_mm"], q1_profiles[column], label=column.replace("T_", "").replace("_C", ""))
    ax.set(xlabel="Position from hot side (mm)", ylabel="Temperature (°C)")
    ax.legend(title="Time (s)", frameon=False, ncol=2)
    ax.grid(alpha=0.25)
    _save_figure(fig, "multilayer_temperature_profiles")

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    heat = ax.pcolormesh(q1_profiles.attrs["heat_x_mm"], q1_profiles.attrs["heat_time_min"], q1_profiles.attrs["heat_field"], shading="auto", cmap="inferno")
    fig.colorbar(heat, ax=ax, label="Temperature (°C)")
    ax.set(xlabel="Position from hot side (mm)", ylabel="Time (min)")
    _save_figure(fig, "temperature_xt_heatmap")

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0))
    for ax, data, title in zip(axes, (q2_time, q3_time), ("Q2 final design", "Q3 final design")):
        ax.plot(data["time_s"] / 60, data["skin_temperature_C"], color="#D55E00")
        ax.axhline(44, color="#0072B2", ls="--", label="44 °C")
        ax.axhline(47, color="black", ls=":", label="47 °C")
        ax.set(xlabel="Time (min)", ylabel="Skin-side temperature (°C)", title=title)
        ax.grid(alpha=0.25)
    axes[0].legend(frameon=False)
    _save_figure(fig, "final_design_safety")

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0))
    axes[0].plot(validation.q2_convergence["target_dx_m"] * 1000, validation.q2_convergence["critical_d_ii_mm"], "o-", label="Q2")
    axes[0].plot(validation.q3_convergence["target_dx_m"] * 1000, validation.q3_convergence["critical_d_ii_mm"], "s-", label="Q3")
    axes[0].invert_xaxis()
    axes[0].set(xlabel="Target dx (mm)", ylabel="Critical layer-II thickness (mm)", title="Spatial convergence")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.25)
    axes[1].plot(validation.q1_temporal_convergence["dt_s"], validation.q1_temporal_convergence["rmse_to_experiment_c"], "o-")
    axes[1].invert_xaxis()
    axes[1].set(xlabel="CN time step (s)", ylabel="Q1 RMSE (°C)", title="Temporal convergence")
    axes[1].grid(alpha=0.25)
    _save_figure(fig, "mesh_time_convergence")

    feasible_trade = validation.final_q3.coarse_scan.replace([np.inf, -np.inf], np.nan).dropna(subset=["total_mm"])
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(feasible_trade["d_iv_mm"], feasible_trade["total_mm"], "o-", color="#009E73")
    ax.scatter([validation.final_q3.d_iv_m * 1000], [validation.final_q3.total_thickness_m * 1000], color="#D55E00", zorder=3, label="Reported design")
    ax.set(xlabel="Layer-IV thickness (mm)", ylabel="Minimum total thickness (mm)")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    _save_figure(fig, "q3_thickness_tradeoff")

    sensitivity = validation.parameter_sensitivity.copy()
    sensitivity = sensitivity[sensitivity["relative_change"] != 0]
    labels = [f"{p}\n{r:+.0%}" for p, r in zip(sensitivity["parameter"], sensitivity["relative_change"])]
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True)
    axes[0].bar(labels, sensitivity["max_skin_temperature_c"], color="#56B4E9")
    axes[0].axhline(47, color="black", ls=":")
    axes[0].set_ylabel("Maximum skin temp. (°C)")
    axes[1].bar(labels, sensitivity["duration_above_44_s"], color="#E69F00")
    axes[1].axhline(300, color="black", ls=":")
    axes[1].set_ylabel("Time above 44 °C (s)")
    axes[1].tick_params(axis="x", rotation=30)
    _save_figure(fig, "parameter_sensitivity")


def generate_all() -> dict:
    started = perf_counter()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    ORIGIN.mkdir(parents=True, exist_ok=True)

    calibration = calibrate()
    validation = run_validation(calibration)
    _, measurements = load_official_data()
    observed = measurements.iloc[:, 1].to_numpy(float)

    q1_system = make_system(75.0, calibration.h_out_w_m2k, calibration.h_skin_w_m2k, target_dx_m=1e-4)
    q1_full = simulate(q1_system, 5400.0, dt_s=0.5, store_every=1)
    q1_indices = np.arange(0, len(q1_full.time_s), 2)
    q1_field = q1_full.temperature_c[q1_indices]
    q1_times = q1_full.time_s[q1_indices]
    q1_skin = q1_full.skin_temperature_c[q1_indices]
    q1_outer = q1_full.outer_surface_temperature_c[q1_indices]
    q1_metrics = fit_metrics(observed, q1_skin)
    q1_time = pd.DataFrame({"time_s": q1_times, "measured_skin_C": observed, "predicted_skin_C": q1_skin, "residual_C": observed - q1_skin, "outer_surface_C": q1_outer})
    interface_time = _interface_time_series(q1_system, q1_field, q1_times)

    field_columns = {"time_s": q1_times, "outer_surface_C": q1_outer}
    for index, x in enumerate(q1_system.grid.centers_m):
        field_columns[f"T_{index:04d}_x_{x:.7f}_m_C"] = q1_field[:, index]
    field_columns["skin_surface_C"] = q1_skin
    temperature_field = pd.DataFrame(field_columns)
    grid_frame = pd.DataFrame(
        {
            "cell_index": np.arange(len(q1_system.grid.centers_m)),
            "x_m": q1_system.grid.centers_m,
            "dx_m": q1_system.grid.widths_m,
            "layer": [q1_system.grid.layer_names[i] for i in q1_system.grid.layer_index],
            "rho_kg_m3": q1_system.grid.density_kg_m3,
            "cp_J_kgK": q1_system.grid.heat_capacity_j_kgk,
            "k_W_mK": q1_system.grid.conductivity_w_mk,
        }
    )
    parameters = pd.DataFrame(
        {
            "parameter": ["h_out", "h_skin", "target_dx", "dt", "environment_temperature", "body_temperature"],
            "value": [calibration.h_out_w_m2k, calibration.h_skin_w_m2k, 1e-4, 0.5, 75.0, 37.0],
            "unit": ["W/(m2 K)", "W/(m2 K)", "m", "s", "degC", "degC"],
        }
    )
    metrics_frame = pd.DataFrame(
        [{"RMSE_C": q1_metrics["rmse"], "MAE_C": q1_metrics["mae"], "R2": q1_metrics["r2"], "rows": len(q1_times), "nodes": len(q1_system.grid.centers_m)}]
    )
    problem1 = OUTPUT / "problem1.xlsx"
    write_excel_checked(
        problem1,
        {
            "SkinTemperature": q1_time,
            "TemperatureField": temperature_field,
            "InterfaceTime": interface_time,
            "Grid": grid_frame,
            "Parameters": parameters,
            "FitMetrics": metrics_frame,
            "InterfacesFinal": interface_diagnostics(q1_system, q1_field[-1]),
        },
        decimals=8,
    )

    q2 = validation.final_q2
    q3 = validation.final_q3
    q2_time = pd.DataFrame({"time_s": q2.simulation.time_s[::4], "skin_temperature_C": q2.simulation.skin_temperature_c[::4]})
    q3_time = pd.DataFrame({"time_s": q3.critical_result.simulation.time_s[::4], "skin_temperature_C": q3.critical_result.simulation.skin_temperature_c[::4]})
    q2_neighbor = _neighbor_table(65.0, 3600.0, q2.d_ii_m, 0.0055, calibration.h_out_w_m2k, calibration.h_skin_w_m2k)
    q3_neighbor = _neighbor_table(80.0, 1800.0, q3.d_ii_m, q3.d_iv_m, calibration.h_out_w_m2k, calibration.h_skin_w_m2k)
    q2_summary = pd.DataFrame([{"critical_d_ii_mm": q2.critical_d_ii_m * 1000, "reported_d_ii_mm": q2.d_ii_m * 1000, "d_iv_mm": 5.5, **q2.metrics}]).fillna(-1.0)
    q3_summary = pd.DataFrame([{"critical_d_ii_mm": q3.critical_result.critical_d_ii_m * 1000, "reported_d_ii_mm": q3.d_ii_m * 1000, "reported_d_iv_mm": q3.d_iv_m * 1000, "total_mm": q3.total_thickness_m * 1000, **q3.critical_result.metrics}]).fillna(-1.0)
    write_excel_checked(OUTPUT / "q2_results.xlsx", {"Summary": q2_summary, "TimeSeries": q2_time, "CoarseScan": q2.coarse_scan, "Neighborhood": q2_neighbor, "Convergence": validation.q2_convergence}, decimals=8)
    q3_coarse_display = q3.coarse_scan.copy()
    q3_coarse_display["critical_d_ii_mm"] = q3_coarse_display["critical_d_ii_mm"].map(lambda value: "INFEASIBLE" if pd.isna(value) else value)
    q3_coarse_display["total_mm"] = q3_coarse_display["total_mm"].map(lambda value: "INFEASIBLE" if not np.isfinite(value) else value)
    write_excel_checked(OUTPUT / "q3_results.xlsx", {"Summary": q3_summary, "TimeSeries": q3_time, "CoarseScan": q3_coarse_display, "NeighborhoodII": q3_neighbor, "Convergence": validation.q3_convergence}, decimals=8)
    write_excel_checked(
        OUTPUT / "validation.xlsx",
        {
            "Analytic": validation.analytic_benchmark,
            "ExplicitCN": validation.explicit_cn,
            "Interface": validation.interface,
            "Q1Spatial": validation.q1_spatial_convergence,
            "Q1Temporal": validation.q1_temporal_convergence,
            "Q2Convergence": validation.q2_convergence,
            "Q3Convergence": validation.q3_convergence,
            "Sensitivity": validation.parameter_sensitivity.drop(columns=["first_crossing_44_s"]).copy(),
            "Performance": validation.performance,
            "Multistart": calibration.multistart,
        },
        decimals=10,
    )

    profile_times = (0, 900, 1800, 3600, 5400)
    profile_indices = [int(time) for time in profile_times]
    profiles = pd.DataFrame({"x_mm": q1_system.grid.centers_m * 1000})
    for time, index in zip(profile_times, profile_indices):
        profiles[f"T_{time}_s_C"] = q1_field[index]
    heat_indices = np.arange(0, len(q1_times), 10)
    profiles.attrs["heat_x_mm"] = q1_system.grid.centers_m * 1000
    profiles.attrs["heat_time_min"] = q1_times[heat_indices] / 60
    profiles.attrs["heat_field"] = q1_field[heat_indices]

    export_origin_table(ORIGIN / "temperature_time.xlsx", pd.concat([q1_time.drop(columns=["measured_skin_C", "predicted_skin_C", "residual_C"]), interface_time.drop(columns=["time_s"])], axis=1), x_column="time_s", metadata={"purpose": "Q1 boundary and interface temperature histories", "time_unit": "s", "temperature_unit": "degC"})
    export_origin_table(ORIGIN / "experiment_fit.xlsx", q1_time[["time_s", "measured_skin_C", "predicted_skin_C", "residual_C"]], x_column="time_s", metadata={"purpose": "experiment-model fit and residual"})
    export_origin_table(ORIGIN / "thickness_comparison.xlsx", q2.coarse_scan, x_column="d_ii_mm", metadata={"purpose": "Q2 coarse bracket and safety constraints"})
    mesh_origin = validation.q2_convergence[["level", "target_dx_m", "critical_d_ii_mm"]].rename(columns={"critical_d_ii_mm": "q2_critical_d_ii_mm"}).merge(validation.q3_convergence[["level", "critical_d_ii_mm"]].rename(columns={"critical_d_ii_mm": "q3_critical_d_ii_mm"}), on="level")
    export_origin_table(ORIGIN / "mesh_convergence.xlsx", mesh_origin, x_column="target_dx_m", metadata={"purpose": "Q2/Q3 spatial convergence"})
    sensitivity_origin = validation.parameter_sensitivity.drop(columns=["first_crossing_44_s"]).copy()
    export_origin_table(ORIGIN / "parameter_sensitivity.xlsx", sensitivity_origin, x_column="relative_change", metadata={"purpose": "Q2 fixed-design sensitivity"})
    export_origin_table(ORIGIN / "temperature_profile.xlsx", profiles, x_column="x_mm", metadata={"purpose": "Q1 selected multilayer profiles"})
    q3_trade = q3.coarse_scan.replace([np.inf, -np.inf], np.nan).dropna(subset=["total_mm"])
    export_origin_table(ORIGIN / "q3_tradeoff.xlsx", q3_trade, x_column="d_iv_mm", metadata={"purpose": "Q3 minimum total thickness versus layer IV"})

    _make_figures(q1_time, profiles, validation, q2_time, q3_time)

    excel_files = [problem1, OUTPUT / "q2_results.xlsx", OUTPUT / "q3_results.xlsx", OUTPUT / "validation.xlsx", *sorted(ORIGIN.glob("*.xlsx"))]
    excel_checks = {path.name: verify_excel(path) for path in excel_files}
    extra_checks = {
        "problem1_time_strict": bool(np.all(np.diff(pd.read_excel(problem1, sheet_name="SkinTemperature")["time_s"]) > 0)),
        "problem1_rows": int(len(pd.read_excel(problem1, sheet_name="SkinTemperature"))),
        "problem1_field_shape": list(pd.read_excel(problem1, sheet_name="TemperatureField").shape),
        "all_workbooks_valid": bool(all(item["valid"] for item in excel_checks.values())),
    }
    with (OUTPUT / "excel_validation.json").open("w", encoding="utf-8") as handle:
        json.dump({"workbooks": excel_checks, "extra": extra_checks}, handle, ensure_ascii=False, indent=2)
    summary = {
        "calibration": {"h_out_w_m2k": calibration.h_out_w_m2k, "h_skin_w_m2k": calibration.h_skin_w_m2k, "rmse_c": calibration.rmse_c, "mae_c": calibration.mae_c, "r2": calibration.r2, "condition_number": calibration.jacobian_condition_number, "parameter_correlation": calibration.parameter_correlation},
        "q2": q2_summary.iloc[0].to_dict(),
        "q3": q3_summary.iloc[0].to_dict(),
        "validation_elapsed_seconds": validation.elapsed_seconds,
        "deliverables_elapsed_seconds": perf_counter() - started,
        "excel": extra_checks,
    }
    with (OUTPUT / "results_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, default=float)
    return summary


if __name__ == "__main__":
    print(json.dumps(generate_all(), ensure_ascii=False, indent=2, default=float))
