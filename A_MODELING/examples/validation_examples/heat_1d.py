"""Grid-convergence demonstration for the reusable heat-equation template."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from templates.pde_heat_1d_template import solve_heat_1d


def main():
    rows = []
    for nx in (21, 41, 81, 161):
        _, _, _, metrics = solve_heat_1d(nx=nx)
        rows.append((nx, metrics["dx"], metrics["dt"], metrics["max_error"]))
    orders = [None] + [__import__("math").log(rows[i - 1][3] / rows[i][3], 2) for i in range(1, len(rows))]
    for row, order in zip(rows, orders): print({"nx": row[0], "dx": row[1], "dt": row[2], "max_error": row[3], "observed_order": order})
    if rows[-1][3] >= rows[0][3] or min(value for value in orders[2:] if value is not None) < 1.5: raise RuntimeError("grid convergence not demonstrated")


if __name__ == "__main__": main()

