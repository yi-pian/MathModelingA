from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import differential_evolution, least_squares, minimize_scalar


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "A" / "附件.xlsx"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

ZONE_LEN = 30.5
GAP = 5.0
FRONT = 25.0
TOTAL = FRONT * 2 + 11 * ZONE_LEN + 10 * GAP


def raw_air_profile(x, s, front_power, cool_transition_cm):
    temps = np.array([s[0]] * 5 + [s[1], s[2]] + [s[3]] * 2 + [25.0] * 2)
    y = np.full_like(x, 25.0, dtype=float)
    for i, temp in enumerate(temps):
        a = FRONT + i * (ZONE_LEN + GAP)
        b = a + ZONE_LEN
        y[(x >= a) & (x <= b)] = temp
        if i < 10:
            g = (x > b) & (x < b + GAP)
            y[g] = temp + (temps[i + 1] - temp) * (x[g] - b) / GAP
    first = (x > 0) & (x < FRONT)
    y[first] = 25.0 + (temps[0] - 25.0) * (x[first] / FRONT) ** front_power
    zone9_end = FRONT + 8 * (ZONE_LEN + GAP) + ZONE_LEN
    cool_end = min(zone9_end + cool_transition_cm, TOTAL)
    cool = (x > zone9_end) & (x < cool_end)
    y[cool] = s[3] + (25.0 - s[3]) * (x[cool] - zone9_end) / max(cool_transition_cm, 1e-9)
    last_end = FRONT + 10 * (ZONE_LEN + GAP) + ZONE_LEN
    rear = (x > last_end) & (x <= TOTAL)
    y[rear] = 25.0
    return y


def air_profile(settings, sigma_cm, front_power, cool_transition_cm):
    dx = 0.1
    xg = np.arange(0.0, TOTAL + dx, dx)
    raw = raw_air_profile(xg, settings, front_power, cool_transition_cm)
    smooth = gaussian_filter1d(raw, max(sigma_cm / dx, 0.01), mode="nearest")
    return xg, smooth


def simulate(settings, speed_cm_min, params, dt=0.1):
    log_tau0, beta, sigma, log_cool_mult, front_power, cool_transition_cm = params
    v = speed_cm_min / 60.0
    xg, ag = air_profile(settings, sigma, front_power, cool_transition_cm)
    t_end = TOTAL / v
    t = np.arange(0.0, t_end, dt)
    if t.size == 0 or t[-1] < t_end:
        t = np.r_[t, t_end]

    def rhs(tt, yy):
        ta = np.interp(v * tt, xg, ag)
        cool_weight = 1.0 / (1.0 + np.exp(np.clip((ta - yy[0]) / 3.0, -40.0, 40.0)))
        tau = np.exp(log_tau0 + beta * (yy[0] - 150.0) / 100.0 + log_cool_mult * cool_weight)
        return [(ta - yy[0]) / tau]

    fast = dt >= 0.2
    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        [25.0],
        t_eval=t,
        rtol=2e-5 if fast else 2e-7,
        atol=2e-6 if fast else 2e-8,
        max_step=0.8 if fast else 0.25,
    )
    temp = sol.y[0]
    air = np.interp(v * t, xg, ag)
    cool_weight = 1.0 / (1.0 + np.exp(np.clip((air - temp) / 3.0, -40.0, 40.0)))
    slope = (air - temp) / np.exp(log_tau0 + beta * (temp - 150.0) / 100.0 + log_cool_mult * cool_weight)
    return t, temp, slope, air


def calibrate(exp):
    te = exp["时间(s)"].to_numpy(float)
    ye = exp["温度(ºC)"].to_numpy(float)

    def residual(p):
        t, y, _, _ = simulate([175.0, 195.0, 235.0, 255.0], 70.0, p, dt=0.25)
        pred = np.interp(te, t, y)
        return np.r_[pred - ye, 0.02 * (p - np.array([4.0, -0.5, 3.0, 0.8, 2.0, 30.0]))]

    fit = least_squares(
        residual,
        [4.0, -0.5, 3.0, 0.8, 2.0, 30.0],
        bounds=([2.5, -3.0, 0.05, 0.0, 0.4, 5.0], [5.5, 3.0, 20.0, 2.5, 10.0, 80.0]),
        loss="soft_l1",
        f_scale=0.8,
        max_nfev=600,
    )
    p = fit.x
    t, y, _, _ = simulate([175.0, 195.0, 235.0, 255.0], 70.0, p, dt=0.1)
    pred = np.interp(te, t, y)
    res = pred - ye
    return p, pred, res


