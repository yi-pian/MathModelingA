"""Focused 2023A timing and memory baselines."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.performance import benchmark
from field import evaluate_time
from problem_data import RESULT_DIR, load_q1_design
from solar import direct_normal_irradiance, solar_position


def run():
    design = load_q1_design()
    altitude, _, sun = solar_position(0, 12.0)
    dni = float(direct_normal_irradiance(altitude))
    levels = {}
    for level in ("FAST", "STANDARD", "FINAL"):
        result = evaluate_time(design, sun, dni, precision=level)
        levels[level] = {
            "summary": result.summary(design.areas),
            "stage_seconds": result.timings_s,
            "candidate_stats": result.candidate_stats.__dict__,
        }
    repeat = benchmark(evaluate_time, design, sun, dni, precision="FAST", repeats=3, warmup=1)
    estimated_static_bytes = design.centers.nbytes + design.widths.nbytes + design.heights.nbytes
    report = {"levels": levels, "fast_repeat": repeat, "static_array_bytes": estimated_static_bytes}
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "performance_2023a.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    run()
