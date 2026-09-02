"""Q4 one bomb from each of FY1/FY2/FY3 against M1."""

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
from core.optimization import optimize_global, optimize_local, optimize_scalar
from core.plotting import COLORS, save_figure, use_paper_style
from core.validation import ValidationReport, check_bounds, check_constraints
import matplotlib.pyplot as plt

from common import Strategy, drop_point, event_value_m2, feasible_active_window, interval_duration, merge_intervals, missile_arrival_time, obscuration_intervals, target_surface_points
from problem_data import GRAVITY_M_S2, UAV_INITIAL_M

RESULTS = ROOT / "results" / "2025A"
TEMPLATE = ROOT / "data" / "2025A" / "official" / "templates" / "result2.xlsx"
UAVS = ("FY1", "FY2", "FY3")
PROFILES = {
    "FAST": {"seeds": [0], "popsize": 7, "iterations": 30},
    "STANDARD": {"seeds": [0, 1, 2], "popsize": 8, "iterations": 50},
    "FINAL": {"seeds": [0, 1, 2], "popsize": 10, "iterations": 70},
}


def bounds_for(uav):
    max_delay = float(np.sqrt(2.0 * UAV_INITIAL_M[uav][2] / GRAVITY_M_S2))
    return np.array([(0.0, 2.0 * np.pi), (70.0, 140.0), (0.0, missile_arrival_time("M1")), (0.0, max_delay)], dtype=float)


def to_strategy(uav, values):
    heading, speed, burst_time, delay = map(float, values)
    if delay > burst_time:
        return None
    try:
        return Strategy(uav, "M1", heading, speed, burst_time - delay, delay)
    except ValueError:
        return None


def duration(uav, values, precision="FAST"):
    strategy = to_strategy(uav, values)
    if strategy is None:
        return -1e6
    return obscuration_intervals(strategy, model="full", precision=precision).duration_s


def guided(uav, values):
    strategy = to_strategy(uav, values)
    if strategy is None:
        return -1e12
    window = feasible_active_window(strategy)
    if window is None:
        return -1e12
    result = obscuration_intervals(strategy, model="full", precision="FAST")
    if result.duration_s > 0:
        return 1e6 + result.duration_s
    points = target_surface_points("FAST")
    return -min(event_value_m2(strategy, time_s, model="full", surface_points=points) for time_s in np.linspace(*window, 21))


def coordinate_polish(uav, start):
    """Successful bounded 1-D searches with monotone acceptance certify the final point."""
    x = np.asarray(start, dtype=float).copy()
    bounds = bounds_for(uav)
    successes = []
    for steps in ([0.08, 8.0, 0.8, 0.8], [0.02, 2.0, 0.2, 0.2], [0.005, 0.5, 0.05, 0.05]):
        for index, step in enumerate(steps):
            baseline = duration(uav, x, "FAST")
            low = max(bounds[index, 0], x[index] - step)
            high = min(bounds[index, 1], x[index] + step)

            def objective(value):
                candidate = x.copy(); candidate[index] = value
                return duration(uav, candidate, "FAST")

            result = optimize_scalar(objective, bounds=(low, high), direction="maximize", options={"xatol": 1e-7})
            successes.append(result.success)
            candidate = x.copy(); candidate[index] = result.x
            if duration(uav, candidate, "FAST") >= baseline:
                x = candidate
    return x, all(successes)


def optimize_uav(uav, profile, *, cached_candidates=None):
    candidates = [] if cached_candidates is None else cached_candidates
    if not candidates:
        for seed in profile["seeds"]:
            result = optimize_global(
                lambda x: guided(uav, x),
                bounds_for(uav),
                direction="maximize",
                seed=seed,
                popsize=profile["popsize"],
                maxiter=profile["iterations"],
                tol=1e-7,
                polish=False,
            )
            candidates.append({"seed": seed, "success": result.success, "message": result.message, "x": np.asarray(result.x).tolist(), "duration_fast_s": duration(uav, result.x, "FAST")})
    best = max(candidates, key=lambda item: item["duration_fast_s"])
    local = optimize_local(
        lambda x: duration(uav, x, "FAST"),
        best["x"],
        bounds=bounds_for(uav),
        method="Nelder-Mead",
        direction="maximize",
        options={"maxiter": 600, "xatol": 1e-5, "fatol": 1e-7},
    )
    polished, polish_success = coordinate_polish(uav, local.x)
    if not polish_success:
        raise RuntimeError(f"Q4 {uav} coordinate polish failed")
    return polished, candidates, local


