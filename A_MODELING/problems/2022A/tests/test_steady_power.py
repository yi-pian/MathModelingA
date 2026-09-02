from pathlib import Path
import sys

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
PROBLEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROBLEM))

from power import average_last_cycles
from steady_state import cycle_change_metrics, detect_steady_cycle, periodic_sample_times


def test_phase_grid_and_steady_detector():
    samples = 32
    cycles = 30
    times = periodic_sample_times(2.0, cycles, samples)
    transient = np.exp(-times / 3.0) + np.sin(np.pi * times)
    metrics = cycle_change_metrics(transient[None, :], cycles, samples)
    cycle = detect_steady_cycle(metrics, tolerance=1e-3, required_consecutive=2, reserve_cycles=5)
    assert 1 < cycle < cycles - 5


def test_integer_cycle_power_average_and_methods():
    samples = 64
    cycles = 20
    time = periodic_sample_times(2.0, cycles, samples)
    values = 3.0 + 2.0 * np.cos(np.pi * time)
    simpson = average_last_cycles(time, values, samples, 10, method="simpson")
    trapezoid = average_last_cycles(time, values, samples, 10, method="trapezoid")
    assert abs(simpson - 3.0) < 1e-12
    assert abs(trapezoid - 3.0) < 1e-12

