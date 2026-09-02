"""Explicit direction, coarse search, fine solve, high-precision recheck and perturbation."""

from pathlib import Path
import sys
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import write_excel_checked
from core.optimization import coarse_to_fine, local_perturbation_check

OUTPUT = ROOT / "results" / "template_optimization"


def objective(x):
    return (x - 3.0) ** 2 + 1.0


def main():
    result, stages = coarse_to_fine(objective, (0.0, 10.0), direction="minimize")
    perturbation = local_perturbation_check(objective, result.x, direction="minimize")
    verified = objective(result.x)
    if not result.success or not perturbation["passed"] or abs(verified - result.objective) > 1e-10: raise RuntimeError("optimization validation failed")
    table = pd.DataFrame({"item": ["x", "objective", "coarse_x", "verified_objective"], "value": [result.x, result.objective, stages["coarse_x"], stages["verified_objective"]]})
    write_excel_checked(OUTPUT / "result.xlsx", {"Optimization": table}, decimals=10)


if __name__ == "__main__": main()
