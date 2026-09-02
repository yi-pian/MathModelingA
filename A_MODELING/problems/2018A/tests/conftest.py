"""Keep flat 2018A imports isolated from other year directories."""

from pathlib import Path
import sys

PROBLEM = Path(__file__).resolve().parents[1]
for name in ("common", "calibration", "q1", "q2", "q3", "deliverables", "validation_2018a"):
    sys.modules.pop(name, None)
sys.path.insert(0, str(PROBLEM))
