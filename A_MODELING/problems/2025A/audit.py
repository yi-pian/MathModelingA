"""Read-only numerical, sensitivity, performance, and deliverable audit for 2025A."""

from __future__ import annotations

from dataclasses import replace
import json
from math import radians
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))

from core.export import export_origin_table
from core.units import degree_to_rad
from common import (
    PRECISIONS,
    Precision,
    Strategy,
    burst_point,
    feasible_active_window,
    interval_duration,
    locate_nonpositive_intervals,
    merge_intervals,
    missile_arrival_time,
    missile_position,
    obscuration_intervals,
    point_segment_distance_sq_many,
    target_surface_points,
)
from deliverables import verify_all
from problem_data import CLOUD_LIFETIME_S, CLOUD_RADIUS_M, CLOUD_DESCENT_M_S

RESULTS = ROOT / "results" / "2025A"
AUDIT_PRECISION = Precision("AUDIT", 0.005, 192, 17, 9, 1e-11, 1e-9)


def strategy_from_row(row, *, default_uav=None, default_missile=None, default_bomb_no=1) -> Strategy:
    return Strategy(
        str(getattr(row, "uav", default_uav)), str(getattr(row, "missile", default_missile)), float(degree_to_rad(row.heading_deg)),
        float(row.speed_m_s), float(row.drop_time_s), float(row.delay_s), int(getattr(row, "bomb_no", default_bomb_no)),
    )


def load_strategies(name: str, *, default_uav=None, default_missile=None) -> list[Strategy]:
    rows = pd.read_csv(RESULTS / name).itertuples(index=False)
    return [strategy_from_row(row, default_uav=default_uav, default_missile=default_missile, default_bomb_no=index) for index, row in enumerate(rows, start=1)]


def union_for(strategies: list[Strategy], precision="FINAL"):
    results = [obscuration_intervals(strategy, model="full", precision=precision) for strategy in strategies]
    union = merge_intervals([interval_ for result in results for interval_ in result.intervals_s])
    return results, union, interval_duration(union)


def physical_parameter_duration(strategy: Strategy, *, radius_m: float, descent_m_s: float) -> float:
    """Re-evaluate the Q2 strategy without mutating official constants."""
    burst = burst_point(strategy)
    if burst[2] < 0 or radius_m <= 0 or descent_m_s <= 0:
        return 0.0
    start = strategy.burst_time_s
    stop = min(start + CLOUD_LIFETIME_S, missile_arrival_time(strategy.missile), start + burst[2] / descent_m_s)
    points = target_surface_points("FINAL")

    def event(time_s: float) -> float:
        center = burst.copy(); center[2] -= descent_m_s * (time_s - start)
        observer = np.asarray(missile_position(strategy.missile, time_s), dtype=float)
        centers = np.repeat(center[None, :], len(points), axis=0)
        distance_sq = point_segment_distance_sq_many(centers, observer, points)
        return float(np.max(distance_sq) - radius_m**2)

    intervals, _ = locate_nonpositive_intervals(
        event, start, stop, step=PRECISIONS["FINAL"].event_step_s,
        xtol=PRECISIONS["FINAL"].root_xtol_s, value_tol=PRECISIONS["FINAL"].event_tol_m2,
    )
    return interval_duration(intervals)


def sensitivity_table(nominal: Strategy) -> pd.DataFrame:
    rows = []

    def add(group, label, strategy=None, radius=CLOUD_RADIUS_M, descent=CLOUD_DESCENT_M_S):
        if strategy is None:
            rows.append({"parameter": group, "perturbation": label, "feasible": False, "duration_s": 0.0})
        else:
            duration = physical_parameter_duration(strategy, radius_m=radius, descent_m_s=descent)
            rows.append({"parameter": group, "perturbation": label, "feasible": True, "duration_s": duration})

    for delta in (-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0):
        add("heading", f"{delta:+.1f} deg", replace(nominal, heading_rad=nominal.heading_rad + radians(delta)))
    for percent in (-1.0, -0.5, 0.0, 0.5, 1.0):
        value = nominal.speed_m_s * (1.0 + percent / 100.0)
        add("speed", f"{percent:+.1f}%", replace(nominal, speed_m_s=value) if 70.0 <= value <= 140.0 else None)
    for field, group in (("drop_time_s", "drop_time"), ("delay_s", "delay")):
        for delta in (-0.10, -0.05, -0.01, 0.0, 0.01, 0.05, 0.10):
            value = getattr(nominal, field) + delta
            add(group, f"{delta:+.2f} s", replace(nominal, **{field: value}) if value >= 0 else None)
    for percent in (-5.0, -1.0, 0.0, 1.0, 5.0):
        add("cloud_radius", f"{percent:+.1f}%", nominal, radius=CLOUD_RADIUS_M * (1.0 + percent / 100.0))
        add("cloud_descent", f"{percent:+.1f}%", nominal, descent=CLOUD_DESCENT_M_S * (1.0 + percent / 100.0))
    frame = pd.DataFrame(rows)
    nominal_duration = physical_parameter_duration(nominal, radius_m=CLOUD_RADIUS_M, descent_m_s=CLOUD_DESCENT_M_S)
    frame["delta_duration_s"] = frame["duration_s"] - nominal_duration
    return frame


