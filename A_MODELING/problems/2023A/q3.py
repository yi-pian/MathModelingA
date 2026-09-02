"""Question 3: four-zone variable-size and variable-height field design."""

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

from core.export import fill_excel_template, write_excel_checked
from field import aggregate_monthly_and_annual
from layout import apply_radial_zones, constraint_report, generate_hexagonal_layout
from problem_data import OFFICIAL_DIR, RESULT_DIR
from q2 import screen_design
from q2 import extend_template_row_styles


ZONE_FRACTIONS = (0.25, 0.50, 0.75)
FINAL_DIMS = (6.54, 6.48, 6.42, 6.36)


def base_design():
    return generate_hexagonal_layout([0.0, 50.0], 6.5, 6.5, 3.3, spacing_gap=0.05)


def construct(zone_dimensions):
    dimensions = np.asarray(zone_dimensions, float)
    installation = dimensions / 2.0 + 0.05
    return apply_radial_zones(base_design(), ZONE_FRACTIONS, dimensions, dimensions, installation)


def candidate_dimensions():
    return [
        (6.50, 6.50, 6.50, 6.50),
        (6.54, 6.54, 6.50, 6.44),
        (6.54, 6.52, 6.48, 6.44),
        (6.54, 6.54, 6.48, 6.42),
        (6.54, 6.50, 6.46, 6.42),
        (6.54, 6.48, 6.42, 6.36),
        (6.54, 6.46, 6.38, 6.30),
        (6.54, 6.44, 6.34, 6.24),
        (6.54, 6.42, 6.30, 6.18),
    ]


def write_official_result(design, path):
    values = {}
    for row, index in enumerate(range(len(design.centers)), start=2):
        values.update(
            {
                f"A{row}": float(design.tower_xy[0]),
                f"B{row}": float(design.tower_xy[1]),
                f"C{row}": index + 1,
                f"D{row}": float(design.widths[index]),
                f"E{row}": float(design.heights[index]),
                f"F{row}": float(design.centers[index, 0]),
                f"G{row}": float(design.centers[index, 1]),
                f"H{row}": float(design.centers[index, 2]),
            }
        )
    fill_excel_template(OFFICIAL_DIR / "result3.xlsx", path, "Sheet1", values)
    extend_template_row_styles(path, "Sheet1", template_row=7, final_row=len(design.centers) + 1)
    frame = pd.read_excel(path)
    if frame.shape != (len(design.centers), 8) or frame.iloc[:, 2].tolist() != list(range(1, len(design.centers) + 1)):
        raise RuntimeError("result3.xlsx row count or mirror ordering failed verification")
    numeric = frame.to_numpy(float)
    if np.any(~np.isfinite(numeric)):
        raise RuntimeError("result3.xlsx contains NaN/Inf in mirror data")
    expected = np.column_stack((design.widths, design.heights, design.centers))
    if not np.allclose(numeric[:, 3:], expected, rtol=0.0, atol=1e-12):
        raise RuntimeError("result3.xlsx values differ from FINAL design arrays")
    return {"shape": frame.shape, "columns": frame.columns.tolist(), "nan_count_mirror_data": int(np.isnan(numeric).sum())}


