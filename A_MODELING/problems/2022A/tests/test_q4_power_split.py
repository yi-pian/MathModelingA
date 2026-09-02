from pathlib import Path
import sys

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
PROBLEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROBLEM))

from physics import linear_heave_average_power, linear_pitch_average_power
from problem_data import wave_case
from q4 import frequency_power


def test_q4_total_power_is_exact_sum_of_pto_channels():
    wave = wave_case(4)
    parameters = np.array([23456.0, 34567.0])
    expected = linear_heave_average_power(wave, parameters[0]) + linear_pitch_average_power(wave, parameters[1])
    assert frequency_power(parameters) == expected


def test_q4_zero_dampers_have_zero_output():
    assert frequency_power([0.0, 0.0]) == 0.0

