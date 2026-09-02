"""Q1 fixed-strategy continuous obscuration calculation and validation."""

from __future__ import annotations

from math import pi
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from core.export import export_origin_table
from core.performance import benchmark
from core.plotting import COLORS, save_figure, use_paper_style
from core.validation import ValidationReport
import matplotlib.pyplot as plt

from common import (
    PRECISIONS,
    Strategy,
    cloud_center,
    event_value_m2,
    feasible_active_window,
    interval_duration,
    merge_intervals,
    missile_position,
    obscuration_intervals,
    target_surface_points,
)
from problem_data import TARGET_CENTER_M

RESULTS = ROOT / "results" / "2025A"


def q1_strategy() -> Strategy:
    return Strategy("FY1", "M1", pi, 120.0, 1.5, 3.6)


def sampled_intervals(strategy: Strategy, model: str, dt_s: float, *, precision: str = "FINAL"):
    """Independent fixed-step cross-check with linearly interpolated crossings."""
    start, stop = feasible_active_window(strategy)
    points = target_surface_points(precision) if model == "full" else None
    count = int(np.ceil((stop - start) / dt_s)) + 1
    time = np.linspace(start, stop, count)
    values = np.array([event_value_m2(strategy, t, model=model, surface_points=points) for t in time])
    crossings = []
    for a, b, fa, fb in zip(time[:-1], time[1:], values[:-1], values[1:]):
        if fa == 0.0:
            crossings.append(float(a))
        elif np.signbit(fa) != np.signbit(fb):
            crossings.append(float(a - fa * (b - a) / (fb - fa)))
    bounds = [start, *crossings, stop]
    intervals = []
    for left, right in zip(bounds[:-1], bounds[1:]):
        if event_value_m2(strategy, 0.5 * (left + right), model=model, surface_points=points) <= 0:
            intervals.append((left, right))
    return merge_intervals(intervals), time, values


def solve_q1():
    strategy = q1_strategy()
    started = perf_counter()
    rows = []
    results = {}
    for model in ("point", "full"):
        for level in ("FAST", "STANDARD", "FINAL"):
            result = obscuration_intervals(strategy, model=model, precision=level)
            results[(model, level)] = result
            rows.append(
                {
                    "model": model,
                    "precision": level,
                    "start_s": result.intervals_s[0][0] if result.intervals_s else np.nan,
                    "end_s": result.intervals_s[-1][1] if result.intervals_s else np.nan,
                    "duration_s": result.duration_s,
                    "root_residual_max_m2": result.root_residual_max_m2,
                }
            )
    final = results[("full", "FINAL")]
    scan_rows = []
    for dt_s in (0.01, 0.005, 0.0025):
        intervals, _, _ = sampled_intervals(strategy, "full", dt_s)
        duration = interval_duration(intervals)
        scan_rows.append({"dt_s": dt_s, "duration_s": duration, "absolute_difference_s": abs(duration - final.duration_s)})

    event = lambda time_s: event_value_m2(strategy, time_s, model="full", surface_points=target_surface_points("FINAL"))
    epsilon_s = 1e-5
    direction_checks = []
    for start, stop in final.intervals_s:
        direction_checks.extend(
            [
                event(start - epsilon_s) > 0,
                abs(event(start)) <= 1e-6,
                event(start + epsilon_s) < 0,
                event(stop - epsilon_s) < 0,
                abs(event(stop)) <= 1e-6,
                event(stop + epsilon_s) > 0,
            ]
        )
    durations = [results[("full", level)].duration_s for level in ("FAST", "STANDARD", "FINAL")]
    report = (
        ValidationReport()
        .add("Q1 physical feasibility", final.feasible and final.burst_point_m[2] >= 0)
        .add("Q1 event root residual", final.root_residual_max_m2 <= 1e-6, f"max={final.root_residual_max_m2:.3e} m^2")
        .add("Q1 event direction", all(direction_checks), "outside -> inside -> outside")
        .add("Q1 surface convergence", abs(durations[-1] - durations[-2]) <= 1e-6, f"FAST/STANDARD/FINAL={durations}")
        .add("Q1 fixed-step cross-check", scan_rows[-1]["absolute_difference_s"] <= 2e-5, str(scan_rows))
        .add("Model interpretation", manual=True, detail="MODEL_CONFIRMATION_REQUIRED: full cylinder is primary; representative point is comparator")
    )
    return {
        "strategy": strategy,
        "results": results,
        "precision_table": pd.DataFrame(rows),
        "scan_table": pd.DataFrame(scan_rows),
        "validation": report,
        "elapsed_s": perf_counter() - started,
    }