def optimize_q4(mode="FINAL", *, use_cache=True):
    profile = PROFILES[mode]
    cache_dir = RESULTS / "cache" / mode; cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "q4_search.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if use_cache and cache_path.exists() else {}
    started = perf_counter(); variables = {}; searches = {}; locals_ = {}

    q2_path = RESULTS / "q2_result.json"
    if q2_path.exists():
        q2 = json.loads(q2_path.read_text(encoding="utf-8"))
        variables["FY1"] = np.array([q2["heading_rad"], q2["speed_m_s"], q2["burst_time_s"], q2["delay_s"]])
        searches["FY1"] = [{"seed": "validated Q2", "success": True, "message": "Q2 accepted solution", "x": variables["FY1"].tolist(), "duration_fast_s": duration("FY1", variables["FY1"], "FAST")}]
        locals_["FY1"] = None
    else:
        variables["FY1"], searches["FY1"], locals_["FY1"] = optimize_uav("FY1", profile, cached_candidates=cache.get("FY1"))
    for uav in ("FY2", "FY3"):
        variables[uav], searches[uav], locals_[uav] = optimize_uav(uav, profile, cached_candidates=cache.get(uav))
    cache_path.write_text(json.dumps({uav: searches[uav] for uav in UAVS}, ensure_ascii=False, indent=2), encoding="utf-8")

    strategies = [to_strategy(uav, variables[uav]) for uav in UAVS]
    results = [obscuration_intervals(strategy, model="full", precision="FINAL") for strategy in strategies]
    groups = [result.intervals_s for result in results]
    union = merge_intervals([interval for group in groups for interval in group])
    total = interval_duration(union)
    standard_total = interval_duration([interval for strategy in strategies for interval in obscuration_intervals(strategy, model="full", precision="STANDARD").intervals_s])
    margins = []
    for uav, strategy, result in zip(UAVS, strategies, results):
        bounds = bounds_for(uav)
        x = variables[uav]
        margins.extend([x[1] - 70.0, 140.0 - x[1], strategy.drop_time_s, strategy.delay_s, result.burst_point_m[2], missile_arrival_time("M1") - strategy.burst_time_s])
    report = (
        ValidationReport()
        .add("Q4 finite strategies", np.all(np.isfinite(np.concatenate(list(variables.values())))))
        .add("Q4 variable bounds", all(check_bounds(variables[uav], bounds_for(uav)[:, 0], bounds_for(uav)[:, 1]) for uav in UAVS))
        .add("Q4 physical constraints", check_constraints(margins, sense="ge"))
        .add("Q4 interval union", total <= sum(result.duration_s for result in results) + 1e-9, f"union={total:.9f}, sum={sum(r.duration_s for r in results):.9f}")
        .add("Q4 root residuals", max(result.root_residual_max_m2 for result in results) <= 1e-5)
        .add("Q4 surface convergence", abs(total - standard_total) <= 1e-2, f"difference={abs(total-standard_total):.3e} s")
        .add("Q4 multiple seeds", len(profile["seeds"]) >= 3 if mode != "FAST" else True)
        .add("Q4 global optimality", manual=True, detail="independent candidates plus coordinate polish; global optimum not proven")
        .add("Model interpretation", manual=True, detail="MODEL_CONFIRMATION_REQUIRED")
    )
    return {"mode": mode, "variables": variables, "strategies": strategies, "results": results, "union": union, "duration_s": total, "searches": searches, "locals": locals_, "validation": report, "elapsed_s": perf_counter() - started}


def export_result2(solution):
    values = {}
    for row, (strategy, result) in enumerate(zip(solution["strategies"], solution["results"]), start=2):
        point = drop_point(strategy); burst = result.burst_point_m
        for column, value in zip("ABCDEFGHIJ", [strategy.uav, strategy.heading_deg, strategy.speed_m_s, *point, *burst, result.duration_s]):
            values[f"{column}{row}"] = round(float(value), 6) if isinstance(value, (float, np.floating)) else value
    return fill_excel_template(TEMPLATE, RESULTS / "result2.xlsx", "Sheet1", values)


def write_outputs(solution):
    export_result2(solution)
    rows = []
    for strategy, result in zip(solution["strategies"], solution["results"]):
        rows.append({"uav": strategy.uav, "heading_deg": strategy.heading_deg, "speed_m_s": strategy.speed_m_s, "drop_time_s": strategy.drop_time_s, "delay_s": strategy.delay_s, "burst_time_s": strategy.burst_time_s, "duration_s": result.duration_s, "intervals_s": str(result.intervals_s)})
    frame = pd.DataFrame(rows); frame.to_csv(RESULTS / "q4_strategy.csv", index=False)
    (RESULTS / "q4_result.json").write_text(json.dumps({"union_intervals_s": solution["union"], "union_duration_s": solution["duration_s"], "elapsed_s": solution["elapsed_s"], "strategies": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS / "q4_validation.txt").write_text(solution["validation"].render(), encoding="utf-8")
    figure_dir = RESULTS / "figures"; origin_dir = RESULTS / "origin_data"; figure_dir.mkdir(parents=True, exist_ok=True); origin_dir.mkdir(parents=True, exist_ok=True)
    use_paper_style(); fig, ax = plt.subplots(figsize=(6.0, 2.8))
    for index, (uav, result) in enumerate(zip(UAVS, solution["results"]), start=1):
        for left, right in result.intervals_s:
            ax.barh(index, right-left, left=left, height=.55, color=COLORS[index-1], label=uav)
    ax.set(yticks=[1,2,3], yticklabels=UAVS, xlabel="Time after detection (s)", title="Q4 three-UAV obscuration intervals"); ax.grid(True, axis="x", color="#D9D9D9", linewidth=.5); fig.tight_layout(); save_figure(fig, figure_dir / "q4_intervals"); plt.close(fig)
    export_origin_table(origin_dir / "q4_strategy.xlsx", frame.drop(columns="intervals_s"), x_column="uav", metadata={"purpose": "Q4 strategy and interval duration", "union_duration_s": str(solution["duration_s"])})


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--mode",choices=tuple(PROFILES),default="FINAL"); parser.add_argument("--no-cache",action="store_true"); args=parser.parse_args()
    solution=optimize_q4(args.mode,use_cache=not args.no_cache); write_outputs(solution)
    print(f"Q4 union duration={solution['duration_s']:.9f} s; intervals={solution['union']}"); print(solution["validation"].render())


if __name__ == "__main__": main()