def crossings(t, y, level):
    z = y - level
    idx = np.where(z[:-1] * z[1:] < 0)[0]
    out = []
    for i in idx:
        out.append(t[i] + (level - y[i]) * (t[i + 1] - t[i]) / (y[i + 1] - y[i]))
    return out


def metrics(t, y, slope):
    ip = int(np.argmax(y))
    tp = t[ip]
    peak = y[ip]
    rise = y[: ip + 1]
    tr = t[: ip + 1]
    c150 = crossings(tr, rise, 150.0)
    c190 = crossings(tr, rise, 190.0)
    c217 = crossings(t, y, 217.0)
    soak = c190[0] - c150[0] if c150 and c190 else np.nan
    above = c217[-1] - c217[0] if len(c217) >= 2 else 0.0
    if c217:
        tu = c217[0]
        m = (t >= tu) & (t <= tp)
        ta = np.r_[tu, t[m], tp]
        ya = np.interp(ta, t, y)
        area = np.trapezoid(np.maximum(ya - 217.0, 0.0), ta)
    else:
        area = 0.0

    asym = np.nan
    if len(c217) >= 2:
        left = tp - c217[0]
        right = c217[-1] - tp
        common = min(left, right)
        u = np.linspace(0.0, common, 500)
        yl = np.interp(tp - u, t, y)
        yr = np.interp(tp + u, t, y)
        core = np.trapezoid(np.abs(yl - yr), u)
        tail = abs(left - right) * max(peak - 217.0, 0.0) * 0.5
        asym = (core + tail) / max(left + right, 1e-9)

    return {
        "max_rise": float(np.max(slope[: ip + 1])),
        "min_fall": float(np.min(slope[ip:])),
        "soak_150_190": float(soak),
        "above_217": float(above),
        "peak": float(peak),
        "peak_time": float(tp),
        "area_q3": float(area),
        "asymmetry_q4": float(asym),
    }


def violations(m):
    vals = [
        max(0.0, -m["max_rise"]),
        max(0.0, m["max_rise"] - 3.0),
        max(0.0, -3.0 - m["min_fall"]),
        max(0.0, m["min_fall"]),
        max(0.0, 60.0 - m["soak_150_190"]),
        max(0.0, m["soak_150_190"] - 120.0),
        max(0.0, 40.0 - m["above_217"]),
        max(0.0, m["above_217"] - 90.0),
        max(0.0, 240.0 - m["peak"]),
        max(0.0, m["peak"] - 250.0),
    ]
    scales = np.array([3, 3, 3, 3, 60, 60, 40, 40, 10, 10], float)
    return np.array(vals) / scales


def eval_design(x, params, dt=0.2):
    settings = x[:4]
    speed = x[4]
    t, y, slope, air = simulate(settings, speed, params, dt=dt)
    return t, y, slope, air, metrics(t, y, slope)


def optimize_q3(params):
    bounds = [(165, 185), (185, 205), (225, 245), (245, 265), (65, 100)]

    def obj(x):
        *_, m = eval_design(x, params, dt=0.3)
        v = violations(m)
        return m["area_q3"] + 2e5 * np.dot(v, v) + 2e4 * np.sum(v)

    de = differential_evolution(obj, bounds, seed=2020, popsize=10, maxiter=70, tol=1e-4, polish=True, workers=1)
    return de.x, eval_design(de.x, params, dt=0.05)[-1]


def optimize_q4(params, q3_area):
    bounds = [(165, 185), (185, 205), (225, 245), (245, 265), (65, 100)]
    area_cap = 1.05 * q3_area

    def obj(x):
        *_, m = eval_design(x, params, dt=0.3)
        v = violations(m)
        area_v = max(0.0, m["area_q3"] - area_cap) / max(area_cap, 1.0)
        return m["asymmetry_q4"] + 2e5 * np.dot(v, v) + 2e4 * np.sum(v) + 2e5 * area_v * area_v + 2e4 * area_v

    de = differential_evolution(obj, bounds, seed=2024, popsize=10, maxiter=80, tol=1e-4, polish=True, workers=1)
    return de.x, eval_design(de.x, params, dt=0.05)[-1], area_cap