def make_figures(solution):
    RESULTS.mkdir(parents=True, exist_ok=True)
    figure_dir = RESULTS / "figures"
    origin_dir = RESULTS / "origin_data"
    figure_dir.mkdir(parents=True, exist_ok=True)
    origin_dir.mkdir(parents=True, exist_ok=True)
    strategy = solution["strategy"]
    start, stop = feasible_active_window(strategy)
    time = np.linspace(max(start, 7.5), min(stop, 10.0), 1001)
    full_points = target_surface_points("FINAL")
    point_value = np.array([event_value_m2(strategy, t, model="point") for t in time])
    full_value = np.array([event_value_m2(strategy, t, model="full", surface_points=full_points) for t in time])

    use_paper_style()
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ax.axhline(0.0, color="#555555", linewidth=0.8)
    point_margin = np.sqrt(np.maximum(0.0, point_value + 100.0)) - 10.0
    full_margin = np.sqrt(np.maximum(0.0, full_value + 100.0)) - 10.0
    ax.plot(time, point_margin, color=COLORS[0], label="Model A: target center")
    ax.plot(time, full_margin, color=COLORS[1], label="Model B: full cylinder")
    for left, right in solution["results"][("full", "FINAL")].intervals_s:
        ax.axvspan(left, right, color=COLORS[2], alpha=0.16, label="Effective interval")
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys())
    ax.set(xlabel="Time after detection (s)", ylabel="Sight-line distance margin (m)", title="Q1 continuous obscuration event")
    ax.grid(True, color="#D9D9D9", linewidth=0.5)
    fig.tight_layout()
    save_figure(fig, figure_dir / "q1_event")
    plt.close(fig)

    trajectory_time = np.linspace(0.0, 12.0, 241)
    missile = missile_position("M1", trajectory_time)
    cloud_time = np.linspace(strategy.burst_time_s, 12.0, 139)
    cloud = np.array([cloud_center(strategy, t) for t in cloud_time])
    burst = solution["results"][("full", "FINAL")].burst_point_m
    use_paper_style()
    fig, (ax_xz, ax_xy) = plt.subplots(1, 2, figsize=(8.2, 3.4))
    ax_xz.plot(missile[:, 0], missile[:, 2], color=COLORS[0], label="M1")
    ax_xz.plot(cloud[:, 0], cloud[:, 2], color=COLORS[1], label="Cloud center")
    ax_xz.scatter(TARGET_CENTER_M[0], TARGET_CENTER_M[2], color=COLORS[2], s=24, label="True target")
    ax_xz.scatter(burst[0], burst[2], color=COLORS[3], s=24, label="Burst")
    ax_xz.set(xlabel="x (m)", ylabel="z (m)", title="Vertical projection (x-z)")
    ax_xz.grid(True, color="#D9D9D9", linewidth=0.5)
    ax_xz.legend(fontsize=8)
    ax_xy.plot(missile[:, 0], missile[:, 1], color=COLORS[0], label="M1")
    ax_xy.plot(cloud[:, 0], cloud[:, 1], color=COLORS[1], label="Cloud center")
    ax_xy.scatter(TARGET_CENTER_M[0], TARGET_CENTER_M[1], color=COLORS[2], s=24, label="True target")
    ax_xy.scatter(burst[0], burst[1], color=COLORS[3], s=24, label="Burst")
    ax_xy.set(xlabel="x (m)", ylabel="y (m)", title="Horizontal projection (x-y)")
    ax_xy.grid(True, color="#D9D9D9", linewidth=0.5)
    fig.tight_layout()
    save_figure(fig, figure_dir / "q1_geometry")
    plt.close(fig)

    export_origin_table(
        origin_dir / "q1_event.xlsx",
        pd.DataFrame({"time_s": time, "point_margin_m": point_margin, "full_cylinder_margin_m": full_margin}),
        x_column="time_s",
        metadata={"purpose": "Locate and compare Q1 obscuration intervals", "negative_means": "effective obscuration"},
    )
    export_origin_table(
        origin_dir / "q1_trajectory.xlsx",
        pd.DataFrame({"time_s": trajectory_time, "missile_x_m": missile[:, 0], "missile_y_m": missile[:, 1], "missile_z_m": missile[:, 2]}),
        x_column="time_s",
        metadata={"purpose": "Q1 M1 trajectory; cloud trajectory is stored in q1_event-derived files"},
    )


def write_outputs(solution):
    RESULTS.mkdir(parents=True, exist_ok=True)
    solution["precision_table"].to_csv(RESULTS / "q1_precision.csv", index=False)
    solution["scan_table"].to_csv(RESULTS / "q1_step_convergence.csv", index=False)
    final = solution["results"][("full", "FINAL")]
    comparator = solution["results"][("point", "FINAL")]
    text = "\n".join(
        [
            "Q1 fixed strategy result",
            f"primary_model=full cylinder (MODEL_CONFIRMATION_REQUIRED)",
            f"burst_point_m={final.burst_point_m.tolist()}",
            f"full_intervals_s={list(final.intervals_s)}",
            f"full_duration_s={final.duration_s:.12f}",
            f"point_duration_s={comparator.duration_s:.12f}",
            f"root_residual_max_m2={final.root_residual_max_m2:.6e}",
            f"elapsed_s={solution['elapsed_s']:.6f}",
            "",
            solution["validation"].render(),
        ]
    )
    (RESULTS / "q1_result.txt").write_text(text, encoding="utf-8")


def main():
    solution = solve_q1()
    make_figures(solution)
    write_outputs(solution)
    timing = benchmark(lambda: obscuration_intervals(q1_strategy(), model="full", precision="FINAL"), repeats=5, warmup=1)
    final = solution["results"][("full", "FINAL")]
    print(f"Q1 full-cylinder duration: {final.duration_s:.9f} s; intervals={final.intervals_s}")
    print(f"Q1 point comparator: {solution['results'][('point', 'FINAL')].duration_s:.9f} s")
    print(f"Single FINAL event solve median: {timing['median_seconds']:.6f} s")
    print(solution["validation"].render())


if __name__ == "__main__":
    main()
