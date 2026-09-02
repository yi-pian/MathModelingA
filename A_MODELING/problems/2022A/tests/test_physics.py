from pathlib import Path
import sys

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
PROBLEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROBLEM))

from core.ode import solve_ode
from physics import damping_force, heave_rhs, linear_heave_average_power
from power import heave_power, rotational_power
from problem_data import PHYSICAL, wave_case


def test_damping_force_zero_odd_and_opposes_motion():
    for exponent in (0.0, 0.5, 1.0):
        assert damping_force(0.0, 10000.0, exponent) == 0.0
        positive = damping_force(0.7, 10000.0, exponent)
        negative = damping_force(-0.7, 10000.0, exponent)
        assert np.isclose(negative, -positive)
        assert (-positive) * 0.7 <= 0.0


def test_power_is_even_nonnegative_and_zero_at_rest():
    velocities = np.array([-1.2, -0.3, 0.0, 0.3, 1.2])
    values = heave_power(velocities, 1234.0, 0.5)
    assert np.all(values >= 0.0)
    assert values[2] == 0.0
    assert np.allclose(values, values[::-1])
    assert np.all(rotational_power(velocities, 4321.0) >= 0.0)


def test_static_geometry_and_inertias_are_physical():
    assert 0.0 < PHYSICAL.equilibrium_spring_length < PHYSICAL.linear_spring_free_length
    assert PHYSICAL.oscillator_pitch_inertia > PHYSICAL.oscillator_centroid_pitch_inertia > 0.0
    components = PHYSICAL.float_pitch_inertia_components()
    assert np.isclose(
        components["total_kg_m2"],
        components["inertia_cylinder_side_kg_m2"]
        + components["inertia_cylinder_top_kg_m2"]
        + components["inertia_cone_side_kg_m2"],
    )


def test_zero_forcing_zero_initial_state_stays_zero():
    base = wave_case(1)
    zero_wave = type(base)(base.name, base.omega, base.added_mass, base.added_pitch_inertia, base.radiation_heave_damping, base.radiation_pitch_damping, 0.0, 0.0)
    result = solve_ode(heave_rhs(zero_wave, 10000.0), (0.0, 5.0), np.zeros(4), sample_times=np.linspace(0.0, 5.0, 51), method="DOP853")
    assert result.success
    assert np.max(np.abs(result.state)) == 0.0


def test_linear_average_power_boundaries():
    wave = wave_case(2)
    assert linear_heave_average_power(wave, 0.0) == 0.0
    assert linear_heave_average_power(wave, 10000.0) > 0.0

