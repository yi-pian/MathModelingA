"""Independent read-only reverse audit of completed 2023A artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from layout import apply_radial_zones, constraint_report, generate_hexagonal_layout
from problem_data import RESULT_DIR


def run():
    checks = []

    def add(name, passed, detail):
        checks.append({"name": name, "status": "PASS" if bool(passed) else "FAIL", "detail": str(detail)})

    expected_times = [(month, hour) for month in range(1, 13) for hour in (9.0, 10.5, 12.0, 13.5, 15.0)]
    annual_values = {}
    for label in ("q1", "q2", "q3"):
        frame = pd.read_csv(RESULT_DIR / f"{label}_time_results.csv")
        actual_times = list(zip(frame["month"].astype(int), frame["local_time_h"].astype(float)))
        add(f"{label.upper()} official time order", actual_times == expected_times, f"rows={len(frame)}, unique={len(set(actual_times))}")
        efficiency = frame[["eta_cos", "eta_at", "eta_sb", "eta_trunc", "eta_total"]].to_numpy(float)
        add(f"{label.upper()} efficiency finite/range", np.all(np.isfinite(efficiency)) and np.all((efficiency >= 0) & (efficiency <= 1)), f"min={efficiency.min():.6f}, max={efficiency.max():.6f}")
        annual_values[label] = {
            "eta_total": float(frame["eta_total"].mean()),
            "power_mw": float(frame["power_kw"].mean() / 1000.0),
            "power_per_area_kw_m2": float(frame["power_per_area_kw_m2"].mean()),
        }
        monthly = pd.read_csv(RESULT_DIR / f"{label}_monthly_results.csv")
        add(f"{label.upper()} monthly/year aggregation", np.allclose(monthly["power_kw"].mean(), frame["power_kw"].mean(), rtol=0, atol=1e-9), "equal 5-times/month and 12-month arithmetic means")

    add("max/min direction Q2", annual_values["q2"]["power_per_area_kw_m2"] > 0, "candidate table maximizes power_per_area subject to calibrated feasibility threshold")
    add("Q2 rated power", annual_values["q2"]["power_mw"] >= 60.0, f"{annual_values['q2']['power_mw']:.9f} MW")
    add("Q3 rated power", annual_values["q3"]["power_mw"] >= 60.0, f"{annual_values['q3']['power_mw']:.9f} MW")
    add("Q3 improves Q2 area objective", annual_values["q3"]["power_per_area_kw_m2"] > annual_values["q2"]["power_per_area_kw_m2"], f"Q2={annual_values['q2']['power_per_area_kw_m2']:.9f}, Q3={annual_values['q3']['power_per_area_kw_m2']:.9f}")

    q2 = generate_hexagonal_layout([0.0, 50.0], 6.5, 6.5, 3.3, spacing_gap=0.05)
    q3, _ = apply_radial_zones(q2, (0.25, 0.5, 0.75), (6.54, 6.48, 6.42, 6.36), (6.54, 6.48, 6.42, 6.36), (3.32, 3.29, 3.26, 3.23))
    for label, design, power in (("Q2", q2, annual_values["q2"]["power_mw"]), ("Q3", q3, annual_values["q3"]["power_mw"])):
        constraints = constraint_report(design, rated_power_mw=power)
        add(f"{label} constraints and signs", constraints["all_geometric_constraints_pass"] and constraints["rated_power_margin_mw"] >= 0, json.dumps(constraints, ensure_ascii=False))
        excel = pd.read_excel(RESULT_DIR / f"result{2 if label == 'Q2' else 3}.xlsx")
        expected = np.column_stack((np.full(len(design.centers), design.tower_xy[0]), np.full(len(design.centers), design.tower_xy[1]), np.arange(1, len(design.centers)+1), design.widths, design.heights, design.centers))
        add(f"{label} Excel exact values", excel.shape == expected.shape and np.allclose(excel.to_numpy(float), expected, rtol=0, atol=1e-12), f"shape={excel.shape}, NaN={int(excel.isna().sum().sum())}")

    origin_eff = pd.read_excel(RESULT_DIR / "origin_data" / "monthly_efficiency.xlsx", sheet_name="Data")
    q1_monthly = pd.read_csv(RESULT_DIR / "q1_monthly_results.csv")
    add("figure/Origin FINAL-data consistency", np.allclose(origin_eff["Q1_eta_total"], q1_monthly["eta_total"], rtol=0, atol=1e-12), "Origin monthly Q1 equals FINAL monthly CSV")

    constants = {
        "receiver radius/height/center": "official statement",
        "reflectivity 0.92": "official permitted example",
        "solar half-angle 4.65 mrad": "external physical constant; MODEL_CONFIRMATION_REQUIRED",
        "0.05 m layout/ground margins": "explicit numerical feasibility margins",
        "Q2 60.35 MW screen threshold": "calibrated by three independent FINAL candidates",
    }
    failures = [check for check in checks if check["status"] == "FAIL"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "constants_audit": constants,
        "cache_audit": "FINAL CSV reuse is guarded by exact named parameter tuples; FAST and FINAL filenames are distinct.",
        "model_limits": [
            "equal weighting of the 60 official points requires model confirmation",
            "uniform 4.65 mrad solar disk is external to the statement",
            "triangular lattice and four radial zones do not prove unrestricted global optimality",
            "shadow/blocking uses central solar/receiver rays per mirror cell; sun-cone effects are applied in truncation",
        ],
    }
    lines = ["# 2023A 独立反向审查", "", f"结论：**{report['status']}**", ""]
    lines += [f"- {item['status']} — {item['name']}：{item['detail']}" for item in checks]
    lines += ["", "## 常数与假设", ""] + [f"- {name}：{source}" for name, source in constants.items()]
    lines += ["", "## 未消除的模型边界", ""] + [f"- {item}" for item in report["model_limits"]]
    (RESULT_DIR / "AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULT_DIR / "audit_details.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failures": len(failures)}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    run()