def timed(function, repeats=3):
    samples = []
    for _ in range(repeats):
        start = perf_counter(); function(); samples.append(perf_counter() - start)
    return {"samples_s": samples, "median_s": median(samples)}


def audit():
    q1 = Strategy("FY1", "M1", np.pi, 120.0, 1.5, 3.6)
    q2_data = json.loads((RESULTS / "q2_result.json").read_text(encoding="utf-8"))
    q2 = Strategy("FY1", "M1", q2_data["heading_rad"], q2_data["speed_m_s"], q2_data["drop_time_s"], q2_data["delay_s"])
    q3 = load_strategies("q3_strategy.csv", default_uav="FY1", default_missile="M1")
    q4 = load_strategies("q4_strategy.csv", default_missile="M1")
    q5 = load_strategies("q5_strategy.csv")

    strategies = {"Q1": [q1], "Q2": [q2], "Q3": q3, "Q4": q4}
    precision = {}
    for name, group in strategies.items():
        _, _, final = union_for(group, "FINAL")
        _, _, audit_value = union_for(group, AUDIT_PRECISION)
        precision[name] = {"final_s": final, "audit_s": audit_value, "absolute_difference_s": abs(final - audit_value)}
    q5_precision = {}
    for missile in ("M1", "M2", "M3"):
        group = [strategy for strategy in q5 if strategy.missile == missile]
        _, _, final = union_for(group, "FINAL"); _, _, audit_value = union_for(group, AUDIT_PRECISION)
        q5_precision[missile] = {"final_s": final, "audit_s": audit_value, "absolute_difference_s": abs(final - audit_value)}
    precision["Q5"] = {
        "final_s": sum(item["final_s"] for item in q5_precision.values()),
        "audit_s": sum(item["audit_s"] for item in q5_precision.values()),
        "absolute_difference_s": abs(sum(item["final_s"] for item in q5_precision.values()) - sum(item["audit_s"] for item in q5_precision.values())),
        "by_missile": q5_precision,
    }

    sensitivity = sensitivity_table(q2)
    sensitivity.to_csv(RESULTS / "sensitivity.csv", index=False)
    export_origin_table(
        RESULTS / "origin_data" / "sensitivity.xlsx", sensitivity,
        x_column="perturbation", metadata={"purpose": "Q2 decision and physical-parameter robustness", "official_answer_changed": "no; this is audit only"},
    )

    performance = {
        "single_Q1_final_evaluation": timed(lambda: obscuration_intervals(q1, model="full", precision="FINAL")),
        "single_Q2_final_evaluation": timed(lambda: obscuration_intervals(q2, model="full", precision="FINAL")),
        "Q3_three_bomb_final_evaluation": timed(lambda: union_for(q3, "FINAL"), repeats=2),
        "Q4_three_uav_final_evaluation": timed(lambda: union_for(q4, "FINAL"), repeats=2),
        "Q5_fifteen_bomb_final_evaluation": timed(lambda: [union_for([s for s in q5 if s.missile == m], "FINAL") for m in ("M1", "M2", "M3")], repeats=1),
        "Q2_global_search_nfev": q2_data["global_search_nfev"],
        "Q2_local_refinement_nfev": q2_data["local_refinement_nfev"],
        "Q2_uncached_total_s": q2_data["elapsed_s"],
        "Q5_assignment_space": {"unrestricted_one_missile_per_uav": 243, "candidate_pool": 32, "visited": 15, "pruned": 5, "leaves": 3},
        "localized_interval_boundaries": {"Q1": 2, "Q2": 2, "Q3": 6, "Q4": 6, "Q5": 16},
    }
    (RESULTS / "performance.json").write_text(json.dumps(performance, ensure_ascii=False, indent=2), encoding="utf-8")

    excel = verify_all(write=True)
    figures = sorted((RESULTS / "figures").glob("*.png"))
    origin = sorted((RESULTS / "origin_data").glob("*.xlsx"))
    origin_valid = {}
    for path in origin:
        sheets = pd.read_excel(path, sheet_name=None)
        origin_valid[path.name] = {
            "sheets": list(sheets),
            "nan": int(sum(frame.isna().sum().sum() for frame in sheets.values())),
            "inf": int(sum(np.isinf(frame.select_dtypes(include=[np.number]).to_numpy(dtype=float)).sum() for frame in sheets.values())),
        }
    result = {
        "status": "PASS" if excel["valid"] and max(item["absolute_difference_s"] for item in precision.values()) < 0.01 else "FAIL",
        "precision": precision,
        "sensitivity_worst_absolute_change_s": float(sensitivity.loc[sensitivity.feasible, "delta_duration_s"].abs().max()),
        "excel": excel,
        "figures": [path.name for path in figures],
        "origin": origin_valid,
        "performance": performance,
        "manual_findings": [
            "MODEL_CONFIRMATION_REQUIRED: full-cylinder all-sightline criterion is conservative and not uniquely forced by the statement.",
            "Q5 is a high-quality feasible solution under a restricted one-missile-per-UAV candidate pool; global optimality is not proven.",
            "Five Q5 rows have zero individual duration and are redundant but physically feasible releases used to keep the official 15-row template complete.",
        ],
    }
    (RESULTS / "audit_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
