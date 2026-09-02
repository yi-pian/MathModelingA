"""Question 2 and reusable one-dimensional critical-thickness search."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from time import perf_counter
from typing import Callable

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.roots import RootResult, solve_bracketed
from core.units import mm_to_m

from common import SimulationResult, make_system, safety_metrics, simulate


@dataclass(frozen=True)
class CriticalThicknessResult:
    d_ii_m: float
    critical_d_ii_m: float
    simulation: SimulationResult
    metrics: dict
    active_constraint: str
    root_47: RootResult | None
    root_duration: RootResult | None
    coarse_scan: pd.DataFrame
    elapsed_seconds: float
    evaluations: int


def _bracket_from_scan(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    if y[0] >= 0:
        return float(x[0]), float(x[0])
    indices = np.flatnonzero((y[:-1] < 0) & (y[1:] >= 0))
    return None if not len(indices) else (float(x[indices[0]]), float(x[indices[0] + 1]))


def find_critical_layer_ii(
    *,
    environment_temperature_c: float,
    final_time_s: float,
    d_iv_m: float,
    h_out_w_m2k: float,
    h_skin_w_m2k: float,
    target_dx_m: float = 1.0e-4,
    dt_s: float = 1.0,
    coarse_points: int = 9,
    search_bounds_m: tuple[float, float] = (0.0006, 0.025),
    report_increment_m: float = 0.0001,
) -> CriticalThicknessResult:
    """Find the smallest layer-II thickness satisfying both safety constraints."""
    started = perf_counter()
    cache: dict[float, tuple[SimulationResult, dict]] = {}

    def evaluate(d_ii_m: float) -> tuple[SimulationResult, dict]:
        key = float(d_ii_m)
        if key not in cache:
            system = make_system(
                environment_temperature_c,
                h_out_w_m2k,
                h_skin_w_m2k,
                d_ii_m=key,
                d_iv_m=d_iv_m,
                target_dx_m=target_dx_m,
            )
            result = simulate(system, final_time_s, dt_s=dt_s)
            cache[key] = (result, safety_metrics(result))
        return cache[key]

    coarse_x = np.linspace(search_bounds_m[0], search_bounds_m[1], coarse_points)
    coarse_metrics = [evaluate(value)[1] for value in coarse_x]
    margin_47 = np.asarray([row["margin_47_c"] for row in coarse_metrics], float)
    margin_duration = np.asarray([row["margin_duration_s"] for row in coarse_metrics], float)
    coarse = pd.DataFrame(
        {
            "d_ii_mm": coarse_x * 1000.0,
            "max_skin_temperature_c": [row["max_skin_temperature_c"] for row in coarse_metrics],
            "duration_above_44_s": [row["duration_above_44_s"] for row in coarse_metrics],
            "margin_47_c": margin_47,
            "margin_duration_s": margin_duration,
        }
    )

    def solve_margin(values: np.ndarray, margin: Callable[[dict], float]) -> RootResult | None:
        bracket = _bracket_from_scan(coarse_x, values)
        if bracket is None:
            return None
        if bracket[0] == bracket[1]:
            return RootResult(bracket[0], abs(float(margin(evaluate(bracket[0])[1]))), True, 0, "lower bound feasible")
        return solve_bracketed(lambda thickness: margin(evaluate(thickness)[1]), bracket, xtol=2.0e-8, rtol=1.0e-10)

    root_47 = solve_margin(margin_47, lambda row: float(row["margin_47_c"]))
    root_duration = solve_margin(margin_duration, lambda row: float(row["margin_duration_s"]))
    if root_47 is None or root_duration is None:
        raise RuntimeError("official upper thickness bound is infeasible for at least one constraint")
    critical = max(float(root_47.root), float(root_duration.root), search_bounds_m[0])
    critical_result, critical_metrics = evaluate(critical)
    if not critical_metrics["feasible"]:
        # Brent residual and changing cell count can leave the point microscopically infeasible.
        critical = min(search_bounds_m[1], critical + max(2.0e-8, target_dx_m * 1.0e-3))
        critical_result, critical_metrics = evaluate(critical)
    recommended = min(search_bounds_m[1], np.ceil((critical - 1e-12) / report_increment_m) * report_increment_m)
    final_result, final_metrics = evaluate(recommended)
    active = "47C" if float(root_47.root) >= float(root_duration.root) else "duration_above_44"
    return CriticalThicknessResult(
        d_ii_m=float(recommended),
        critical_d_ii_m=float(critical),
        simulation=final_result,
        metrics=final_metrics,
        active_constraint=active,
        root_47=root_47,
        root_duration=root_duration,
        coarse_scan=coarse,
        elapsed_seconds=perf_counter() - started,
        evaluations=len(cache),
    )


def solve_q2(
    h_out_w_m2k: float,
    h_skin_w_m2k: float,
    *,
    target_dx_m: float = 1.0e-4,
    dt_s: float = 1.0,
) -> CriticalThicknessResult:
    return find_critical_layer_ii(
        environment_temperature_c=65.0,
        final_time_s=3600.0,
        d_iv_m=mm_to_m(5.5),
        h_out_w_m2k=h_out_w_m2k,
        h_skin_w_m2k=h_skin_w_m2k,
        target_dx_m=target_dx_m,
        dt_s=dt_s,
    )


if __name__ == "__main__":
    result = solve_q2(120.28446734458524, 8.364567662641655)
    print({"d_ii_mm": 1000 * result.d_ii_m, **result.metrics, "active": result.active_constraint, "evaluations": result.evaluations, "elapsed_seconds": result.elapsed_seconds})
