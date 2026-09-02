"""Promote strictly verified Q3/Q4 candidates found by the figure-data stress test.

The independent graph plan is unchanged. This script corrects the numerical
result package after the high-resolution feasibility audit found that the
initial heuristic selections were mildly dominated.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "vendor"))

from solve_blind_2020a import crossings, eval_design, violations  # noqa: E402

RESULTS = ROOT / "results"
FIGDATA = ROOT / "figure_data"


def summary_map(df):
    return {(r.section, r.item): float(r.value) for r in df.itertuples()}


def replace_section_metrics(summary, section, x, metrics, area_cap=None):
    items = {
        "T1_5": (x[0], "C"),
        "T6": (x[1], "C"),
        "T7": (x[2], "C"),
        "T8_9": (x[3], "C"),
        "speed": (x[4], "cm/min"),
        "max_rise": (metrics["max_rise"], "various"),
        "min_fall": (metrics["min_fall"], "various"),
        "soak_150_190": (metrics["soak_150_190"], "various"),
        "above_217": (metrics["above_217"], "various"),
        "peak": (metrics["peak"], "various"),
        "peak_time": (metrics["peak_time"], "various"),
        "area_q3": (metrics["area_q3"], "various"),
        "asymmetry_q4": (metrics["asymmetry_q4"], "various"),
    }
    if area_cap is not None:
        items["area_cap"] = (area_cap, "C*s")
    summary = summary[summary.section != section].copy()
    add = pd.DataFrame(
        [{"section": section, "item": k, "value": v, "unit": u} for k, (v, u) in items.items()]
    )
    return pd.concat([summary, add], ignore_index=True)


def objective_table(curve):
    q = curve.iloc[::4].copy()
    t = q.time_s.to_numpy()
    y = q.temperature_C.to_numpy()
    ip = int(np.argmax(y))
    up = crossings(t, y, 217.0)[0]
    tp = float(t[ip])
    q["threshold_C"] = 217.0
    q["area_floor_C"] = np.where((t >= up) & (t <= tp), 217.0, np.nan)
    q["area_curve_C"] = np.where((t >= up) & (t <= tp), y, np.nan)
    q[["time_s", "temperature_C", "threshold_C", "area_floor_C", "area_curve_C"]].to_csv(
        FIGDATA / "main4_q3_objective_area.csv", index=False
    )
    pd.DataFrame([{"time_s": tp, "peak_C": float(y[ip]), "label": "selected optimum"}]).to_csv(
        FIGDATA / "main4_q3_peak.csv", index=False
    )


def mirror_table():
    rows = []
    for design, file in [("Q3 area minimum", "q3_curve.csv"), ("Q4 selected", "q4_curve.csv")]:
        curve = pd.read_csv(RESULTS / file)
        t = curve.time_s.to_numpy()
        y = curve.temperature_C.to_numpy()
        ip = int(np.argmax(y))
        tp = t[ip]
        cs = crossings(t, y, 217.0)
        common = min(tp - cs[0], cs[-1] - tp)
        u = np.linspace(0.0, common, 180)
        design_rows = []
        for uu, hh, cc in zip(u, np.interp(tp - u, t, y), np.interp(tp + u, t, y)):
            rows.append({"design": design, "relative_time_s": uu, "heating_C": hh, "cooling_C": cc})
            design_rows.append({"relative_time_s": uu, "heating_C": hh, "cooling_C": cc})
        suffix = "q3" if design.startswith("Q3") else "q4"
        pd.DataFrame(design_rows).to_csv(FIGDATA / f"main5_q4_mirror_{suffix}.csv", index=False)
    pd.DataFrame(rows).to_csv(FIGDATA / "main5_q4_mirrored_branches.csv", index=False)


def main():
    summary = pd.read_csv(RESULTS / "summary.csv")
    sm = summary_map(summary)
    params = np.array(
        [
            sm[("calibration", "log_tau0")],
            sm[("calibration", "beta")],
            sm[("calibration", "smoothing_sigma")],
            sm[("calibration", "log_cool_multiplier")],
            sm[("calibration", "front_infiltration_power")],
            sm[("calibration", "cool_transition_length")],
        ]
    )
    feasible = pd.read_csv(FIGDATA / "main5_q4_feasible_samples.csv")
    q3_row = feasible.loc[feasible.area_C_s.idxmin()]
    q3 = q3_row[["T1_5_C", "T6_C", "T7_C", "T8_9_C", "speed_cm_min"]].to_numpy(float)
    t3, y3, s3, a3, m3 = eval_design(q3, params, dt=0.05)
    if np.max(violations(m3)) > 1e-7:
        raise RuntimeError("Q3 promoted candidate failed strict feasibility")
    cap = 1.05 * m3["area_q3"]
    eligible = feasible[feasible.area_C_s <= cap]
    q4_row = eligible.loc[eligible.asymmetry_C.idxmin()]
    q4 = q4_row[["T1_5_C", "T6_C", "T7_C", "T8_9_C", "speed_cm_min"]].to_numpy(float)
    t4, y4, s4, a4, m4 = eval_design(q4, params, dt=0.05)
    if np.max(violations(m4)) > 1e-7 or m4["area_q3"] > cap + 1e-8:
        raise RuntimeError("Q4 promoted candidate failed strict feasibility or area cap")

    old = {
        "Q3_area_C_s": sm[("Q3", "area_q3")],
        "Q3_asymmetry_C": sm[("Q3", "asymmetry_q4")],
        "Q4_area_C_s": sm[("Q4", "area_q3")],
        "Q4_asymmetry_C": sm[("Q4", "asymmetry_q4")],
    }
    summary = replace_section_metrics(summary, "Q3", q3, m3)
    summary = replace_section_metrics(summary, "Q4", q4, m4, area_cap=cap)
    summary.to_csv(RESULTS / "summary.csv", index=False)
    pd.DataFrame({"time_s": t3, "temperature_C": y3, "slope_C_per_s": s3, "air_C": a3}).to_csv(
        RESULTS / "q3_curve.csv", index=False
    )
    pd.DataFrame({"time_s": t4, "temperature_C": y4, "slope_C_per_s": s4, "air_C": a4}).to_csv(
        RESULTS / "q4_curve.csv", index=False
    )
    objective_table(pd.read_csv(RESULTS / "q3_curve.csv"))
    mirror_table()
    pd.DataFrame(
        [
            {"design": "Q3 area minimum", "area_C_s": m3["area_q3"], "asymmetry_C": m3["asymmetry_q4"]},
            {"design": "Q4 selected", "area_C_s": m4["area_q3"], "asymmetry_C": m4["asymmetry_q4"]},
        ]
    ).to_csv(FIGDATA / "main5_q4_selected_designs.csv", index=False)
    pd.DataFrame([{"area_C_s": m3["area_q3"], "asymmetry_C": m3["asymmetry_q4"]}]).to_csv(
        FIGDATA / "main5_q4_selected_q3.csv", index=False
    )
    pd.DataFrame([{"area_C_s": m4["area_q3"], "asymmetry_C": m4["asymmetry_q4"]}]).to_csv(
        FIGDATA / "main5_q4_selected_q4.csv", index=False
    )
    audit = pd.DataFrame(
        [
            {"field": "reason", "old": "initial heuristic search", "new": "strict high-resolution feasible-sample promotion"},
            {"field": "Q3 area (C s)", "old": old["Q3_area_C_s"], "new": m3["area_q3"]},
            {"field": "Q3 asymmetry (C)", "old": old["Q3_asymmetry_C"], "new": m3["asymmetry_q4"]},
            {"field": "Q4 area (C s)", "old": old["Q4_area_C_s"], "new": m4["area_q3"]},
            {"field": "Q4 asymmetry (C)", "old": old["Q4_asymmetry_C"], "new": m4["asymmetry_q4"]},
            {"field": "Q4 area cap (C s)", "old": sm[("Q4", "area_cap")], "new": cap},
        ]
    )
    audit.to_csv(FIGDATA / "post_plan_numerical_correction_audit.csv", index=False)

    # Separate display tables keep Origin plot roles unambiguous when a frozen
    # template is instantiated. Metrics still use the full-resolution data.
    cal = pd.read_csv(RESULTS / "calibration.csv")
    cal.iloc[::5][["time_s", "measured_C"]].to_csv(FIGDATA / "main1_measured_display.csv", index=False)
    cal[["time_s", "predicted_C"]].to_csv(FIGDATA / "main1_model_line.csv", index=False)
    cal.iloc[::3][["time_s", "residual_C"]].to_csv(FIGDATA / "main1_residual_display.csv", index=False)
    pd.DataFrame({"speed_cm_min": [65.0, 100.0], "limit_C": [240.0, 240.0]}).to_csv(
        FIGDATA / "main3_q2_lower_limit.csv", index=False
    )
    pd.DataFrame({"speed_cm_min": [65.0, 100.0], "limit_C": [250.0, 250.0]}).to_csv(
        FIGDATA / "main3_q2_upper_limit.csv", index=False
    )
    pd.DataFrame({"time_s": [0.0, 300.0], "threshold_C": [217.0, 217.0]}).to_csv(
        FIGDATA / "main4_q3_threshold.csv", index=False
    )
    area = pd.read_csv(FIGDATA / "main4_q3_objective_area.csv").dropna(subset=["area_curve_C"])
    area[["time_s", "area_curve_C"]].to_csv(FIGDATA / "main4_q3_area_upper.csv", index=False)
    area[["time_s", "area_floor_C"]].to_csv(FIGDATA / "main4_q3_area_lower.csv", index=False)
    feasible.iloc[::2][["area_C_s", "asymmetry_C"]].to_csv(FIGDATA / "main5_q4_cloud_display.csv", index=False)
    print(audit.to_string(index=False))
    print("Q3", q3, m3)
    print("Q4", q4, m4)


if __name__ == "__main__":
    main()
