"""ODE workflow: RHS -> initial state -> solve -> convergence -> plot -> export."""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from core.ode import second_order_system, solve_ode, tolerance_convergence
from core.plotting import plot_multi_series

OUTPUT = ROOT / "results" / "template_ode"


def acceleration(time_s, position_m, velocity_m_s):
    return -4.0 * position_m - 0.2 * velocity_m_s


def main():
    time_s = np.linspace(0.0, 10.0, 501)
    rhs = second_order_system(acceleration)
    result = solve_ode(rhs, (time_s[0], time_s[-1]), [1.0, 0.0], sample_times=time_s, method="DOP853")
    study = tolerance_convergence(rhs, (0, 10), [1, 0], time_s, tolerances=(1e-5, 1e-7, 1e-9))
    if not result.success or study["max_differences"][-1] > 1e-5: raise RuntimeError("ODE solve/convergence failed")
    data = pd.DataFrame({"time_s": result.time, "position_m": result.state[0], "velocity_m_s": result.state[1]})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plot_multi_series(data["time_s"], {"position": data["position_m"], "velocity": data["velocity_m_s"]}, xlabel="Time (s)", ylabel="State (SI)", output=OUTPUT / "state")
    write_excel_checked(OUTPUT / "result.xlsx", {"State": data}, decimals=8)


if __name__ == "__main__": main()
