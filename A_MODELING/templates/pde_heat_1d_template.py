"""Validated explicit 1-D heat equation template; requires r=alpha*dt/dx^2 <= 0.5."""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from core.plotting import plot_multi_series

OUTPUT = ROOT / "results" / "template_pde"


def solve_heat_1d(alpha=0.1, length=1.0, final_time=0.1, nx=51, stability_ratio=0.45):
    x = np.linspace(0, length, nx); dx = x[1] - x[0]; dt_limit = 0.5 * dx**2 / alpha
    steps = int(np.ceil(final_time / (stability_ratio * dx**2 / alpha))); dt = final_time / steps; ratio = alpha * dt / dx**2
    if ratio > 0.5 + 1e-14: raise ValueError("FTCS stability condition violated")
    temperature = np.sin(np.pi * x / length); temperature[[0, -1]] = 0.0
    for _ in range(steps):
        next_temperature = temperature.copy()
        next_temperature[1:-1] = temperature[1:-1] + ratio * (temperature[2:] - 2 * temperature[1:-1] + temperature[:-2])
        next_temperature[[0, -1]] = 0.0
        temperature = next_temperature
    exact = np.sin(np.pi * x / length) * np.exp(-alpha * (np.pi / length) ** 2 * final_time)
    return x, temperature, exact, {"dx": dx, "dt": dt, "steps": steps, "ratio": ratio, "max_error": float(np.max(np.abs(temperature - exact)))}


def main():
    x, numerical, exact, metrics = solve_heat_1d()
    if metrics["ratio"] > 0.5 or metrics["max_error"] > 2e-3: raise RuntimeError(str(metrics))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame({"x_m": x, "temperature_numerical": numerical, "temperature_exact": exact})
    plot_multi_series(x, {"Numerical": numerical, "Exact": exact}, xlabel="Position (m)", ylabel="Normalized temperature (-)", output=OUTPUT / "heat")
    write_excel_checked(OUTPUT / "result.xlsx", {"Temperature": data, "Metrics": pd.DataFrame([metrics])}, decimals=10)


if __name__ == "__main__": main()
