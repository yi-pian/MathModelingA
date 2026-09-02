"""Question 1: verified optical baseline for the official 1745-mirror field."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.export import write_excel_checked
from field import aggregate_monthly_and_annual, evaluate_representative_year, mirror_detail_frame
from problem_data import RESULT_DIR, load_q1_design


def run(precision="FINAL"):
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    design = load_q1_design()
    started = perf_counter()
    time_frame, _, detail = evaluate_representative_year(design, precision=precision, detail_time=(3, 12.0))
    elapsed = perf_counter() - started
    monthly, annual = aggregate_monthly_and_annual(time_frame)
    detail_frame = mirror_detail_frame(design, detail)

    time_frame.to_csv(RESULT_DIR / "q1_time_results.csv", index=False, encoding="utf-8-sig")
    monthly.to_csv(RESULT_DIR / "q1_monthly_results.csv", index=False, encoding="utf-8-sig")
    detail_frame.to_csv(RESULT_DIR / "q1_march21_noon_mirror_detail.csv", index=False, encoding="utf-8-sig")
    annual_frame = pd.DataFrame([annual])
    write_excel_checked(
        RESULT_DIR / "result1.xlsx",
        {
            "表1_月均": monthly,
            "表2_年均": annual_frame,
            "60时点": time_frame,
            "3月21日12时逐镜": detail_frame,
        },
        decimals=6,
    )
    performance = {
        "precision": precision,
        "mirror_count": len(design.centers),
        "time_count": len(time_frame),
        "total_seconds": elapsed,
        "average_time_seconds": elapsed / len(time_frame),
        "mean_stage_seconds": {
            key.removeprefix("time_").removesuffix("_s"): float(time_frame[key].mean())
            for key in time_frame.columns
            if key.startswith("time_") and key.endswith("_s")
        },
        "mean_candidates": float(time_frame["average_candidates"].mean()),
        "maximum_candidates": int(time_frame["maximum_candidates"].max()),
        "raw_pair_comparisons_per_time": int(2 * len(design.centers) * (len(design.centers) - 1)),
    }
    (RESULT_DIR / "q1_performance.json").write_text(json.dumps(performance, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULT_DIR / "q1_summary.txt").write_text(
        "Q1 2023A\n"
        + "\n".join(f"{key}: {value}" for key, value in annual.items())
        + f"\nprecision: {precision}\nelapsed_s: {elapsed:.6f}\n",
        encoding="utf-8",
    )
    print(json.dumps({"annual": annual, "performance": performance}, ensure_ascii=False, indent=2))
    return time_frame, monthly, annual, detail_frame, performance


if __name__ == "__main__":
    run()

