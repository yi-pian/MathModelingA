"""Generate deterministic Phase 2 benchmark and stress-test data.

This script creates numeric CSV inputs only.  All figure rendering is performed
later by Origin through Origin MCP.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RNG = random.Random(20260831)


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    path = ROOT / name
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def scatter_fit() -> None:
    rows: list[dict[str, object]] = []
    for i in range(61):
        x = i / 6
        fit = 1.5 + 0.62 * x + 0.17 * x * x
        sigma = 0.34 + 0.025 * x
        noise = 0.28 * math.sin(2.3 * x) + 0.18 * math.cos(4.7 * x)
        noise += RNG.gauss(0, sigma * 0.48)
        if i == 46:
            noise += 2.65
        observed = fit + noise
        half = 1.96 * sigma / math.sqrt(7.5)
        rows.append(
            {
                "x": f"{x:.6f}",
                "observed": f"{observed:.6f}",
                "fit": f"{fit:.6f}",
                "ci_lower": f"{fit - half:.6f}",
                "ci_upper": f"{fit + half:.6f}",
                "residual": f"{observed - fit:.6f}",
                "outlier": f"{observed:.6f}" if i == 46 else "",
            }
        )
    write_csv(
        "phase2_scatter_fit.csv",
        ["x", "ci_lower", "ci_upper", "observed", "fit", "residual", "outlier"],
        rows,
    )
    flagged = rows[46]
    write_csv(
        "phase2_scatter_outlier.csv",
        ["x", "observed", "residual"],
        [{"x": flagged["x"], "observed": flagged["observed"], "residual": flagged["residual"]}],
    )

    stress: list[dict[str, object]] = []
    for i in range(601):
        x = 30 * i / 600
        fit = 2.2 + 0.48 * x + 0.019 * x * x
        sigma = 0.45 + 0.055 * x
        observed = fit + RNG.gauss(0, sigma) + 0.28 * math.sin(1.7 * x)
        is_outlier = i in {8, 159, 420, 592}
        if is_outlier:
            observed += (3.8 + 0.05 * x) * (1 if i % 2 == 0 else -1)
        stress.append(
            {
                "exposure_duration_with_extended_label_s": f"{x:.6f}",
                "observed": f"{observed:.6f}",
                "fit": f"{fit:.6f}",
                "outlier": f"{observed:.6f}" if is_outlier else "",
            }
        )
    write_csv(
        "phase2_scatter_stress.csv",
        ["exposure_duration_with_extended_label_s", "observed", "fit", "outlier"],
        stress,
    )
    write_csv(
        "phase2_scatter_stress_outliers.csv",
        ["exposure_duration_with_extended_label_s", "observed"],
        [
            {
                "exposure_duration_with_extended_label_s": row["exposure_duration_with_extended_label_s"],
                "observed": row["outlier"],
            }
            for row in stress if row["outlier"]
        ],
    )


def convergence() -> None:
    rows: list[dict[str, object]] = []
    for iteration in range(121):
        best = 0.008 + 0.84 * math.exp(-iteration / 20) + 0.08 * math.exp(-iteration / 4.5)
        mean = best + 0.018 + 0.15 * math.exp(-iteration / 34)
        mean += 0.006 * math.exp(-iteration / 80) * math.sin(iteration / 3.2)
        rows.append(
            {
                "iteration": iteration,
                "best_objective": f"{best:.8f}",
                "population_mean": f"{mean:.8f}",
                "final_best": f"{best:.8f}" if iteration == 120 else "",
            }
        )
    write_csv(
        "phase2_convergence.csv",
        ["iteration", "best_objective", "population_mean", "final_best"],
        rows,
    )
    write_csv(
        "phase2_convergence_final.csv",
        ["iteration", "best_objective"],
        [{"iteration": 120, "best_objective": rows[-1]["best_objective"]}],
    )

    stress: list[dict[str, object]] = []
    for iteration in range(0, 2001, 5):
        best = 1.4e3 * math.exp(-iteration / 155) + 8.0e-7
        best *= 1 + 0.025 * math.exp(-iteration / 600) * math.sin(iteration / 31)
        mean = best * (1.65 + 0.10 * math.sin(iteration / 53)) + 2.5e-5
        stress.append(
            {
                "iteration": iteration,
                "best_objective": f"{best:.12g}",
                "population_mean": f"{mean:.12g}",
                "final_best": f"{best:.12g}" if iteration == 2000 else "",
                "log10_best_objective": f"{math.log10(best):.9f}",
                "log10_population_mean": f"{math.log10(mean):.9f}",
            }
        )
    write_csv(
        "phase2_convergence_stress.csv",
        [
            "iteration", "best_objective", "population_mean", "final_best",
            "log10_best_objective", "log10_population_mean",
        ],
        stress,
    )
    write_csv(
        "phase2_convergence_stress_final.csv",
        ["iteration", "log10_best_objective"],
        [{"iteration": 2000, "log10_best_objective": stress[-1]["log10_best_objective"]}],
    )


def multipanel() -> None:
    rows: list[dict[str, object]] = []
    for i in range(81):
        t = i * 0.25
        disp_model = 8.0 * (1 - math.exp(-t / 5.5)) + 0.35 * math.sin(t / 2.7)
        disp_obs = disp_model + 0.16 * math.sin(1.6 * t)
        vel_model = 1.45 * math.exp(-t / 6.2) + 0.18 * math.sin(t / 2.0)
        vel_obs = vel_model + 0.045 * math.cos(1.8 * t)
        power_model = 42 + 18 * math.exp(-((t - 6.5) / 3.0) ** 2) + 5 * math.sin(t / 3.4)
        power_obs = power_model + 1.2 * math.sin(1.35 * t)
        err_model = 0.62 * math.exp(-t / 4.0) + 0.028
        err_obs = err_model + 0.012 * math.sin(1.9 * t)
        rows.append(
            {
                "time_s": f"{t:.6f}",
                "displacement_observed": f"{disp_obs:.6f}",
                "displacement_model": f"{disp_model:.6f}",
                "velocity_observed": f"{vel_obs:.6f}",
                "velocity_model": f"{vel_model:.6f}",
                "power_observed": f"{power_obs:.6f}",
                "power_model": f"{power_model:.6f}",
                "error_observed": f"{err_obs:.6f}",
                "error_model": f"{err_model:.6f}",
            }
        )
    fields = list(rows[0])
    write_csv("phase2_multipanel.csv", fields, rows)

    stress: list[dict[str, object]] = []
    for i in range(181):
        t = i * 20
        u = t / 3600
        error_observed = 8e-4*math.exp(-8*u) + 8e-7 + 5e-6*math.sin(30*u)
        error_model = 8e-4*math.exp(-8*u) + 8e-7
        # The oscillatory observation can cross zero late in the run.  A
        # signed residual cannot be put on a logarithmic axis, so the stress
        # view uses log10 absolute magnitude and records that adaptation.
        stress.append(
            {
                "elapsed_operation_time_seconds": t,
                "displacement_observed": f"{(1.2e-3 * (1 - math.exp(-5*u)) + 4e-5*math.sin(20*u)):.10g}",
                "displacement_model": f"{(1.2e-3 * (1 - math.exp(-5*u))):.10g}",
                "velocity_observed": f"{(120*math.exp(-3*u) + 2.5*math.sin(25*u)):.10g}",
                "velocity_model": f"{(120*math.exp(-3*u)):.10g}",
                "power_observed": f"{(1.2e4 + 7.0e3*math.exp(-((u-0.72)/0.06)**2) + 200*math.sin(20*u)):.10g}",
                "power_model": f"{(1.2e4 + 7.0e3*math.exp(-((u-0.72)/0.06)**2)):.10g}",
                "error_observed": f"{error_observed:.10g}",
                "error_model": f"{error_model:.10g}",
                "log10_abs_error_observed": f"{math.log10(max(abs(error_observed), 1e-8)):.9f}",
                "log10_abs_error_model": f"{math.log10(max(abs(error_model), 1e-8)):.9f}",
            }
        )
    write_csv("phase2_multipanel_stress.csv", list(stress[0]), stress)


def heatmap_stress() -> None:
    rows: list[dict[str, object]] = []
    for ti in range(181):
        t = float(ti)
        for xi in range(121):
            x = 6 * xi / 120
            moving = 42 * math.exp(-((x - (1.0 + 0.022 * t)) / 0.52) ** 2)
            boundary = 88 * math.exp(-((x - 5.75) / 0.24) ** 2 - ((t - 146) / 21) ** 2)
            cooling = -7 * math.exp(-((x - 0.3) / 0.42) ** 2) * (1 - math.exp(-t / 45))
            temperature = 23 + 0.052 * t + moving + boundary + cooling
            rows.append(
                {
                    "position_along_extended_domain_m": f"{x:.6f}",
                    "elapsed_heating_time_s": f"{t:.6f}",
                    "temperature_c": f"{temperature:.6f}",
                }
            )
    write_csv(
        "phase2_heatmap_stress.csv",
        ["position_along_extended_domain_m", "elapsed_heating_time_s", "temperature_c"],
        rows,
    )


def surface_stress() -> None:
    rows: list[dict[str, object]] = []
    best = None
    for yi in range(61):
        y = -3 + 6 * yi / 60
        for xi in range(61):
            x = -3 + 6 * xi / 60
            z = 0.06 + 2.2 * (x + 2.72) ** 2 + 0.85 * (y - 2.58) ** 2
            z += 0.28 * (x + 2.72) * (y - 2.58) + 0.015 * (x**2 + y**2) ** 2
            row = {"x": f"{x:.6f}", "y": f"{y:.6f}", "objective": f"{z:.8f}"}
            rows.append(row)
            if best is None or z < best[2]:
                best = (x, y, z)
    write_csv("phase2_surface_stress.csv", ["x", "y", "objective"], rows)
    assert best is not None
    write_csv(
        "phase2_surface_stress_optimum.csv",
        ["x", "y", "objective"],
        [{"x": f"{best[0]:.6f}", "y": f"{best[1]:.6f}", "objective": f"{best[2]:.8f}"}],
    )


def main() -> None:
    scatter_fit()
    convergence()
    multipanel()
    heatmap_stress()
    surface_stress()
    print("Generated Phase 2 benchmark and stress-test CSV files.")


if __name__ == "__main__":
    main()
