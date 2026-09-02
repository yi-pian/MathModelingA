"""Isolate 2025A flat imports from other historical problem directories."""

from pathlib import Path
import sys

PROBLEM = Path(__file__).resolve().parents[1]
for name in ("problem_data", "common", "q1", "q2", "q3", "q4", "q5", "deliverables"):
    sys.modules.pop(name, None)
sys.path.insert(0, str(PROBLEM))
