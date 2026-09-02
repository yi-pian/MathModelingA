"""Q3 three-bomb shared-flight optimization and official result1 export."""

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
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))

from core.export import export_origin_table, fill_excel_template
from core.optimization import optimize_global, optimize_local
from core.plotting import COLORS, save_figure, use_paper_style
from core.validation import ValidationReport, check_bounds, check_constraints
import matplotlib.pyplot as plt

from common import (
    Strategy,
    drop_point,
    event_value_m2,
    feasible_active_window,
    interval_duration,
    marginal_interval_gains,
    merge_intervals,
    missile_arrival_time,
    obscuration_intervals,
    target_surface_points,
    validate_drop_gaps,
)
from problem_data import GRAVITY_M_S2, UAV_INITIAL_M

RESULTS = ROOT / "results" / "2025A"
TEMPLATE = ROOT / "data" / "2025A" / "official" / "templates" / "result1.xlsx"
PROFILES = {
    "FAST": {"seeds": [0], "popsize": 5, "iterations": 20},
    "STANDARD": {"seeds": [0, 1, 2], "popsize": 5, "iterations": 30},
    "FINAL": {"seeds": [0, 1, 2], "popsize": 6, "iterations": 45},
}


def joint_bounds():
    max_delay = float(np.sqrt(2.0 * UAV_INITIAL_M["FY1"][2] / GRAVITY_M_S2))
    return [(0.0, 2.0 * np.pi), (70.0, 140.0), (0.0, 10.0), (0.0, 15.0), (0.0, 15.0)] + [(0.0, max_delay)] * 3


def variables_to_strategies(values):
    heading, speed, first_drop, gap2_extra, gap3_extra, delay1, delay2, delay3 = map(float, values)
    drops = [first_drop, first_drop + 1.0 + gap2_extra, first_drop + 2.0 + gap2_extra + gap3_extra]
    try:
        strategies = [Strategy("FY1", "M1", heading, speed, drop, delay, index + 1) for index, (drop, delay) in enumerate(zip(drops, (delay1, delay2, delay3)))]
    except ValueError:
        return None
    if any(strategy.burst_time_s >= missile_arrival_time("M1") for strategy in strategies):
        return None
    return strategies


def strategy_results(strategies, *, model="full", precision="FAST"):
    results = [obscuration_intervals(strategy, model=model, precision=precision) for strategy in strategies]
    union = merge_intervals([interval for result in results for interval in result.intervals_s])
    return results, union, interval_duration(union)


def joint_point_fitness(values):
    strategies = variables_to_strategies(values)
    if strategies is None:
        return -1e12
    results, _, union_duration = strategy_results(strategies, model="point", precision="FAST")
    own_duration = sum(result.duration_s for result in results)
    if union_duration > 0:
        return 1e6 + union_duration + 0.01 * own_duration
    closeness = []
    for strategy, result in zip(strategies, results):
        if result.duration_s > 0:
            closeness.append(0.0)
            continue
        window = feasible_active_window(strategy)
        if window is None:
            return -1e12
        closeness.append(max(0.0, min(event_value_m2(strategy, time_s, model="point") for time_s in np.linspace(*window, 15))))
    return -sum(np.log1p(value) for value in closeness)


def full_union_objective(values, precision="FAST"):
    strategies = variables_to_strategies(values)
    if strategies is None:
        return -1e6
    return strategy_results(strategies, model="full", precision=precision)[2]


def physics_informed_start():
    """Rounded warm start from early/middle/late line-of-sight intercept chaining."""
    return np.array([np.pi, 140.0, 0.03, 2.7, 0.8, 3.6, 5.3, 6.0])


