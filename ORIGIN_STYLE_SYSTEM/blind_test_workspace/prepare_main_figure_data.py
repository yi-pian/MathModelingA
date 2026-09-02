"""Prepare numerical evidence tables for the blind-test MAIN figures.

This script does not draw figures. It only derives display-ready tables from
the frozen model/result package and performs a deterministic local feasibility
sample for the Question 4 area--asymmetry evidence map.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from solve_blind_2020a import crossings, eval_design, metrics, violations  # noqa: E402

RESULTS = ROOT / "results"
FIGDATA = ROOT / "figure_data"
FIGDATA.mkdir(exist_ok=True)


def summary_map():
    s = pd.read_csv(RESULTS / "summary.csv")
    return {(r.section, r.item): float(r.value) for r in s.itertuples()}


def design_from_summary(sm, section):
    return np.array(
        [
            sm[(section, "T1_5")],
            sm[(section, "T6")],
            sm[(section, "T7")],
            sm[(section, "T8_9")],
            sm[(section, "speed")],
        ],
        dtype=float,
    )


def calibration_table():
    df = pd.read_csv(RESULTS / "calibration.csv")
    df.to_csv(FIGDATA / "main1_calibration_fit_residual.csv", index=False)


def q1_table():
    q1 = pd.read_csv(RESULTS / "q1_curve.csv").iloc[::4].copy()
    q1["checkpoint_C"] = np.nan
    sm = summary_map()
    checkpoints = [
        ("zone 3 midpoint", sm[("Q1", "zone3_mid")]),
        ("zone 6 midpoint", sm[("Q1", "zone6_mid")]),
        ("zone 7 midpoint", sm[("Q1", "zone7_mid")]),
        ("zone 8 end", sm[("Q1", "zone8_end")]),
    ]
    # Distances from the official geometry, converted at 78 cm/min.
    zone_len, gap, front = 30.5, 5.0, 25.0
    x_positions = [
        front + 2 * (zone_len + gap) + zone_len / 2,
        front + 5 * (zone_len + gap) + zone_len / 2,
        front + 6 * (zone_len + gap) + zone_len / 2,
        front + 7 * (zone_len + gap) + zone_len,
    ]
    checkpoint_rows = []
    for (label, temp), x in zip(checkpoints, x_positions):
        t = x / (78.0 / 60.0)
        checkpoint_rows.append({"time_s": t, "checkpoint_C": temp, "checkpoint_label": label})
    q1[["time_s", "temperature_C", "air_C"]].to_csv(FIGDATA / "main2_q1_profiles.csv", index=False)
    pd.DataFrame(checkpoint_rows).to_csv(FIGDATA / "main2_q1_checkpoints.csv", index=False)


def q2_table():
    q2 = pd.read_csv(RESULTS / "q2_speed_scan.csv")
    sm = summary_map()
    selected_speed = sm[("Q2", "max_feasible_speed")]
    selected_peak = sm[("Q2", "peak")]
    out = q2[["speed_cm_min", "peak"]].copy()
    out["lower_limit_C"] = 240.0
    out["upper_limit_C"] = 250.0
    out.to_csv(FIGDATA / "main3_q2_peak_vs_speed.csv", index=False)
    pd.DataFrame(
        [{"speed_cm_min": selected_speed, "peak_C": selected_peak, "label": "maximum feasible speed"}]
    ).to_csv(FIGDATA / "main3_q2_selected.csv", index=False)


def q3_table():
    q3 = pd.read_csv(RESULTS / "q3_curve.csv").iloc[::4].copy()
    t = q3["time_s"].to_numpy()
    y = q3["temperature_C"].to_numpy()
    ip = int(np.argmax(y))
    cross = crossings(t, y, 217.0)
    up = cross[0]
    tp = float(t[ip])
    q3["threshold_C"] = 217.0
    q3["area_floor_C"] = np.where((t >= up) & (t <= tp), 217.0, np.nan)
    q3["area_curve_C"] = np.where((t >= up) & (t <= tp), y, np.nan)
    q3[["time_s", "temperature_C", "threshold_C", "area_floor_C", "area_curve_C"]].to_csv(
        FIGDATA / "main4_q3_objective_area.csv", index=False
    )
    pd.DataFrame(
        [{"time_s": tp, "peak_C": float(y[ip]), "label": "selected optimum"}]
    ).to_csv(FIGDATA / "main4_q3_peak.csv", index=False)


def q4_feasible_and_mirror():
    sm = summary_map()
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
    x3 = design_from_summary(sm, "Q3")
    x4 = design_from_summary(sm, "Q4")
    bounds_lo = np.array([165.0, 185.0, 225.0, 245.0, 65.0])
    bounds_hi = np.array([185.0, 205.0, 245.0, 265.0, 100.0])
    rng = np.random.default_rng(20200901)

    # Dense local evidence near the two selected solutions plus a wider search.
    n_local, n_bridge, n_wide = 1400, 500, 600
    centers = np.where(rng.random((n_local, 1)) < 0.55, x3, x4)
    local_scale = np.array([2.3, 2.3, 2.3, 1.2, 2.8])
    local = centers + rng.normal(size=(n_local, 5)) * local_scale
    alpha = rng.random((n_bridge, 1))
    bridge = (1.0 - alpha) * x3 + alpha * x4 + rng.normal(size=(n_bridge, 5)) * np.array([1.0, 1.0, 1.0, 0.6, 1.2])
    wide = rng.uniform(bounds_lo, bounds_hi, size=(n_wide, 5))
    candidates = np.vstack([x3, x4, local, bridge, wide])
    candidates = np.clip(candidates, bounds_lo, bounds_hi)

    coarse_rows = []
    for i, x in enumerate(candidates):
        *_, m = eval_design(x, params, dt=0.35)
        if np.max(violations(m)) <= 5e-3:
            coarse_rows.append(
                {
                    "sample_id": i,
                    "T1_5_C": x[0],
                    "T6_C": x[1],
                    "T7_C": x[2],
                    "T8_9_C": x[3],
                    "area_C_s": m["area_q3"],
                    "asymmetry_C": m["asymmetry_q4"],
                    "peak_C": m["peak"],
                    "speed_cm_min": x[4],
                }
            )
        if (i + 1) % 400 == 0:
            print(f"evaluated {i + 1}/{len(candidates)}; coarse-feasible={len(coarse_rows)}", flush=True)

    # Re-evaluate every coarse-feasible point with the high-resolution model.
    # A candidate is retained only when all official inequalities are met at
    # this resolution. This prevents sub-240 C peaks from entering the figure
    # merely because the coarse integrator rounded them upward.
    rows = []
    for j, r in enumerate(coarse_rows):
        x = np.array([r["T1_5_C"], r["T6_C"], r["T7_C"], r["T8_9_C"], r["speed_cm_min"]])
        *_, m = eval_design(x, params, dt=0.05)
        if np.max(violations(m)) <= 1e-7:
            rows.append(
                {
                    **{k: r[k] for k in ["sample_id", "T1_5_C", "T6_C", "T7_C", "T8_9_C", "speed_cm_min"]},
                    "area_C_s": m["area_q3"],
                    "asymmetry_C": m["asymmetry_q4"],
                    "peak_C": m["peak"],
                }
            )
        if (j + 1) % 250 == 0:
            print(f"strictly checked {j + 1}/{len(coarse_rows)}; feasible={len(rows)}", flush=True)

    feasible = pd.DataFrame(rows).sort_values(["area_C_s", "asymmetry_C"]).reset_index(drop=True)
    if len(feasible) < 80:
        raise RuntimeError(f"DATA_EVIDENCE_INSUFFICIENT: only {len(feasible)} feasible samples")

    # Nondominated frontier for two minimization objectives.
    best_asym = np.inf
    keep = []
    for r in feasible.itertuples():
        if r.asymmetry_C < best_asym - 1e-5:
            keep.append(r.Index)
            best_asym = r.asymmetry_C
    frontier = feasible.loc[keep].copy()
    feasible.to_csv(FIGDATA / "main5_q4_feasible_samples.csv", index=False)
    frontier.to_csv(FIGDATA / "main5_q4_nondominated_frontier.csv", index=False)
    pd.DataFrame(
        [
            {"design": "Q3 area minimum", "area_C_s": sm[("Q3", "area_q3")], "asymmetry_C": sm[("Q3", "asymmetry_q4")]},
            {"design": "Q4 selected", "area_C_s": sm[("Q4", "area_q3")], "asymmetry_C": sm[("Q4", "asymmetry_q4")]},
        ]
    ).to_csv(FIGDATA / "main5_q4_selected_designs.csv", index=False)

    mirror_rows = []
    for design, file in [("Q3 area minimum", "q3_curve.csv"), ("Q4 selected", "q4_curve.csv")]:
        curve = pd.read_csv(RESULTS / file)
        t = curve.time_s.to_numpy()
        y = curve.temperature_C.to_numpy()
        ip = int(np.argmax(y))
        tp = t[ip]
        cs = crossings(t, y, 217.0)
        common = min(tp - cs[0], cs[-1] - tp)
        u = np.linspace(0.0, common, 180)
        heat = np.interp(tp - u, t, y)
        cool = np.interp(tp + u, t, y)
        for uu, hh, cc in zip(u, heat, cool):
            mirror_rows.append(
                {
                    "design": design,
                    "relative_time_s": uu,
                    "heating_C": hh,
                    "cooling_C": cc,
                }
            )
    pd.DataFrame(mirror_rows).to_csv(FIGDATA / "main5_q4_mirrored_branches.csv", index=False)

    report = pd.DataFrame(
        [
            {"metric": "candidate_count", "value": len(candidates)},
            {"metric": "feasible_count", "value": len(feasible)},
            {"metric": "frontier_count", "value": len(frontier)},
            {"metric": "minimum_sampled_area_C_s", "value": feasible.area_C_s.min()},
            {"metric": "minimum_sampled_asymmetry_C", "value": feasible.asymmetry_C.min()},
        ]
    )
    report.to_csv(FIGDATA / "main5_q4_sampling_audit.csv", index=False)
    print(report.to_string(index=False))


def main():
    calibration_table()
    q1_table()
    q2_table()
    q3_table()
    q4_feasible_and_mirror()


if __name__ == "__main__":
    main()
