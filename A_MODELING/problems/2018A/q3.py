"""Question 3: minimum total thickness using a coarse-to-fine boundary search."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.optimization import optimize_scalar
from core.units import mm_to_m

from q2 import CriticalThicknessResult, find_critical_layer_ii


@dataclass(frozen=True)
class Q3Result:
    d_ii_m: float
    d_iv_m: float
    total_thickness_m: float
    critical_result: CriticalThicknessResult
    coarse_scan: pd.DataFrame
    neighbor_scan: pd.DataFrame
    elapsed_seconds: float
    outer_evaluations: int
    optimizer_message: str


def solve_q3(
    h_out_w_m2k: float,
    h_skin_w_m2k: float,
    *,
    target_dx_m: float = 1.0e-4,
    dt_s: float = 1.0,
    coarse_points: int = 11,
) -> Q3Result:
    started = perf_counter()
    lower_iv, upper_iv = mm_to_m(0.6), mm_to_m(6.4)
    cache: dict[float, CriticalThicknessResult | None] = {}

    def critical(d_iv_m: float) -> CriticalThicknessResult | None:
        key = float(d_iv_m)
        if key not in cache:
            try:
                cache[key] = find_critical_layer_ii(
                    environment_temperature_c=80.0,
                    final_time_s=1800.0,
                    d_iv_m=key,
                    h_out_w_m2k=h_out_w_m2k,
                    h_skin_w_m2k=h_skin_w_m2k,
                    target_dx_m=target_dx_m,
                    dt_s=dt_s,
                    coarse_points=8,
                )
            except RuntimeError:
                cache[key] = None
        return cache[key]

    def objective(d_iv_m: float) -> float:
        candidate = critical(float(d_iv_m))
        return 1.0 if candidate is None else float(d_iv_m + candidate.critical_d_ii_m)

    coarse_iv = np.linspace(lower_iv, upper_iv, coarse_points)
    coarse_results = [critical(value) for value in coarse_iv]
    totals = np.asarray([np.inf if result is None else value + result.critical_d_ii_m for value, result in zip(coarse_iv, coarse_results)])
    if not np.isfinite(totals).any():
        raise RuntimeError("no feasible Q3 design within official thickness bounds")
    best_index = int(np.argmin(totals))
    optimizer_message = "coarse minimum at official boundary"
    if best_index == 0 or best_index == len(coarse_iv) - 1:
        best_iv = float(coarse_iv[best_index])
    else:
        refined = optimize_scalar(
            objective,
            bounds=(float(coarse_iv[best_index - 1]), float(coarse_iv[best_index + 1])),
            direction="minimize",
            method="bounded",
            options={"xatol": 2.0e-7},
        )
        if not refined.success:
            raise RuntimeError(refined.message)
        best_iv = float(refined.x)
        optimizer_message = refined.message
    best = critical(best_iv)
    if best is None:
        raise RuntimeError("refined Q3 candidate is infeasible")

    neighbor_values = np.unique(np.clip(best_iv + np.array([-2e-4, -1e-4, 0.0, 1e-4, 2e-4]), lower_iv, upper_iv))
    neighbor_results = [critical(value) for value in neighbor_values]
    neighbor = pd.DataFrame(
        {
            "d_iv_mm": neighbor_values * 1000.0,
            "d_ii_mm": [np.nan if result is None else result.d_ii_m * 1000.0 for result in neighbor_results],
            "critical_d_ii_mm": [np.nan if result is None else result.critical_d_ii_m * 1000.0 for result in neighbor_results],
            "total_mm": [np.nan if result is None else (value + result.d_ii_m) * 1000.0 for value, result in zip(neighbor_values, neighbor_results)],
            "max_skin_temperature_c": [np.nan if result is None else result.metrics["max_skin_temperature_c"] for result in neighbor_results],
            "duration_above_44_s": [np.nan if result is None else result.metrics["duration_above_44_s"] for result in neighbor_results],
        }
    )
    coarse = pd.DataFrame(
        {
            "d_iv_mm": coarse_iv * 1000.0,
            "critical_d_ii_mm": [np.nan if result is None else result.critical_d_ii_m * 1000.0 for result in coarse_results],
            "total_mm": totals * 1000.0,
            "active_constraint": ["infeasible" if result is None else result.active_constraint for result in coarse_results],
        }
    )
    return Q3Result(
        d_ii_m=best.d_ii_m,
        d_iv_m=best_iv,
        total_thickness_m=best.d_ii_m + best_iv,
        critical_result=best,
        coarse_scan=coarse,
        neighbor_scan=neighbor,
        elapsed_seconds=perf_counter() - started,
        outer_evaluations=len(cache),
        optimizer_message=optimizer_message,
    )


if __name__ == "__main__":
    result = solve_q3(120.28446734458524, 8.364567662641655)
    print(
        {
            "d_ii_mm": result.d_ii_m * 1000.0,
            "d_iv_mm": result.d_iv_m * 1000.0,
            "total_mm": result.total_thickness_m * 1000.0,
            **result.critical_result.metrics,
            "outer_evaluations": result.outer_evaluations,
            "elapsed_seconds": result.elapsed_seconds,
        }
    )