def run():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    search_path = RESULT_DIR / "q3_optimization_search.csv"
    if search_path.exists():
        search = pd.read_csv(search_path)
    else:
        rows = []
        for index, dims in enumerate(candidate_dimensions(), start=1):
            design, zone = construct(dims)
            screened = screen_design(design)
            constraints = constraint_report(design)
            rows.append(
                {
                    "candidate": index,
                    **{f"zone_{j + 1}_size_m": value for j, value in enumerate(dims)},
                    **constraints,
                    **{f"screen_{key}": value for key, value in screened.items()},
                }
            )
            print(index, dims, screened["power_kw"] / 1000.0, screened["power_per_area_kw_m2"])
        search = pd.DataFrame(rows)
        search.to_csv(search_path, index=False, encoding="utf-8-sig")

    design, zone = construct(FINAL_DIMS)
    time_frame = pd.read_csv(RESULT_DIR / "q3_candidate_final_times.csv")
    monthly, annual = aggregate_monthly_and_annual(time_frame)
    constraints = constraint_report(design, rated_power_mw=annual["power_mw"])
    if annual["power_mw"] < 60.0 or not constraints["all_geometric_constraints_pass"]:
        raise RuntimeError(f"Q3 FINAL design violates constraints: {constraints}")

    sensitivity_rows = []
    for scale in (0.98, 0.99, 0.995, 1.0, 1.005, 1.01, 1.02):
        scaled = tuple(np.asarray(FINAL_DIMS) * scale)
        if max(scaled) >= 6.55:  # nearest-center spacing is 11.55 m
            sensitivity_rows.append({"scale": scale, "status": "geometric_infeasible", "power_mw": np.nan, "power_per_area_kw_m2": np.nan})
            continue
        perturbed, _ = construct(scaled)
        screened = screen_design(perturbed)
        sensitivity_rows.append({"scale": scale, "status": "FAST", "power_mw": screened["power_kw"] / 1000.0, "power_per_area_kw_m2": screened["power_per_area_kw_m2"]})
    sensitivity = pd.DataFrame(sensitivity_rows)

    time_frame.to_csv(RESULT_DIR / "q3_time_results.csv", index=False, encoding="utf-8-sig")
    monthly.to_csv(RESULT_DIR / "q3_monthly_results.csv", index=False, encoding="utf-8-sig")
    sensitivity.to_csv(RESULT_DIR / "q3_sensitivity.csv", index=False, encoding="utf-8-sig")
    sensitivity_excel = sensitivity.fillna("NOT_EVALUATED")
    design_frame = pd.DataFrame(
        {
            "mirror_id": np.arange(1, len(design.centers) + 1),
            "zone": zone + 1,
            "width_m": design.widths,
            "height_m": design.heights,
            "installation_height_m": design.centers[:, 2],
            "x_m": design.centers[:, 0],
            "y_m": design.centers[:, 1],
        }
    )
    design_frame.to_csv(RESULT_DIR / "q3_design.csv", index=False, encoding="utf-8-sig")
    annual_frame = pd.DataFrame([{**annual, **constraints}])
    write_excel_checked(
        RESULT_DIR / "q3_tables.xlsx",
        {"表1_月均": monthly, "表2_年均": annual_frame, "优化搜索": search, "敏感性": sensitivity_excel, "分区设计": design_frame},
        decimals=6,
        allow_nan=False,
    )
    excel_check = write_official_result(design, RESULT_DIR / "result3.xlsx")
    report = {
        "zone_fractions": ZONE_FRACTIONS,
        "zone_dimensions_m": FINAL_DIMS,
        "zone_installation_heights_m": tuple(value / 2.0 + 0.05 for value in FINAL_DIMS),
        "annual": annual,
        "constraints": constraints,
        "optimization_value": {
            "power_mw": float(search.loc[search["candidate"] == 6, "screen_power_kw"].iloc[0] / 1000.0),
            "power_per_area_kw_m2": float(search.loc[search["candidate"] == 6, "screen_power_per_area_kw_m2"].iloc[0]),
        },
        "final_verified_value": {"power_mw": annual["power_mw"], "power_per_area_kw_m2": annual["power_per_area_kw_m2"]},
        "evaluations": len(search),
        "elapsed_seconds": perf_counter() - started,
        "excel": excel_check,
        "model_note": "four radial quantile zones on the Q2 triangular lattice; MODEL_CONFIRMATION_REQUIRED",
    }
    (RESULT_DIR / "q3_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return design, time_frame, monthly, annual, search, sensitivity, report


if __name__ == "__main__":
    run()
