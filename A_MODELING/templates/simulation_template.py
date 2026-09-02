"""Copy to problems/qX and replace the documented model, not the workflow."""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from core.plotting import plot_trajectory_2d
from core.validation import standard_report

OUTPUT = ROOT / "results" / "template_simulation"


def simulate(speed_m_s=20.0, angle_rad=np.deg2rad(35.0), duration_s=2.0, samples=101):
    time_s = np.linspace(0.0, duration_s, samples)
    x_m = speed_m_s * np.cos(angle_rad) * time_s
    y_m = speed_m_s * np.sin(angle_rad) * time_s - 0.5 * 9.80665 * time_s**2
    return pd.DataFrame({"time_s": time_s, "x_m": x_m, "y_m": y_m})


def main():
    data = simulate()
    report = standard_report(arrays=data.to_numpy(), time=data["time_s"].to_numpy())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "validation_report.txt").write_text(report.render(), encoding="utf-8")
    plot_trajectory_2d(data["x_m"], data["y_m"], xlabel="Horizontal position (m)", ylabel="Vertical position (m)", output=OUTPUT / "trajectory")
    write_excel_checked(OUTPUT / "result.xlsx", {"Trajectory": data}, decimals=6)
    if not report.passed: raise RuntimeError(report.render())


if __name__ == "__main__": main()