def repair_third_bomb(values, *, seed):
    """Repair a zero/overlapped third bomb by maximizing its exact marginal coverage."""
    values = np.asarray(values, dtype=float).copy()
    strategies = variables_to_strategies(values)
    if strategies is None:
        return values
    first_two = strategies[:2]
    _, _, base = strategy_results(first_two, model="full", precision="FAST")
    second_drop = first_two[-1].drop_time_s
    max_delay = joint_bounds()[-1][1]
    surface = target_surface_points("FAST")

    def candidate(pair):
        drop, delay = map(float, pair)
        try:
            strategy = Strategy("FY1", "M1", values[0], values[1], drop, delay, 3)
        except ValueError:
            return None
        return strategy if strategy.burst_time_s < missile_arrival_time("M1") else None

    def fitness(pair):
        third = candidate(pair)
        if third is None:
            return -1e12
        result = obscuration_intervals(third, model="full", precision="FAST")
        _, _, total = strategy_results([*first_two, third], model="full", precision="FAST")
        gain = total - base
        if gain > 1e-8:
            return 1e6 + gain + 1e-3 * result.duration_s
        if result.duration_s > 0:
            return 1e3 + result.duration_s
        window = feasible_active_window(third)
        if window is None:
            return -1e12
        return -min(event_value_m2(third, t, model="full", surface_points=surface) for t in np.linspace(*window, 21))

    search = optimize_global(
        fitness,
        [(second_drop + 1.0, 25.0), (0.0, max_delay)],
        direction="maximize",
        seed=seed,
        popsize=8,
        maxiter=55,
        tol=1e-7,
        polish=False,
    )
    third_drop, third_delay = search.x
    values[4] = third_drop - second_drop - 1.0
    values[7] = third_delay
    return values


