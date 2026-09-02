from pathlib import Path
import sys

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
PROBLEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROBLEM))

from core.integration import integrate_samples
from physics import harmonic_state, heave_frequency_response, heave_rhs, linear_heave_average_power
from power import heave_power
from problem_data import wave_case
from steady_state import solve_periodic_orbit


def test_shooting_matches_frequency_domain_for_linear_heave():
    wave = wave_case(2)
    damping = 25000.0
    response = heave_frequency_response(wave, damping)
    guess = harmonic_state([0.0], wave.omega, response)[:, 0]
    orbit = solve_periodic_orbit(heave_rhs(wave, damping), wave.omega, guess, samples_per_cycle=128, rtol=1e-10, atol=1e-12)
    relative_velocity = orbit.ode.state[3] - orbit.ode.state[2]
    numerical = integrate_samples(orbit.ode.time, heave_power(relative_velocity, damping), method="simpson") / orbit.period
    analytical = linear_heave_average_power(wave, damping)
    assert orbit.periodic_residual < 1e-8
    assert abs(numerical - analytical) / analytical < 1e-7

