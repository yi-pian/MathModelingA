"""Q2 single-bomb design with slice analysis and multi-seed refinement."""

from __future__ import annotations

import argparse
import json
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
from core.optimization import optimize_global, optimize_local
from core.plotting import COLORS, save_figure, use_paper_style
from core.validation import ValidationReport, check_bounds, check_constraints
import matplotlib.pyplot as plt

from common import (
    Precision,
    Strategy,
    event_value_m2,
    feasible_active_window,
    missile_arrival_time,
    obscuration_intervals,
    target_surface_points,
)
from problem_data import GRAVITY_M_S2, UAV_INITIAL_M, UAV_SPEED_BOUNDS_M_S

RESULTS = ROOT / "results" / "2025A"
PROFILES = {
    "FAST": {"seeds": [0], "popsize": 7, "point_iter": 25, "full_iter": 35, "slice_n": 13},
    "STANDARD": {"seeds": [0, 1, 2], "popsize": 9, "point_iter": 45, "full_iter": 55, "slice_n": 21},
    "FINAL": {"seeds": [0, 1, 2], "popsize": 12, "point_iter": 70, "full_iter": 85, "slice_n": 31},
}


def variable_bounds():
    max_delay = float(np.sqrt(2.0 * UAV_INITIAL_M["FY1"][2] / GRAVITY_M_S2))
    return [(0.0, 2.0 * np.pi), UAV_SPEED_BOUNDS_M_S, (0.0, missile_arrival_time("M1")), (0.0, max_delay)]


def variables_to_strategy(values) -> Strategy | None:
    heading, speed, burst_time, delay = map(float, values)
    if delay > burst_time:
        return None
    try:
        return Strategy("FY1", "M1", heading, speed, burst_time - delay, delay)
    except ValueError:
        return None


def guided_fitness(values, model: str, precision: str = "FAST") -> float:
    """Lexicographic guide: duration first; near-miss depth only breaks zero ties."""
    strategy = variables_to_strategy(values)
    if strategy is None:
        return -1e12
    window = feasible_active_window(strategy)
    if window is None:
        return -1e12
    result = obscuration_intervals(strategy, model=model, precision=precision)
    if result.duration_s > 0.0:
        return 1e6 + result.duration_s
    points = target_surface_points(precision) if model == "full" else None
    times = np.linspace(*window, 21)
    min_event_m2 = min(event_value_m2(strategy, t, model=model, surface_points=points) for t in times)
    return -float(min_event_m2)


def duration_objective(values, precision: str | Precision = "FAST") -> float:
    strategy = variables_to_strategy(values)
    if strategy is None:
        return -1e6
    return obscuration_intervals(strategy, model="full", precision=precision).duration_s


def slice_analysis(anchor=None, *, count=31):
    if anchor is None:
        anchor = np.array([0.10, 120.0, 1.0, 0.5])
    headings = np.linspace(0.0, 2.0 * np.pi, 73)
    heading_duration = [duration_objective([value, anchor[1], anchor[2], anchor[3]], "FAST") for value in headings]
    speeds = np.linspace(70.0, 140.0, count)
    speed_duration = [duration_objective([anchor[0], value, anchor[2], anchor[3]], "FAST") for value in speeds]
    burst_times = np.linspace(0.2, 4.0, count)
    delay_fractions = np.linspace(0.0, 1.0, count)
    heatmap = np.empty((count, count))
    for row, fraction in enumerate(delay_fractions):
        for column, burst_time in enumerate(burst_times):
            heatmap[row, column] = duration_objective([anchor[0], anchor[1], burst_time, fraction * burst_time], "FAST")
    return {
        "heading": pd.DataFrame({"heading_rad": headings, "duration_s": heading_duration}),
        "speed": pd.DataFrame({"speed_m_s": speeds, "duration_s": speed_duration}),
        "burst_times": burst_times,
        "delay_fractions": delay_fractions,
        "heatmap": heatmap,
    }


