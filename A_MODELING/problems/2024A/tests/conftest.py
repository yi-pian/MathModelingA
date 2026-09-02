"""Isolate 2024A flat imports from other historical problem directories."""

from pathlib import Path
import sys

PROBLEM = Path(__file__).resolve().parents[1]
for name in ("common", "deliverables", "q1", "q2", "q3", "q4", "q5"):
    sys.modules.pop(name, None)
sys.path.insert(0, str(PROBLEM))
