"""Publication figures and one-purpose Origin tables from final 2022A results."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt

from core.export import export_origin_table
from core.plotting import COLORS, save_figure, use_paper_style
from physics import harmonic_state, heave_frequency_response, heave_rhs
from power import heave_power
from problem_data import wave_case
from q1 import solve_case
from q3 import _official_matrix as q3_official_matrix
from q3 import solve_formal
from steady_state import solve_periodic_orbit


RESULTS = ROOT / "results" / "2022A"
FIGURES = RESULTS / "figures"
ORIGIN = RESULTS / "origin_data"


def _finish(figure, name):
    figure.tight_layout()
    paths = save_figure(figure, FIGURES / name)
    plt.close(figure)
    return [str(path) for path in paths]


def _response_figure(result, name, title):
    use_paper_style()
    figure, axes = plt.subplots(2, 1, figsize=(6.4, 5.4), sharex=True)
    axes[0].plot(result.time, result.state[0], label="Float", color=COLORS[0])
    axes[0].plot(result.time, result.state[1], label="Oscillator", color=COLORS[1])
    axes[0].set(ylabel="Displacement (m)", title=title)
    axes[1].plot(result.time, result.state[2], label="Float", color=COLORS[0])
    axes[1].plot(result.time, result.state[3], label="Oscillator", color=COLORS[1])
    axes[1].set(xlabel="Time (s)", ylabel="Velocity (m/s)")
    for axis in axes:
        axis.grid(True, color="#D9D9D9", linewidth=0.5)
        axis.legend(ncol=2)
    return _finish(figure, name)


def run() -> dict:
    FIGURES.mkdir(parents=True, exist_ok=True)
    ORIGIN.mkdir(parents=True, exist_ok=True)
    written = {}

    linear = solve_case(10000.0, 0.0)
    nonlinear = solve_case(10000.0, 0.5)
    written["q1_linear_response"] = _response_figure(linear, "q1_linear_response", "Q1 constant-damping transient response")
    written["q1_nonlinear_response"] = _response_figure(nonlinear, "q1_nonlinear_response", "Q1 velocity-power-damping transient response")
    for name, result in (("q1_linear_response", linear), ("q1_nonlinear_response", nonlinear)):
        export_origin_table(
            ORIGIN / f"{name}.xlsx",
            pd.DataFrame(
                {
                    "time_s": result.time,
                    "float_displacement_m": result.state[0],
                    "oscillator_displacement_m": result.state[1],
                    "float_velocity_m_s": result.state[2],
                    "oscillator_velocity_m_s": result.state[3],
                }
            ),
            x_column="time_s",
            metadata={"purpose": "Q1 transient displacement and velocity", "units": "SI"},
        )

    q2 = pd.read_excel(RESULTS / "q2_optimization.xlsx", sheet_name=None)
    constant = q2["ConstantScan"]
    use_paper_style()
    figure, axis = plt.subplots(figsize=(5.4, 3.5))
    axis.plot(constant["damping"], constant["average_power_w"], color=COLORS[0])
    best = constant.loc[constant["average_power_w"].idxmax()]
    axis.scatter([best["damping"]], [best["average_power_w"]], color=COLORS[1], zorder=3, label="Coarse maximum")
    axis.set(xlabel="Linear damping (N·s/m)", ylabel="Average power (W)", title="Q2 constant-damping power curve")
    axis.grid(True, color="#D9D9D9", linewidth=0.5); axis.legend()
    written["q2_constant_power"] = _finish(figure, "q2_constant_power")
    export_origin_table(ORIGIN / "q2_constant_power.xlsx", constant, x_column="damping", metadata={"purpose": "Q2 constant-damping optimum"})

    coarse = q2["NonlinearCoarse"]
    scale_values = np.sort(coarse["scale"].unique())
    exponent_values = np.sort(coarse["exponent"].unique())
    surface = coarse.pivot(index="exponent", columns="scale", values="average_power_w").loc[exponent_values, scale_values].to_numpy()
    use_paper_style()
    figure, axis = plt.subplots(figsize=(5.6, 3.8))
    contour = axis.contourf(scale_values, exponent_values, surface, levels=18, cmap="viridis")
    figure.colorbar(contour, ax=axis, label="Average power (W)")
    axis.set(xlabel="Scale λ", ylabel="Exponent p", title="Q2 nonlinear-damping coarse objective")
    written["q2_nonlinear_surface"] = _finish(figure, "q2_nonlinear_surface")
    export_origin_table(ORIGIN / "q2_nonlinear_surface.xlsx", coarse, x_column="scale", metadata={"purpose": "Q2 nonlinear coarse objective surface"})
    export_origin_table(
        ORIGIN / "q2_optimum_neighborhood.xlsx",
        q2["NonlinearNeighborhood"],
        metadata={"purpose": "Q2 final nonlinear optimum neighborhood"},
    )

    q2_metrics = json.loads((RESULTS / "q2_metrics.json").read_text(encoding="utf-8"))
    q2_wave = wave_case(2)
    q2_scale = q2_metrics["nonlinear"]["optimal_scale"]
    q2_exponent = q2_metrics["nonlinear"]["optimal_exponent"]
    equivalent_damping = max(1.0, q2_scale * 0.1**q2_exponent)
    q2_guess = harmonic_state([0.0], q2_wave.omega, heave_frequency_response(q2_wave, equivalent_damping))[:, 0]
    q2_orbit = solve_periodic_orbit(
        heave_rhs(q2_wave, q2_scale, q2_exponent),
        q2_wave.omega,
        q2_guess,
        samples_per_cycle=512,
        rtol=1e-10,
        atol=1e-12,
    )
    q2_relative_velocity = q2_orbit.ode.state[3] - q2_orbit.ode.state[2]
    export_origin_table(
        ORIGIN / "q2_optimal_power_time.xlsx",
        pd.DataFrame(
            {
                "time_s": q2_orbit.ode.time,
                "relative_velocity_m_s": q2_relative_velocity,
                "instantaneous_power_w": heave_power(q2_relative_velocity, q2_scale, q2_exponent),
            }
        ),
        x_column="time_s",
        metadata={"purpose": "Q2 strict periodic optimum instantaneous PTO power", "period_s": q2_wave.period},
    )

    q3 = solve_formal()
    q3_matrix = q3_official_matrix(q3)
    q3_frame = pd.DataFrame(
        q3_matrix,
        columns=["time_s", "float_heave_m", "float_velocity_m_s", "float_pitch_rad", "float_pitch_rate_rad_s", "oscillator_heave_m", "oscillator_velocity_m_s", "oscillator_pitch_rad", "oscillator_pitch_rate_rad_s"],
    )
    use_paper_style()
    figure, axes = plt.subplots(2, 1, figsize=(6.4, 5.4), sharex=True)
    axes[0].plot(q3_frame["time_s"], q3_frame["float_heave_m"], label="Float", color=COLORS[0])
    axes[0].plot(q3_frame["time_s"], q3_frame["oscillator_heave_m"], label="Oscillator", color=COLORS[1])
    axes[0].set(ylabel="Heave (m)", title="Q3 coupled heave and pitch response")
    axes[1].plot(q3_frame["time_s"], q3_frame["float_pitch_rad"], label="Float", color=COLORS[0])
    axes[1].plot(q3_frame["time_s"], q3_frame["oscillator_pitch_rad"], label="Oscillator", color=COLORS[1])
    axes[1].set(xlabel="Time (s)", ylabel="Pitch (rad)")
    for axis in axes: axis.grid(True, color="#D9D9D9", linewidth=0.5); axis.legend(ncol=2)
    written["q3_coupled_response"] = _finish(figure, "q3_coupled_response")
    export_origin_table(ORIGIN / "q3_coupled_response.xlsx", q3_frame, x_column="time_s", metadata={"purpose": "Q3 final nonlinear coupled response", "angle_unit": "rad"})

    q4 = pd.read_excel(RESULTS / "q4_optimization.xlsx", sheet_name=None)
    q4_coarse = q4["CoarseSurface"]
    linear_values = np.sort(q4_coarse["linear_damping"].unique())
    rotation_values = np.sort(q4_coarse["rotational_damping"].unique())
    q4_surface = q4_coarse.pivot(index="rotational_damping", columns="linear_damping", values="total_power_w").loc[rotation_values, linear_values].to_numpy()
    q4_metrics = json.loads((RESULTS / "q4_metrics.json").read_text(encoding="utf-8"))
    use_paper_style()
    figure, axis = plt.subplots(figsize=(5.6, 3.8))
    contour = axis.contourf(linear_values, rotation_values, q4_surface, levels=18, cmap="viridis")
    figure.colorbar(contour, ax=axis, label="Total power (W)")
    axis.scatter([q4_metrics["optimal_linear_damping_n_s_m"]], [q4_metrics["optimal_rotational_damping_n_m_s"]], color="white", edgecolor="black", s=38, label="Refined optimum")
    axis.set(xlabel="Linear damping (N·s/m)", ylabel="Rotational damping (N·m·s)", title="Q4 nonlinear coupled objective")
    axis.set_ylim(float(rotation_values.min()), float(rotation_values.max()) * 1.04)
    axis.legend(loc="upper right")
    written["q4_power_surface"] = _finish(figure, "q4_power_surface")
    export_origin_table(ORIGIN / "q4_power_surface.xlsx", q4_coarse, x_column="linear_damping", metadata={"purpose": "Q4 nonlinear coupled coarse objective surface"})
    export_origin_table(
        ORIGIN / "q4_optimum_neighborhood.xlsx",
        q4["Neighborhood"],
        metadata={"purpose": "Q4 final two-dimensional optimum neighborhood"},
    )

    split = pd.DataFrame({"channel": ["Linear PTO", "Rotational PTO"], "average_power_w": [q4_metrics["heave_power_w"], q4_metrics["rotation_power_w"]]})
    use_paper_style()
    figure, axis = plt.subplots(figsize=(4.8, 3.4))
    bars = axis.bar(split["channel"], split["average_power_w"], color=[COLORS[0], COLORS[1]])
    axis.set_yscale("log")
    axis.bar_label(bars, labels=[f"{value:.4g} W" for value in split["average_power_w"]], padding=3)
    axis.set(ylabel="Average power (W, log scale)", title="Q4 optimal PTO power split")
    axis.grid(True, axis="y", color="#D9D9D9", linewidth=0.5)
    written["q4_power_split"] = _finish(figure, "q4_power_split")
    export_origin_table(ORIGIN / "q4_power_split.xlsx", split, metadata={"purpose": "Q4 optimal linear/rotational PTO power split"})

    manifest = {"figures": written, "origin_files": sorted(str(path) for path in ORIGIN.glob("*.xlsx"))}
    (RESULTS / "figure_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