def main():
    exp = pd.read_excel(DATA)
    params, pred, res = calibrate(exp)
    calibration = pd.DataFrame({"time_s": exp.iloc[:, 0], "measured_C": exp.iloc[:, 1], "predicted_C": pred, "residual_C": res})
    calibration.to_csv(OUT / "calibration.csv", index=False)

    q1_settings = np.array([173.0, 198.0, 230.0, 257.0])
    t1, y1, s1, a1 = simulate(q1_settings, 78.0, params, dt=0.05)
    q1 = pd.DataFrame({"time_s": t1, "temperature_C": y1, "slope_C_per_s": s1, "air_C": a1})
    q1.to_csv(OUT / "q1_curve.csv", index=False)

    mids = {
        "zone3_mid": FRONT + 2 * (ZONE_LEN + GAP) + ZONE_LEN / 2,
        "zone6_mid": FRONT + 5 * (ZONE_LEN + GAP) + ZONE_LEN / 2,
        "zone7_mid": FRONT + 6 * (ZONE_LEN + GAP) + ZONE_LEN / 2,
        "zone8_end": FRONT + 7 * (ZONE_LEN + GAP) + ZONE_LEN,
    }
    v1 = 78.0 / 60.0
    q1_points = {k: float(np.interp(x / v1, t1, y1)) for k, x in mids.items()}

    fixed = np.array([182.0, 203.0, 237.0, 254.0])

    def speed_feas(speed):
        t, y, sl, _ = simulate(fixed, speed, params, dt=0.08)
        return metrics(t, y, sl)

    def q2_obj(speed):
        m = speed_feas(speed)
        return 1e4 * np.sum(violations(m)) - speed

    q2_opt = minimize_scalar(q2_obj, bounds=(65.0, 100.0), method="bounded", options={"xatol": 1e-7})
    q2_speed = float(q2_opt.x)
    q2_metrics = speed_feas(q2_speed)
    speeds = np.linspace(65, 100, 141)
    pd.DataFrame([{"speed_cm_min": v, **speed_feas(v)} for v in speeds]).to_csv(OUT / "q2_speed_scan.csv", index=False)

    x3, m3 = optimize_q3(params)
    t3, y3, sl3, a3, _ = eval_design(x3, params, dt=0.05)
    pd.DataFrame({"time_s": t3, "temperature_C": y3, "slope_C_per_s": sl3, "air_C": a3}).to_csv(OUT / "q3_curve.csv", index=False)

    x4, m4, cap = optimize_q4(params, m3["area_q3"])
    t4, y4, sl4, a4, _ = eval_design(x4, params, dt=0.05)
    pd.DataFrame({"time_s": t4, "temperature_C": y4, "slope_C_per_s": sl4, "air_C": a4}).to_csv(OUT / "q4_curve.csv", index=False)

    summary = []
    summary.append({"section": "calibration", "item": "log_tau0", "value": params[0], "unit": "log(s)"})
    summary.append({"section": "calibration", "item": "beta", "value": params[1], "unit": "1"})
    summary.append({"section": "calibration", "item": "smoothing_sigma", "value": params[2], "unit": "cm"})
    summary.append({"section": "calibration", "item": "log_cool_multiplier", "value": params[3], "unit": "1"})
    summary.append({"section": "calibration", "item": "front_infiltration_power", "value": params[4], "unit": "1"})
    summary.append({"section": "calibration", "item": "cool_transition_length", "value": params[5], "unit": "cm"})
    summary.append({"section": "calibration", "item": "RMSE", "value": np.sqrt(np.mean(res**2)), "unit": "C"})
    summary.append({"section": "calibration", "item": "MAE", "value": np.mean(np.abs(res)), "unit": "C"})
    summary.append({"section": "calibration", "item": "max_abs_residual", "value": np.max(np.abs(res)), "unit": "C"})
    for k, val in q1_points.items():
        summary.append({"section": "Q1", "item": k, "value": val, "unit": "C"})
    summary.append({"section": "Q2", "item": "max_feasible_speed", "value": q2_speed, "unit": "cm/min"})
    for k, val in q2_metrics.items():
        summary.append({"section": "Q2", "item": k, "value": val, "unit": "various"})
    for sec, x, m in [("Q3", x3, m3), ("Q4", x4, m4)]:
        for name, val, unit in zip(["T1_5", "T6", "T7", "T8_9", "speed"], x, ["C", "C", "C", "C", "cm/min"]):
            summary.append({"section": sec, "item": name, "value": val, "unit": unit})
        for k, val in m.items():
            summary.append({"section": sec, "item": k, "value": val, "unit": "various"})
    summary.append({"section": "Q4", "item": "area_cap", "value": cap, "unit": "C*s"})
    pd.DataFrame(summary).to_csv(OUT / "summary.csv", index=False)

    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
