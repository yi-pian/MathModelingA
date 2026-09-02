import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.optimization import coarse_to_fine


def main():
    result, details = coarse_to_fine(lambda x: (x - 3) ** 2, (0, 10))
    print({"x": result.x, "objective": result.objective, **details})
    if abs(result.x - 3) > 1e-7: raise RuntimeError("analytic optimum check failed")


if __name__ == "__main__": main()
