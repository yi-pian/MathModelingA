import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

import numpy as np
from core.ode import second_order_system, solve_ode


def main():
    solution = solve_ode(second_order_system(lambda t, q, v: -q), (0, 2 * np.pi), [1, 0], sample_times=np.linspace(0, 2 * np.pi, 101), method="DOP853")
    print({"success": solution.success, "final_state": solution.state[:, -1].tolist()})
    if not np.allclose(solution.state[:, -1], [1, 0], atol=1e-7): raise RuntimeError("analytic check failed")


if __name__ == "__main__": main()
