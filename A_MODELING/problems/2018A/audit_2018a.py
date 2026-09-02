"""Independent read-only reverse audit of generated 2018A artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.validation import check_bounds, check_finite, check_monotonic_time

RESULTS = ROOT / "results" / "2018A"
ARCHIVE = ROOT / "data" / "2018A" / "official" / "CUMCM2018Problems.rar"
EXPECTED_SHA256 = "DC2DB8A836D6D3DA519DF0D9DB9D68F6989ADBC91F25CDC471BFA0C8F415865E"


def audit() -> dict:
    checks = []

    def add(name: str, passed: bool, detail: str):
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest().upper()
    add("official_archive_hash", digest == EXPECTED_SHA256, digest)

    p1 = pd.read_excel(RESULTS / "problem1.xlsx", sheet_name=None)
    add("problem1_required_name", (RESULTS / "problem1.xlsx").exists(), "official requested filename")
    time_values = p1["SkinTemperature"]["time_s"].to_numpy()
    add("problem1_time_index", np.array_equal(time_values, np.arange(5401)) and check_monotonic_time(time_values), f"rows={len(p1['SkinTemperature'])}")
    add("problem1_complete_field", p1["TemperatureField"].shape == (5401, 155), str(p1["TemperatureField"].shape))
    add("problem1_finite", all(check_finite(frame.select_dtypes(include=[np.number]).to_numpy()) for frame in p1.values()), "all numeric cells finite")
    add("si_grid_units", abs(p1["Grid"]["dx_m"].sum() - 0.0152) < 1e-12, f"total={p1['Grid']['dx_m'].sum():.12g} m")

    validation = pd.read_excel(RESULTS / "validation.xlsx", sheet_name=None)
    analytic = validation["Analytic"]
    cn_error = analytic.loc[analytic["method"] == "CN", "max_error"].to_numpy()
    add("analytic_convergence", bool(np.all(np.diff(cn_error) < 0) and cn_error[-1] < 5e-7), str(cn_error.tolist()))
    cross = validation["ExplicitCN"].iloc[0]
    add("explicit_stability", cross["used_dt_s"] < cross["explicit_dt_limit_s"], f"used={cross['used_dt_s']}, limit={cross['explicit_dt_limit_s']}")
    add("explicit_cn_crosscheck", cross["field_max_abs_error_c"] < 1e-3, f"max={cross['field_max_abs_error_c']:.3e} C")
    interface = validation["Interface"]
    add("interface_temperature_continuity", interface["temperature_residual_c"].abs().max() < 1e-10, f"max={interface['temperature_residual_c'].abs().max():.3e} C")
    add("interface_flux_continuity", interface["heat_flux_residual_w_m2"].abs().max() < 1e-10, f"max={interface['heat_flux_residual_w_m2'].abs().max():.3e} W/m2")

    multistart = validation["Multistart"]
    fitted_parameters = multistart[["h_out_w_m2k", "h_skin_w_m2k"]].to_numpy()
    add("fit_bounds", check_bounds(fitted_parameters, [1, 1], [500, 100]), "all starts within bounds")
    add("fit_multistart_repeatability", multistart["h_out_w_m2k"].max() - multistart["h_out_w_m2k"].min() < 0.01 and multistart["h_skin_w_m2k"].max() - multistart["h_skin_w_m2k"].min() < 0.001, "five distant starts agree")

    q2 = pd.read_excel(RESULTS / "q2_results.xlsx", sheet_name=None)
    q3 = pd.read_excel(RESULTS / "q3_results.xlsx", sheet_name=None)
    q2_summary, q3_summary = q2["Summary"].iloc[0], q3["Summary"].iloc[0]
    add("q2_constraints", bool(q2_summary["feasible"] and q2_summary["margin_47_c"] > 0 and q2_summary["margin_duration_s"] > 0), f"margins={q2_summary['margin_47_c']:.6f} C,{q2_summary['margin_duration_s']:.6f} s")
    add("q3_constraints", bool(q3_summary["feasible"] and q3_summary["margin_47_c"] > 0 and q3_summary["margin_duration_s"] > 0), f"margins={q3_summary['margin_47_c']:.6f} C,{q3_summary['margin_duration_s']:.6f} s")
    q2_minus = q2["Neighborhood"].loc[np.isclose(q2["Neighborhood"]["offset_mm"], -0.1)].iloc[0]
    q3_minus = q3["NeighborhoodII"].loc[np.isclose(q3["NeighborhoodII"]["offset_mm"], -0.1)].iloc[0]
    add("q2_neighbor_direction", not bool(q2_minus["feasible"]), "-0.1 mm is infeasible")
    add("q3_neighbor_direction", not bool(q3_minus["feasible"]), "-0.1 mm layer II is infeasible")
    add("q2_mesh_convergence", validation["Q2Convergence"]["critical_d_ii_mm"].max() - validation["Q2Convergence"]["critical_d_ii_mm"].min() < 1e-3, "spread < 0.001 mm")
    add("q3_mesh_convergence", validation["Q3Convergence"]["critical_d_ii_mm"].max() - validation["Q3Convergence"]["critical_d_ii_mm"].min() < 1e-3, "spread < 0.001 mm")

    summary = json.loads((RESULTS / "results_summary.json").read_text(encoding="utf-8"))
    add("figure_data_q2_match", abs(summary["q2"]["reported_d_ii_mm"] - q2_summary["reported_d_ii_mm"]) < 1e-12, "summary and workbook match")
    add("figure_data_q3_match", abs(summary["q3"]["reported_d_ii_mm"] - q3_summary["reported_d_ii_mm"]) < 1e-12, "summary and workbook match")
    figures = sorted((RESULTS / "figures").glob("*.png"))
    add("figures_present", len(figures) == 7 and all(path.stat().st_size > 50_000 for path in figures), f"png_count={len(figures)}")
    origin = sorted((RESULTS / "origin_data").glob("*.xlsx"))
    add("origin_present", len(origin) >= 6, f"xlsx_count={len(origin)}")

    failed = [item for item in checks if item["status"] == "FAIL"]
    return {"passed": not failed, "failed_count": len(failed), "checks": checks, "manual_warning": "Nominal optimum is sensitive to +/-5% boundary/material perturbations; robust design is outside the official nominal objective."}


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