def optimize_q2(mode="FINAL", *, use_cache=True):
    profile = PROFILES[mode]
    cache_dir = RESULTS / "cache" / mode
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "q2_search.json"
    bounds = variable_bounds()
    started = perf_counter()
    candidates = []
    if use_cache and cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        candidates = payload["candidates"]
    else:
        for model, iterations in (("point", profile["point_iter"]), ("full", profile["full_iter"])):
            for seed in profile["seeds"]:
                result = optimize_global(
                    lambda x, chosen=model: guided_fitness(x, chosen, "FAST"),
                    bounds,
                    direction="maximize",
                    seed=seed,
                    polish=False,
                    popsize=profile["popsize"],
                    maxiter=iterations,
                    tol=1e-7,
                )
                strategy = variables_to_strategy(result.x)
                full_duration = 0.0 if strategy is None else obscuration_intervals(strategy, model="full", precision="FAST").duration_s
                candidates.append(
                    {
                        "stage": model,
                        "seed": seed,
                        "search_success": result.success,
                        "search_message": result.message,
                        "search_iterations": result.iterations,
                        "search_nfev": result.nfev,
                        "guided_objective": result.objective,
                        "full_fast_duration_s": full_duration,
                        "x": np.asarray(result.x).tolist(),
                    }
                )
        cache_path.write_text(json.dumps({"mode": mode, "candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")

    best = max(candidates, key=lambda item: item["full_fast_duration_s"])
    first_refine = optimize_local(
        lambda x: duration_objective(x, "FAST"),
        best["x"],
        bounds=bounds,
        method="Nelder-Mead",
        direction="maximize",
        options={"maxiter": 500, "xatol": 1e-6, "fatol": 1e-7},
    )
    refine_precision = Precision("FINAL_REFINE", 0.05, 96, 9, 5, 1e-9, 1e-7) if mode == "FINAL" else mode
    final_refine = optimize_local(
        lambda x: duration_objective(x, refine_precision),
        first_refine.x,
        bounds=bounds,
        method="Nelder-Mead",
        direction="maximize",
        options={"maxiter": 350, "xatol": 1e-5, "fatol": 1e-7},
    )
    convergence_polish = None
    if not final_refine.success:
        convergence_polish = optimize_local(
            lambda x: duration_objective(x, refine_precision),
            final_refine.x,
            bounds=bounds,
            method="Nelder-Mead",
            direction="maximize",
            options={"maxiter": 400, "xatol": 2e-5, "fatol": 2e-7},
        )
    accepted = final_refine if final_refine.success else convergence_polish if convergence_polish.success else first_refine
    if not accepted.success:
        raise RuntimeError(f"Q2 local refinement failed: {accepted.message}")
    strategy = variables_to_strategy(accepted.x)
    if strategy is None:
        raise RuntimeError("Q2 accepted optimizer output is infeasible")
    precision_results = {level: obscuration_intervals(strategy, model="full", precision=level) for level in ("FAST", "STANDARD", "FINAL")}
    point_result = obscuration_intervals(strategy, model="point", precision="FINAL")
    final = precision_results["FINAL"]

    burst_height = final.burst_point_m[2]
    margins = [
        strategy.speed_m_s - 70.0,
        140.0 - strategy.speed_m_s,
        strategy.drop_time_s,
        strategy.delay_s,
        burst_height,
        missile_arrival_time("M1") - strategy.burst_time_s,
    ]
    perturbations = []
    accepted_x = np.asarray(accepted.x, dtype=float)
    steps = np.array([2e-5, 1e-2, 2e-5, 2e-5])
    for index in range(4):
        for sign in (-1.0, 1.0):
            neighbor = accepted_x.copy()
            neighbor[index] += sign * steps[index]
            if variables_to_strategy(neighbor) is not None and check_bounds(neighbor, np.array(bounds)[:, 0], np.array(bounds)[:, 1]):
                perturbations.append(duration_objective(neighbor, "FINAL"))
    report = (
        ValidationReport()
        .add("Q2 optimizer success", accepted.success, accepted.message)
        .add("Q2 finite strategy", np.all(np.isfinite(accepted.x)))
        .add("Q2 variable bounds", check_bounds(accepted.x, np.array(bounds)[:, 0], np.array(bounds)[:, 1]))
        .add("Q2 physical constraints", check_constraints(margins, sense="ge"), f"margins={margins}")
        .add("Q2 root residual", final.root_residual_max_m2 <= 1e-6, f"max={final.root_residual_max_m2:.3e} m^2")
        .add("Q2 surface convergence", abs(precision_results["FINAL"].duration_s - precision_results["STANDARD"].duration_s) <= 1e-3)
        .add("Q2 local perturbation", all(value <= final.duration_s + 2e-4 for value in perturbations), f"neighbor max={max(perturbations):.9f}")
        .add("Q2 multiple seeds", len(profile["seeds"]) >= 3 if mode != "FAST" else True, f"seeds={profile['seeds']}")
        .add("Model interpretation", manual=True, detail="MODEL_CONFIRMATION_REQUIRED")
    )
    slices = slice_analysis(count=profile["slice_n"])
    return {
        "mode": mode,
        "strategy": strategy,
        "variables": np.asarray(accepted.x),
        "candidates": candidates,
        "first_refine": first_refine,
        "final_refine": final_refine,
        "convergence_polish": convergence_polish,
        "precision_results": precision_results,
        "point_result": point_result,
        "validation": report,
        "slices": slices,
        "elapsed_s": perf_counter() - started,
    }


def write_outputs(solution):
    RESULTS.mkdir(parents=True, exist_ok=True)
    origin_dir = RESULTS / "origin_data"
    figure_dir = RESULTS / "figures"
    origin_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    strategy = solution["strategy"]
    final = solution["precision_results"]["FINAL"]
    rows = []
    for level, result in solution["precision_results"].items():
        rows.append({"precision": level, "duration_s": result.duration_s, "start_s": result.intervals_s[0][0], "end_s": result.intervals_s[-1][1], "root_residual_max_m2": result.root_residual_max_m2})
    pd.DataFrame(rows).to_csv(RESULTS / "q2_precision.csv", index=False)
    pd.DataFrame(solution["candidates"]).drop(columns=["x"]).to_csv(RESULTS / "q2_multiseed.csv", index=False)
    solution["slices"]["heading"].to_csv(RESULTS / "q2_heading_slice.csv", index=False)
    solution["slices"]["speed"].to_csv(RESULTS / "q2_speed_slice.csv", index=False)

    summary = {
        "heading_rad": strategy.heading_rad,
        "heading_deg": strategy.heading_deg,
        "speed_m_s": strategy.speed_m_s,
        "drop_time_s": strategy.drop_time_s,
        "delay_s": strategy.delay_s,
        "burst_time_s": strategy.burst_time_s,
        "drop_point_m": __import__("common").drop_point(strategy).tolist(),
        "burst_point_m": final.burst_point_m.tolist(),
        "full_intervals_s": list(final.intervals_s),
        "full_duration_s": final.duration_s,
        "point_duration_s": solution["point_result"].duration_s,
        "elapsed_s": solution["elapsed_s"],
        "first_refine_success": solution["first_refine"].success,
        "final_refine_success": solution["final_refine"].success,
        "convergence_polish_success": None if solution["convergence_polish"] is None else solution["convergence_polish"].success,
        "global_search_nfev": sum(int(item.get("search_nfev") or 0) for item in solution["candidates"]),
        "local_refinement_nfev": {
            "first": solution["first_refine"].nfev,
            "final": solution["final_refine"].nfev,
            "convergence_polish": None if solution["convergence_polish"] is None else solution["convergence_polish"].nfev,
        },
    }
    (RESULTS / "q2_result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS / "q2_validation.txt").write_text(solution["validation"].render(), encoding="utf-8")

    use_paper_style()
    fig, (left, right) = plt.subplots(1, 2, figsize=(8.2, 3.3))
    heading = solution["slices"]["heading"]
    speed = solution["slices"]["speed"]
    left.plot(np.degrees(heading["heading_rad"]), heading["duration_s"], color=COLORS[0])
    left.axvline(strategy.heading_deg, color=COLORS[1], linestyle="--", label="Accepted")
    left.set(xlabel="Heading (degree)", ylabel="Obscuration duration (s)", title="Heading slice")
    left.legend(); left.grid(True, color="#D9D9D9", linewidth=0.5)
    right.plot(speed["speed_m_s"], speed["duration_s"], color=COLORS[0])
    right.axvline(strategy.speed_m_s, color=COLORS[1], linestyle="--", label="Accepted")
    right.set(xlabel="UAV speed (m/s)", ylabel="Obscuration duration (s)", title="Speed slice")
    right.legend(); right.grid(True, color="#D9D9D9", linewidth=0.5)
    fig.tight_layout(); save_figure(fig, figure_dir / "q2_parameter_slices"); plt.close(fig)

    burst_times = solution["slices"]["burst_times"]
    fractions = solution["slices"]["delay_fractions"]
    use_paper_style(); fig, ax = plt.subplots(figsize=(5.0, 3.7))
    image = ax.imshow(solution["slices"]["heatmap"], origin="lower", aspect="auto", extent=[burst_times[0], burst_times[-1], fractions[0], fractions[-1]], cmap="viridis")
    fig.colorbar(image, ax=ax, label="Obscuration duration (s)")
    ax.scatter(strategy.burst_time_s, strategy.delay_s / strategy.burst_time_s, color="white", edgecolor="black", s=30, label="Accepted")
    ax.set(xlabel="Burst time (s)", ylabel="Delay / burst time", title="Q2 feasible timing slice")
    ax.legend(); fig.tight_layout(); save_figure(fig, figure_dir / "q2_timing_slice"); plt.close(fig)

    export_origin_table(origin_dir / "q2_heading_slice.xlsx", heading.assign(heading_deg=np.degrees(heading["heading_rad"])), x_column="heading_deg", metadata={"purpose": "Q2 heading sensitivity at fixed anchor"})
    export_origin_table(origin_dir / "q2_speed_slice.xlsx", speed, x_column="speed_m_s", metadata={"purpose": "Q2 speed sensitivity at fixed anchor"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=tuple(PROFILES), default="FINAL")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    solution = optimize_q2(args.mode, use_cache=not args.no_cache)
    write_outputs(solution)
    result = solution["precision_results"]["FINAL"]
    strategy = solution["strategy"]
    print(f"Q2 duration={result.duration_s:.9f} s, heading={strategy.heading_deg:.6f} deg, speed={strategy.speed_m_s:.6f} m/s")
    print(f"drop={strategy.drop_time_s:.9f} s, delay={strategy.delay_s:.9f} s, burst={strategy.burst_time_s:.9f} s")
    print(solution["validation"].render())


if __name__ == "__main__":
    main()
