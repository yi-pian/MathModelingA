"""End-to-end acceptance smoke test covering computation, plot, Excel and Origin."""

import sys
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.export import export_origin_table, write_excel_checked
from core.fitting import fit_curve
from core.geometry import line_sphere_intersections, rodrigues_matrix
from core.ode import solve_ode
from core.optimization import optimize_scalar
from core.plotting import plot_scatter_fit
from core.roots import solve_bracketed
from core.sensitivity import one_parameter_sensitivity
from core.validation import ValidationReport


def main():
    output = ROOT / "results" / "smoke"; output.mkdir(parents=True, exist_ok=True)
    root = solve_bracketed(lambda x: x**2 - 4, (0, 3))
    ode = solve_ode(lambda t, y: y, (0, 1), [1], sample_times=np.linspace(0, 1, 21), method="DOP853")
    rotation = rodrigues_matrix([0, 0, 1], np.pi / 2)
    intersections = line_sphere_intersections([-2, 0, 0], [1, 0, 0], [0, 0, 0], 1)
    x = np.linspace(0, 3, 20); y = 2.0 * x + 1.0
    fit = fit_curve(lambda x, a, b: a * x + b, x, y)
    optimum = optimize_scalar(lambda value: (value - 3) ** 2, bounds=(0, 6))
    sensitivity = one_parameter_sensitivity(lambda p: p["a"] * 2, {"a": 3.0}, "a")
    figure, _ = plot_scatter_fit(x, y, fit.predictions, xlabel="x (-)", ylabel="y (-)", output=output / "fit")
    plt.close(figure)
    summary = pd.DataFrame({"check": ["root", "ode_e", "fit_slope", "optimum_x", "sphere_hits"], "value": [root.root, ode.state[0, -1], fit.parameters[0], optimum.x, len(intersections)]})
    excel = write_excel_checked(output / "result.xlsx", {"Summary": summary, "Sensitivity": sensitivity}, decimals=8)
    origin = export_origin_table(output / "origin_sensitivity.xlsx", sensitivity, x_column="change_rate", metadata={"purpose": "smoke test"})
    report = ValidationReport().add("Root", root.converged and abs(root.root - 2) < 1e-10).add("ODE", ode.success and abs(ode.state[0, -1] - np.e) < 1e-7).add("3D rotation", np.allclose(rotation @ [1, 0, 0], [0, 1, 0], atol=1e-12)).add("Sphere intersections", len(intersections) == 2).add("Parameter fitting", fit.success and np.allclose(fit.parameters, [2, 1], atol=1e-9)).add("Continuous optimization", optimum.success and abs(optimum.x - 3) < 1e-6).add("Sensitivity table", len(sensitivity) == 7).add("Matplotlib outputs", all((output / f"fit.{ext}").exists() for ext in ("png", "pdf", "svg"))).add("Excel output", excel["valid"]).add("Origin output", origin["valid"])
    (output / "validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps({"passed": report.passed, "checks": [item.__dict__ for item in report.checks]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report.render())
    if not report.passed: raise RuntimeError("smoke test failed")


if __name__ == "__main__": main()
