"""Paper figures and one-figure-one-table Origin exports from FINAL 2023A data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.export import export_origin_table
from core.plotting import COLORS, save_figure, use_paper_style
from layout import apply_radial_zones, generate_hexagonal_layout
from problem_data import FIELD_RADIUS_M, RESULT_DIR, TOWER_EXCLUSION_M, load_q1_design


FIGURE_DIR = RESULT_DIR / "figures"
ORIGIN_DIR = RESULT_DIR / "origin_data"


def _circle(axis, radius, center=(0.0, 0.0), **kwargs):
    angle = np.linspace(0.0, 2.0 * np.pi, 500)
    axis.plot(center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle), **kwargs)


def run():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    ORIGIN_DIR.mkdir(parents=True, exist_ok=True)
    use_paper_style()

    q1 = load_q1_design()
    q2 = generate_hexagonal_layout([0.0, 50.0], 6.5, 6.5, 3.3, spacing_gap=0.05)
    q3, zone = apply_radial_zones(
        q2,
        (0.25, 0.50, 0.75),
        (6.54, 6.48, 6.42, 6.36),
        (6.54, 6.48, 6.42, 6.36),
        tuple(value / 2.0 + 0.05 for value in (6.54, 6.48, 6.42, 6.36)),
    )

    fig, ax = plt.subplots(figsize=(5.0, 4.6))
    ax.scatter(q1.centers[:, 0], q1.centers[:, 1], s=3.5, color=COLORS[0], alpha=0.75)
    _circle(ax, FIELD_RADIUS_M, color="#333333", linewidth=0.8)
    _circle(ax, TOWER_EXCLUSION_M, color=COLORS[1], linewidth=0.8, linestyle="--")
    ax.scatter([0], [0], marker="^", s=45, color=COLORS[1], label="Receiver tower")
    ax.set(xlabel="East x (m)", ylabel="North y (m)", title="Q1 official heliostat field (1745 mirrors)")
    ax.set_aspect("equal"); ax.legend(); fig.tight_layout(); save_figure(fig, FIGURE_DIR / "q1_field_layout"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    axes[0].scatter(q2.centers[:, 0], q2.centers[:, 1], s=2.5, color=COLORS[0], alpha=0.7)
    axes[0].scatter(q2.tower_xy[0], q2.tower_xy[1], marker="^", s=38, color=COLORS[1])
    axes[0].set_title("Q2 triangular lattice")
    for index in range(4):
        mask = zone == index
        axes[1].scatter(q3.centers[mask, 0], q3.centers[mask, 1], s=2.8, alpha=0.72, color=COLORS[index], label=f"Zone {index+1}: {q3.widths[mask][0]:.2f} m")
    axes[1].scatter(q3.tower_xy[0], q3.tower_xy[1], marker="^", s=38, color="#222222")
    axes[1].set_title("Q3 radial size zones"); axes[1].legend(markerscale=3, fontsize=7)
    for axis in axes:
        _circle(axis, FIELD_RADIUS_M, color="#333333", linewidth=0.7)
        _circle(axis, TOWER_EXCLUSION_M, center=q2.tower_xy, color=COLORS[1], linewidth=0.7, linestyle="--")
        axis.set(xlabel="East x (m)", ylabel="North y (m)"); axis.set_aspect("equal")
    fig.tight_layout(); save_figure(fig, FIGURE_DIR / "q2_q3_layout_comparison"); plt.close(fig)

    monthly_frames = {}
    for label in ("q1", "q2", "q3"):
        monthly_frames[label.upper()] = pd.read_csv(RESULT_DIR / f"{label}_monthly_results.csv")
    monthly_eff = pd.DataFrame({"month": np.arange(1, 13)})
    monthly_power = pd.DataFrame({"month": np.arange(1, 13)})
    for label, frame in monthly_frames.items():
        monthly_eff[f"{label}_eta_total"] = frame["eta_total"]
        monthly_eff[f"{label}_eta_cos"] = frame["eta_cos"]
        monthly_eff[f"{label}_eta_sb"] = frame["eta_sb"]
        monthly_eff[f"{label}_eta_trunc"] = frame["eta_trunc"]
        monthly_power[f"{label}_power_MW"] = frame["power_kw"] / 1000.0
        monthly_power[f"{label}_power_per_area_kW_m2"] = frame["power_per_area_kw_m2"]
    export_origin_table(ORIGIN_DIR / "monthly_efficiency.xlsx", monthly_eff, x_column="month", metadata={"source": "FINAL 60-point calculations", "unit": "efficiencies are dimensionless"})
    export_origin_table(ORIGIN_DIR / "monthly_power.xlsx", monthly_power, x_column="month", metadata={"source": "FINAL 60-point calculations"})

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    for index, label in enumerate(monthly_frames):
        axes[0].plot(monthly_eff["month"], monthly_eff[f"{label}_eta_total"], marker="o", ms=3, color=COLORS[index], label=label)
        axes[1].plot(monthly_power["month"], monthly_power[f"{label}_power_MW"], marker="o", ms=3, color=COLORS[index], label=label)
    axes[0].set(xlabel="Month", ylabel="Mean optical efficiency", title="Seasonal optical efficiency")
    axes[1].set(xlabel="Month", ylabel="Mean thermal power (MW)", title="Seasonal thermal output")
    for axis in axes: axis.grid(True, color="#dddddd", linewidth=0.5); axis.legend()
    fig.tight_layout(); save_figure(fig, FIGURE_DIR / "monthly_efficiency_and_power"); plt.close(fig)

    detail = pd.read_csv(RESULT_DIR / "q1_march21_noon_mirror_detail.csv")
    export_origin_table(
        ORIGIN_DIR / "efficiency_distribution.xlsx",
        detail[["mirror_id", "x_m", "y_m", "eta_cos", "eta_at", "eta_sb", "eta_trunc", "eta_total", "power_kw"]],
        x_column="mirror_id",
        metadata={"time": "March 21, 12:00 local time", "coordinate": "ENU, m"},
    )
    fig, ax = plt.subplots(figsize=(5.2, 4.3))
    scatter = ax.scatter(detail["x_m"], detail["y_m"], c=detail["eta_total"], s=8, cmap="viridis", vmin=0, vmax=1)
    fig.colorbar(scatter, ax=ax, label="Total optical efficiency")
    ax.set(xlabel="East x (m)", ylabel="North y (m)", title="Q1 efficiency distribution: Mar 21, 12:00")
    ax.set_aspect("equal"); fig.tight_layout(); save_figure(fig, FIGURE_DIR / "q1_efficiency_distribution"); plt.close(fig)

    q2_search = pd.read_csv(RESULT_DIR / "q2_optimization_search.csv")
    size_slice = q2_search[(q2_search["tower_y_m"] == 50.0) & (q2_search["width_m"] == q2_search["height_m"])].sort_values("width_m")
    export_origin_table(
        ORIGIN_DIR / "optimization_convergence.xlsx",
        size_slice[["candidate", "width_m", "screen_power_kw", "screen_power_per_area_kw_m2"]],
        x_column="candidate",
        metadata={"note": "deterministic candidate search, not an iterative stochastic convergence trace", "precision": "FAST, 12-point screen"},
    )
    q3_search = pd.read_csv(RESULT_DIR / "q3_optimization_search.csv")
    before_after = pd.DataFrame(
        {
            "design": ["Q1", "Q2", "Q3"],
            "mirror_count": [1745, 3054, 3054],
            "total_area_m2": [float(np.sum(q1.areas)), float(np.sum(q2.areas)), float(np.sum(q3.areas))],
            "annual_power_MW": [35.374777949653605, 60.89583835926479, 60.65629578501832],
            "annual_power_per_area_kW_m2": [0.5631133070622987, 0.4719455199642319, 0.4773538445605828],
        }
    )
    export_origin_table(ORIGIN_DIR / "before_after_comparison.xlsx", before_after, x_column="design", metadata={"source": "FINAL values"})
    sensitivity = pd.read_csv(RESULT_DIR / "q3_sensitivity.csv")
    feasible_sensitivity = sensitivity[sensitivity["status"] == "FAST"].copy()
    export_origin_table(ORIGIN_DIR / "parameter_sensitivity.xlsx", feasible_sensitivity, x_column="scale", metadata={"precision": "FAST 12-point screen", "excluded": "positive scales are geometrically infeasible and remain documented in q3_sensitivity.csv"})
    export_origin_table(ORIGIN_DIR / "q3_zone_search.xlsx", q3_search, x_column="candidate", metadata={"precision": "FAST 12-point screen"})

    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(size_slice["width_m"], size_slice["screen_power_per_area_kw_m2"], marker="o", color=COLORS[0])
    feasible = size_slice["screen_power_kw"] >= 60350.0
    ax.scatter(size_slice.loc[feasible, "width_m"], size_slice.loc[feasible, "screen_power_per_area_kw_m2"], color=COLORS[1], zorder=3, label="Screen-feasible")
    ax.set(xlabel="Common mirror side length (m)", ylabel="Power per mirror area (kW/m²)", title="Q2 size slice and rated-power boundary")
    ax.grid(True, color="#dddddd", linewidth=0.5); ax.legend(); fig.tight_layout(); save_figure(fig, FIGURE_DIR / "q2_size_slice"); plt.close(fig)

    print(f"Generated figures in {FIGURE_DIR} and Origin data in {ORIGIN_DIR}")


if __name__ == "__main__":
    run()
