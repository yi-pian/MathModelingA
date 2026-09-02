"""Numerical, geometric, performance and export validation for the 2023A benchmark."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.geometry import angle_between
from core.validation import ValidationReport, check_finite, check_range
from field import evaluate_time
from heliostat import mirror_geometry, reflected_direction
from layout import apply_radial_zones, constraint_report, generate_hexagonal_layout
from problem_data import PrecisionConfig, RESULT_DIR, load_q1_design
from solar import direct_normal_irradiance, solar_position


def _excel_check(path, expected_rows):
    frame = pd.read_excel(path)
    return {
        "file": path.name,
        "shape": list(frame.shape),
        "columns": frame.columns.tolist(),
        "nan_count": int(frame.isna().sum().sum()),
        "inf_count": int(np.isinf(frame.select_dtypes(include=[np.number]).to_numpy()).sum()),
        "mirror_ids_sequential": frame.iloc[:, 2].tolist() == list(range(1, expected_rows + 1)),
        "valid": bool(
            frame.shape == (expected_rows, 8)
            and frame.iloc[:, 2].tolist() == list(range(1, expected_rows + 1))
            and np.all(np.isfinite(frame.to_numpy(float)))
        ),
    }


def run():
    report = ValidationReport()
    diagnostics = {}

    alpha_am, gamma_am, sun_am = solar_position(0, 9.0)
    alpha_pm, gamma_pm, sun_pm = solar_position(0, 15.0)
    solar_norm_error = max(abs(np.linalg.norm(sun_am) - 1.0), abs(np.linalg.norm(sun_pm) - 1.0))
    report.add("solar unit vectors", solar_norm_error < 2e-12, f"max residual={solar_norm_error:.3e}")
    report.add("AM/PM azimuth quadrant", gamma_am < 0 < gamma_pm and sun_am[0] > 0 > sun_pm[0])
    report.add("AM/PM altitude symmetry", abs(alpha_am - alpha_pm) < 2e-12, f"residual={abs(alpha_am-alpha_pm):.3e}")

    q1 = load_q1_design()
    _, _, sun = solar_position(0, 12.0)
    geometry = mirror_geometry(q1.centers, q1.receiver_center, sun)
    reflected = reflected_direction(-sun, geometry.normals)
    reflection_residual = np.linalg.norm(reflected - geometry.receiver_directions, axis=1)
    normal_residual = np.abs(np.linalg.norm(geometry.normals, axis=1) - 1.0)
    report.add("mirror normal unit length", float(np.max(normal_residual)) < 2e-12, f"max={np.max(normal_residual):.3e}")
    report.add("reflection law", float(np.max(reflection_residual)) < 3e-12, f"max vector residual={np.max(reflection_residual):.3e}")
    diagnostics["maximum_reflection_angle_rad"] = float(max(angle_between(reflected[i], geometry.receiver_directions[i]) for i in range(len(reflected))))

    dni = float(direct_normal_irradiance(alpha_am))
    levels = {}
    for name, config in (
        ("FAST", "FAST"),
        ("STANDARD", "STANDARD"),
        ("FINAL", "FINAL"),
        ("AUDIT", PrecisionConfig("AUDIT", 11, 73, 1.5)),
    ):
        result = evaluate_time(q1, sun, float(direct_normal_irradiance(solar_position(0, 12.0)[0])), precision=config)
        levels[name] = {**result.summary(q1.areas), "seconds": result.timings_s["total"]}
    final_audit_relative = abs(levels["FINAL"]["power_kw"] - levels["AUDIT"]["power_kw"]) / levels["AUDIT"]["power_kw"]
    report.add("FINAL/AUDIT power convergence", final_audit_relative < 0.002, f"relative difference={final_audit_relative:.6%}")
    diagnostics["precision_levels_march21_noon"] = levels

    q1_time = pd.read_csv(RESULT_DIR / "q1_time_results.csv")
    efficiency_columns = ["eta_cos", "eta_at", "eta_sb", "eta_trunc", "eta_total"]
    report.add("Q1 all efficiency bounds", all(check_range(q1_time[column], 0.0, 1.0) for column in efficiency_columns))
    report.add("Q1 finite powers", check_finite(q1_time["power_kw"]) and bool((q1_time["power_kw"] >= 0).all()))

    q2 = generate_hexagonal_layout([0.0, 50.0], 6.5, 6.5, 3.3, spacing_gap=0.05)
    q2_annual = pd.read_csv(RESULT_DIR / "q2_time_results.csv")["power_kw"].mean() / 1000.0
    q2_constraints = constraint_report(q2, rated_power_mw=q2_annual)
    q3, _ = apply_radial_zones(
        q2,
        (0.25, 0.50, 0.75),
        (6.54, 6.48, 6.42, 6.36),
        (6.54, 6.48, 6.42, 6.36),
        tuple(value / 2.0 + 0.05 for value in (6.54, 6.48, 6.42, 6.36)),
    )
    q3_annual = pd.read_csv(RESULT_DIR / "q3_time_results.csv")["power_kw"].mean() / 1000.0
    q3_constraints = constraint_report(q3, rated_power_mw=q3_annual)
    report.add("Q2 geometric constraints", q2_constraints["all_geometric_constraints_pass"], json.dumps(q2_constraints, ensure_ascii=False))
    report.add("Q2 rated power", q2_annual >= 60.0, f"margin={q2_annual-60:.6f} MW")
    report.add("Q3 geometric constraints", q3_constraints["all_geometric_constraints_pass"], json.dumps(q3_constraints, ensure_ascii=False))
    report.add("Q3 rated power", q3_annual >= 60.0, f"margin={q3_annual-60:.6f} MW")

    excel = [_excel_check(RESULT_DIR / "result2.xlsx", len(q2.centers)), _excel_check(RESULT_DIR / "result3.xlsx", len(q3.centers))]
    report.add("official Excel roundtrip", all(item["valid"] for item in excel), json.dumps(excel, ensure_ascii=False))

    q3_sensitivity = pd.read_csv(RESULT_DIR / "q3_sensitivity.csv")
    down_half = q3_sensitivity.loc[np.isclose(q3_sensitivity["scale"], 0.995), "power_mw"].iloc[0]
    report.add("Q3 -0.5% FAST perturbation", down_half >= 60.0, f"FAST power={down_half:.6f} MW")
    report.add("solar half-angle model", manual=True, detail="4.65 mrad is an external physical constant; MODEL_CONFIRMATION_REQUIRED")
    report.add("annual averaging interpretation", manual=True, detail="60 official points are equally weighted; MODEL_CONFIRMATION_REQUIRED")
    report.add("layout-family global optimality", manual=True, detail="triangular lattice/four zones do not prove unrestricted global optimality")

    diagnostics.update(
        {
            "q2_constraints": q2_constraints,
            "q3_constraints": q3_constraints,
            "excel": excel,
            "q1_candidate_reduction": {
                "raw_per_time": 6086560,
                "mean_candidates_per_time": float(q1_time["average_candidates"].mean() * len(q1.centers)),
                "reduction_fraction": 1.0 - float(q1_time["average_candidates"].mean() * len(q1.centers)) / 6086560.0,
            },
        }
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "validation_report.txt").write_text(report.render(), encoding="utf-8")
    (RESULT_DIR / "validation_details.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report.render())
    return report, diagnostics


if __name__ == "__main__":
    run()
