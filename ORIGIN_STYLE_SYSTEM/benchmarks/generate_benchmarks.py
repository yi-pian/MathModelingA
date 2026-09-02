"""Generate deterministic mathematical-modeling figure benchmark tables."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def write_rows(name: str, fieldnames: list[str], rows: list[dict[str, float | int | str]]) -> None:
    with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rounded(value: float) -> float:
    return round(value, 6)


def single_peak() -> None:
    rows = []
    for i in range(49):
        t = 0.5 * i
        response = 12.0 + 72.0 * (t / 7.0) ** 2 * math.exp(2.0 * (1.0 - t / 7.0))
        rows.append({"time_h": t, "response_index": rounded(response)})
    write_rows("single_peak_time_curve.csv", ["time_h", "response_index"], rows)
    peak = max(rows, key=lambda row: float(row["response_index"]))
    write_rows("single_peak_point.csv", ["time_h", "response_index"], [peak])


def multi_solution() -> None:
    rows = []
    for i in range(49):
        t = 0.5 * i
        baseline = 28.0 + 48.0 * (1.0 - math.exp(-t / 8.8))
        conservative = 27.0 + 56.0 * (1.0 - math.exp(-t / 7.5)) - 1.5 * math.exp(-((t - 16.0) / 3.8) ** 2)
        aggressive = 25.0 + 65.0 * (1.0 - math.exp(-t / 4.2)) - 0.030 * t**2
        proposed = 26.0 + 68.0 * (1.0 - math.exp(-t / 5.6)) + 3.2 * math.exp(-((t - 12.0) / 4.0) ** 2)
        rows.append(
            {
                "time_h": t,
                "baseline": rounded(baseline),
                "conservative": rounded(conservative),
                "aggressive": rounded(aggressive),
                "proposed": rounded(proposed),
            }
        )
    write_rows(
        "multi_solution_time_curves.csv",
        ["time_h", "baseline", "conservative", "aggressive", "proposed"],
        rows,
    )


def scatter_fit() -> None:
    rows = []
    for i in range(41):
        x = 0.25 * i
        y_true = 1.5 + 0.8 * x + 0.15 * x**2
        deviation = 0.55 * math.sin(2.2 * x) + 0.22 * math.cos(5.1 * x)
        rows.append({"x": x, "observed_y": rounded(y_true + deviation), "quadratic_truth": rounded(y_true)})
    write_rows("scatter_plus_fit.csv", ["x", "observed_y", "quadratic_truth"], rows)


def sensitivity() -> None:
    rows = []
    for i in range(17):
        p = -20.0 + 2.5 * i
        q = p / 20.0
        rows.append(
            {
                "perturbation_pct": p,
                "demand": rounded(14.0 * q + 5.0 * q**2),
                "capacity": rounded(-9.0 * q + 2.5 * q**3),
                "unit_cost": rounded(20.0 * q + 3.5 * q**2),
                "efficiency": rounded(-6.0 * q - 2.0 * q**2),
            }
        )
    write_rows(
        "single_parameter_sensitivity.csv",
        ["perturbation_pct", "demand", "capacity", "unit_cost", "efficiency"],
        rows,
    )


def objective_surface() -> None:
    rows = []
    optimum: dict[str, float] | None = None
    for ix in range(41):
        x = -3.0 + 0.15 * ix
        for iy in range(41):
            y = -3.0 + 0.15 * iy
            z = (x - 0.8) ** 2 + 1.4 * (y + 0.6) ** 2 + 0.18 * math.sin(3.0 * x) * math.cos(2.0 * y)
            row = {"x": rounded(x), "y": rounded(y), "objective": rounded(z)}
            rows.append(row)
            if optimum is None or z < optimum["objective"]:
                optimum = row
    write_rows("two_parameter_objective.csv", ["x", "y", "objective"], rows)
    assert optimum is not None
    write_rows("two_parameter_optimum.csv", ["x", "y", "objective"], [optimum])


def temperature_field() -> None:
    rows = []
    for it in range(41):
        t = 0.25 * it
        for ix in range(41):
            x = 0.025 * ix
            center = 0.25 + 0.04 * t
            width = 0.020 + 0.003 * t
            pulse = 35.0 * math.exp(-((x - center) ** 2) / width) * math.exp(-0.05 * t)
            boundary = 4.0 * math.sin(math.pi * x) * math.exp(-0.18 * t)
            rows.append({"position_m": rounded(x), "time_s": rounded(t), "temperature_c": rounded(20.0 + pulse + boundary)})
    write_rows("spatiotemporal_temperature.csv", ["position_m", "time_s", "temperature_c"], rows)


def convergence() -> None:
    rows = []
    for k in range(101):
        baseline = 0.42 * math.exp(-0.045 * k) + 0.018 / (k + 1.0)
        accelerated = 0.42 * math.exp(-0.085 * k) + 0.010 / (k + 1.0)
        adaptive = 0.42 * math.exp(-0.070 * k) * (1.0 + 0.08 * math.sin(0.32 * k)) + 0.007
        proposed = 0.42 * math.exp(-0.105 * k) + 0.0035
        rows.append(
            {
                "iteration": k,
                "baseline_gap": rounded(baseline),
                "accelerated_gap": rounded(accelerated),
                "adaptive_gap": rounded(adaptive),
                "proposed_gap": rounded(proposed),
            }
        )
    write_rows(
        "optimization_convergence.csv",
        ["iteration", "baseline_gap", "accelerated_gap", "adaptive_gap", "proposed_gap"],
        rows,
    )


def solution_comparison() -> None:
    values = {
        "Economic benefit": (68, 82, 88),
        "Reliability": (91, 76, 89),
        "Low emissions": (61, 84, 92),
        "Scalability": (73, 88, 90),
        "Robustness": (86, 79, 91),
        "Implementation ease": (94, 70, 83),
    }
    rows = [
        {"criterion": criterion, "baseline": vals[0], "alternative": vals[1], "proposed": vals[2]}
        for criterion, vals in values.items()
    ]
    write_rows("three_solution_comparison.csv", ["criterion", "baseline", "alternative", "proposed"], rows)


def main() -> None:
    single_peak()
    multi_solution()
    scatter_fit()
    sensitivity()
    objective_surface()
    temperature_field()
    convergence()
    solution_comparison()


if __name__ == "__main__":
    main()
