import sys
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.geometry import line_of_sight_blocked_by_sphere


def main():
    blocked = line_of_sight_blocked_by_sphere((-2, 0, 0), (2, 0, 0), (0, 0, 0), 0.5)
    print({"blocked": blocked})
    if not blocked: raise RuntimeError("expected obstruction")


if __name__ == "__main__": main()
