"""Export every adjacent-handle distance error for the 2024A benchmark."""

from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from common import LINK_LENGTHS_M, ArchimedeanSpiral, TURN_RADIUS_M, TurnaroundPath, build_path_chain, build_spiral_chain
from deliverables import RESULT_DIR


def time_series_frame(errors):
    errors = np.asarray(errors, float)
    return pd.DataFrame({
        "link_index": np.arange(1, len(LINK_LENGTHS_M) + 1),
        "target_length_m": LINK_LENGTHS_M,
        "maximum_error_m": np.max(errors, axis=0),
        "mean_error_m": np.mean(errors, axis=0),
        "p95_error_m": np.percentile(errors, 95, axis=0),
    })


def state_frame(positions):
    errors = np.abs(np.linalg.norm(np.diff(np.asarray(positions, float), axis=0), axis=1) - LINK_LENGTHS_M)
    return pd.DataFrame({
        "link_index": np.arange(1, len(LINK_LENGTHS_M) + 1),
        "target_length_m": LINK_LENGTHS_M,
        "error_m": errors,
    })


def summarize(frame, raw_errors):
    raw_errors = np.asarray(raw_errors, float)
    values = np.mean(raw_errors, axis=0) if raw_errors.ndim == 2 else raw_errors
    index = frame["link_index"].to_numpy(float)
    return {
        "maximum_m": float(np.max(raw_errors)), "mean_m": float(np.mean(raw_errors)),
        "p95_m": float(np.percentile(raw_errors, 95)),
        "index_error_correlation": float(np.corrcoef(index, values)[0, 1]),
        "first_decile_mean_m": float(np.mean(values[:23])),
        "last_decile_mean_m": float(np.mean(values[-23:])),
    }


def main():
    q1 = np.load(RESULT_DIR / "raw" / "q1.npz")
    q4 = np.load(RESULT_DIR / "raw" / "q4.npz")
    q2_metrics = json.loads((RESULT_DIR / "q2_metrics.json").read_text(encoding="utf-8"))
    q3_metrics = json.loads((RESULT_DIR / "q3_metrics.json").read_text(encoding="utf-8"))
    q5_metrics = json.loads((RESULT_DIR / "q5_metrics.json").read_text(encoding="utf-8"))

    q2_state = build_spiral_chain(
        ArchimedeanSpiral(0.55).theta_from_arc(
            ArchimedeanSpiral(0.55).arc_primitive(32.0 * np.pi) - q2_metrics["event_time_s"],
            upper_hint=32.0 * np.pi,
        )[0]
    )
    q3_state = build_spiral_chain(q3_metrics["critical_theta_head_rad"], pitch_m=q3_metrics["critical_pitch_m"])
    path = TurnaroundPath()
    q5_state = build_path_chain(path, q5_metrics["critical_head_path_coordinate_m"], head_speed_m_s=q5_metrics["maximum_head_speed_m_s"])

    error_arrays = {
        "Q1 all times": q1["link_errors"],
        "Q2 event": np.abs(np.linalg.norm(np.diff(q2_state.positions, axis=0), axis=1) - LINK_LENGTHS_M),
        "Q3 critical": np.abs(np.linalg.norm(np.diff(q3_state.positions, axis=0), axis=1) - LINK_LENGTHS_M),
        "Q4 all times": q4["link_errors"],
        "Q5 limiting": np.abs(np.linalg.norm(np.diff(q5_state.positions, axis=0), axis=1) - LINK_LENGTHS_M),
    }
    frames = {
        name: time_series_frame(errors) if np.asarray(errors).ndim == 2 else state_frame(
            {"Q2 event": q2_state, "Q3 critical": q3_state, "Q5 limiting": q5_state}[name].positions
        )
        for name, errors in error_arrays.items()
    }
    verification = write_excel_checked(RESULT_DIR / "chain_error_by_link.xlsx", frames, decimals=15)
    metrics = {name: summarize(frame, error_arrays[name]) for name, frame in frames.items()}
    metrics["excel"] = verification
    (RESULT_DIR / "chain_error_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
