"""Data -> bounded fit -> metrics/residual -> figure -> Excel."""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from core.fitting import fit_curve
from core.plotting import plot_residual, plot_scatter_fit

OUTPUT = ROOT / "results" / "template_fitting"


def model(x, amplitude, rate):
    return amplitude * np.exp(rate * x)


def main():
    x = np.linspace(0, 2, 30); y = model(x, 3.0, 0.4)
    result = fit_curve(model, x, y, p0=[2, 0.2], bounds=([0, 0], [10, 2]))
    if not result.success or result.rmse > 1e-8: raise RuntimeError(result.message)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame({"x": x, "observed": y, "predicted": result.predictions, "residual": result.residuals})
    metrics = pd.DataFrame({"metric": ["amplitude", "rate", "RMSE", "MAE", "R2"], "value": [*result.parameters, result.rmse, result.mae, result.r2]})
    plot_scatter_fit(x, y, result.predictions, xlabel="x (-)", ylabel="response (-)", output=OUTPUT / "fit")
    plot_residual(x, result.residuals, xlabel="x (-)", output=OUTPUT / "residual")
    write_excel_checked(OUTPUT / "result.xlsx", {"Data": data, "Metrics": metrics}, decimals=10)


if __name__ == "__main__": main()
