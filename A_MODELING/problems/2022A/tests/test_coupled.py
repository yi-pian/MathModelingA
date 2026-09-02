from dataclasses import replace
from pathlib import Path
import sys

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
PROBLEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROBLEM))

from core.ode import solve_ode
from core.integration import integrate_samples
from physics import (
    coupled_rhs,
    harmonic_state,
    heave_frequency_response,
    heave_rhs,
    nonlinear_coupled_rhs,
    nonlinear_observables,
    pitch_acceleration,
    pitch_frequency_response,
    pitch_rhs,
)
from power import heave_power, rotational_power
from problem_data import wave_case
from steady_state import solve_periodic_orbit


def test_coupled_state_order_matches_independent_blocks():
    wave = wave_case(3)
    time = np.linspace(0.0, 12.0, 241)
    full = solve_ode(coupled_rhs(wave, 10000.0, 1000.0), (0.0, 12.0), np.zeros(8), sample_times=time, method="DOP853", rtol=1e-10, atol=1e-12)
    heave = solve_ode(heave_rhs(wave, 10000.0), (0.0, 12.0), np.zeros(4), sample_times=time, method="DOP853", rtol=1e-10, atol=1e-12)
    pitch = solve_ode(pitch_rhs(wave, 1000.0), (0.0, 12.0), np.zeros(4), sample_times=time, method="DOP853", rtol=1e-10, atol=1e-12)
    expected = np.vstack([heave.state[:2], pitch.state[:2], heave.state[2:], pitch.state[2:]])
    assert np.max(np.abs(full.state - expected)) < 1e-8


def test_zero_pitch_forcing_degenerates_to_q1_style_heave():
    wave = replace(wave_case(3), excitation_moment=0.0)
    time = np.linspace(0.0, 10.0, 201)
    full = solve_ode(coupled_rhs(wave, 10000.0, 1000.0), (0.0, 10.0), np.zeros(8), sample_times=time, method="DOP853", rtol=1e-11, atol=1e-13, max_step=0.02)
    heave = solve_ode(heave_rhs(wave, 10000.0), (0.0, 10.0), np.zeros(4), sample_times=time, method="DOP853", rtol=1e-11, atol=1e-13, max_step=0.02)
    assert np.max(np.abs(full.state[[0, 1, 4, 5]] - heave.state)) < 1e-8
    assert np.max(np.abs(full.state[[2, 3, 6, 7]])) == 0.0


def test_pitch_forcing_uses_radians_without_degree_conversion():
    wave = wave_case(3)
    acceleration = pitch_acceleration(wave, 1000.0)
    at_zero = acceleration(0.0, np.zeros(2), np.zeros(2))[0]
    at_quarter_period = acceleration(np.pi / (2.0 * wave.omega), np.zeros(2), np.zeros(2))[0]
    assert at_zero > 0.0
    assert abs(at_quarter_period) < 1e-12


def test_nonlinear_model_degenerates_to_heave_when_pitch_is_disabled():
    wave = replace(wave_case(3), excitation_moment=0.0)
    time = np.linspace(0.0, 8.0, 161)
    nonlinear = solve_ode(nonlinear_coupled_rhs(wave, 10000.0, 1000.0), (0.0, 8.0), np.zeros(8), sample_times=time, method="DOP853", rtol=1e-10, atol=1e-12, max_step=0.02)
    heave = solve_ode(heave_rhs(wave, 10000.0), (0.0, 8.0), np.zeros(4), sample_times=time, method="DOP853", rtol=1e-10, atol=1e-12, max_step=0.02)
    observed = nonlinear_observables(nonlinear.state)
    assert np.max(np.abs(observed[[0, 1, 4, 5]] - heave.state)) < 2e-8
    assert np.max(np.abs(observed[[2, 3, 6, 7]])) == 0.0


def test_nonlinear_periodic_orbit_closes_energy_balance():
    """Regression: a mixed single-body/Lagrange equation leaves an O(1 W) defect."""
    wave = wave_case(4)
    linear_damping = 50000.0
    rotational_damping = 50000.0
    heave_guess = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, linear_damping))[:, 0]
    pitch_guess = harmonic_state([0.0], wave.omega, pitch_frequency_response(wave, rotational_damping))[:, 0]
    guess = np.array(
        [
            heave_guess[1] - heave_guess[0],
            heave_guess[0],
            pitch_guess[0],
            pitch_guess[1],
            heave_guess[3] - heave_guess[2],
            heave_guess[2],
            pitch_guess[2],
            pitch_guess[3],
        ]
    )
    orbit = solve_periodic_orbit(
        nonlinear_coupled_rhs(wave, linear_damping, rotational_damping),
        wave.omega,
        guess,
        samples_per_cycle=256,
        rtol=1e-9,
        atol=1e-11,
    )
    time = orbit.ode.time
    state = orbit.ode.state
    input_power = wave.excitation_force * np.cos(wave.omega * time) * state[5]
    input_power += wave.excitation_moment * np.cos(wave.omega * time) * state[6]
    dissipated = wave.radiation_heave_damping * state[5] ** 2
    dissipated += wave.radiation_pitch_damping * state[6] ** 2
    dissipated += heave_power(state[4], linear_damping)
    dissipated += rotational_power(state[7] - state[6], rotational_damping)
    residual = integrate_samples(time, input_power - dissipated, method="simpson") / wave.period
    assert abs(residual) < 2e-4