def optimize_q3(mode="FINAL", *, use_cache=True):
    profile = PROFILES[mode]
    cache_dir = RESULTS / "cache" / mode
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "q3_search.json"
    started = perf_counter()
    candidates = []
    if use_cache and cache_path.exists():
        candidates = json.loads(cache_path.read_text(encoding="utf-8"))["candidates"]
    else:
        for seed in profile["seeds"]:
            search = optimize_global(
                joint_point_fitness,
                joint_bounds(),
                direction="maximize",
                seed=seed,
                popsize=profile["popsize"],
                maxiter=profile["iterations"],
                tol=1e-7,
                polish=False,
            )
            repaired = repair_third_bomb(search.x, seed=seed)
            candidates.append({"seed": seed, "search_success": search.success, "message": search.message, "x": repaired.tolist(), "full_fast_duration_s": full_union_objective(repaired, "FAST")})
        warm = physics_informed_start()
        candidates.append({"seed": "physics-informed", "search_success": True, "message": "rounded intercept-chain start", "x": warm.tolist(), "full_fast_duration_s": full_union_objective(warm, "FAST")})
        cache_path.write_text(json.dumps({"mode": mode, "candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")

    local_results = []
    for item in sorted(candidates, key=lambda row: row["full_fast_duration_s"], reverse=True)[:2]:
        refined = optimize_local(
            lambda x: full_union_objective(x, "FAST"),
            item["x"],
            bounds=joint_bounds(),
            method="Nelder-Mead",
            direction="maximize",
            options={"maxiter": 800, "xatol": 1e-5, "fatol": 1e-6},
        )
        local_results.append(refined)
    successful = [result for result in local_results if result.success]
    if not successful:
        raise RuntimeError("Q3 joint local refinement produced no converged result")
    accepted = max(successful, key=lambda result: full_union_objective(result.x, "FINAL"))
    strategies = variables_to_strategies(accepted.x)
    precision = {level: strategy_results(strategies, model="full", precision=level) for level in ("FAST", "STANDARD", "FINAL")}
    final_results, final_union, final_duration = precision["FINAL"]
    gains = marginal_interval_gains([result.intervals_s for result in final_results])
    margins = [strategies[1].drop_time_s - strategies[0].drop_time_s - 1.0, strategies[2].drop_time_s - strategies[1].drop_time_s - 1.0]
    report = (
        ValidationReport()
        .add("Q3 optimizer success", accepted.success, accepted.message)
        .add("Q3 shared heading/speed", len({round(s.heading_rad, 12) for s in strategies}) == 1 and len({round(s.speed_m_s, 9) for s in strategies}) == 1)
        .add("Q3 drop gaps", validate_drop_gaps(strategies), f"extra margins={margins}")
        .add("Q3 burst heights", check_constraints([result.burst_point_m[2] for result in final_results], sense="ge"))
        .add("Q3 interval union", abs(sum(gains) - final_duration) <= 1e-8, f"gains={gains}")
        .add("Q3 root residuals", max(result.root_residual_max_m2 for result in final_results) <= 1e-5)
        .add("Q3 surface convergence", abs(precision["FINAL"][2] - precision["STANDARD"][2]) <= 1e-4)
        .add("Q3 multiple seeds", len(profile["seeds"]) >= 3 if mode != "FAST" else True)
        .add("Q3 global optimality", manual=True, detail="best feasible multi-seed result; global optimum not proven")
        .add("Model interpretation", manual=True, detail="MODEL_CONFIRMATION_REQUIRED")
    )
    return {"mode": mode, "strategies": strategies, "results": final_results, "union": final_union, "duration_s": final_duration, "gains": gains, "accepted": accepted, "candidates": candidates, "precision": precision, "validation": report, "elapsed_s": perf_counter() - started}


def export_result1(solution):
    values = {}
    for row, (strategy, result) in enumerate(zip(solution["strategies"], solution["results"]), start=2):
        drop = drop_point(strategy)
        burst = result.burst_point_m
        row_values = [strategy.heading_deg, strategy.speed_m_s, strategy.bomb_no, *drop, *burst, result.duration_s]
        for column, value in zip("ABCDEFGHIJ", row_values):
            values[f"{column}{row}"] = round(float(value), 6) if isinstance(value, (float, np.floating)) else int(value)
    return fill_excel_template(TEMPLATE, RESULTS / "result1.xlsx", "Sheet1", values)


def write_outputs(solution):
    RESULTS.mkdir(parents=True, exist_ok=True)
    export_result1(solution)
    rows = []
    for strategy, result, gain in zip(solution["strategies"], solution["results"], solution["gains"]):
        rows.append({"bomb_no": strategy.bomb_no, "heading_deg": strategy.heading_deg, "speed_m_s": strategy.speed_m_s, "drop_time_s": strategy.drop_time_s, "delay_s": strategy.delay_s, "burst_time_s": strategy.burst_time_s, "own_duration_s": result.duration_s, "marginal_duration_s": gain, "intervals_s": str(result.intervals_s)})
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "q3_strategy.csv", index=False)
    (RESULTS / "q3_validation.txt").write_text(solution["validation"].render(), encoding="utf-8")
    (RESULTS / "q3_result.json").write_text(json.dumps({"union_intervals_s": solution["union"], "union_duration_s": solution["duration_s"], "elapsed_s": solution["elapsed_s"], "strategies": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    figure_dir = RESULTS / "figures"; origin_dir = RESULTS / "origin_data"
    figure_dir.mkdir(parents=True, exist_ok=True); origin_dir.mkdir(parents=True, exist_ok=True)
    use_paper_style(); fig, ax = plt.subplots(figsize=(6.0, 2.8))
    for index, result in enumerate(solution["results"], start=1):
        for left, right in result.intervals_s:
            ax.barh(index, right - left, left=left, height=0.55, color=COLORS[(index - 1) % len(COLORS)], label=f"Bomb {index}")
    ax.set(yticks=[1, 2, 3], yticklabels=["Bomb 1", "Bomb 2", "Bomb 3"], xlabel="Time after detection (s)", title="Q3 continuous interval chaining")
    ax.grid(True, axis="x", color="#D9D9D9", linewidth=0.5); fig.tight_layout(); save_figure(fig, figure_dir / "q3_intervals"); plt.close(fig)
    export_origin_table(origin_dir / "q3_strategy.xlsx", frame.drop(columns="intervals_s"), x_column="bomb_no", metadata={"purpose": "Q3 per-bomb strategy and marginal coverage", "union_duration_s": str(solution["duration_s"])})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=tuple(PROFILES), default="FINAL"); parser.add_argument("--no-cache", action="store_true"); args = parser.parse_args()
    solution = optimize_q3(args.mode, use_cache=not args.no_cache)
    write_outputs(solution)
    print(f"Q3 union duration={solution['duration_s']:.9f} s; intervals={solution['union']}")
    print(solution["validation"].render())


if __name__ == "__main__":
    main()
