"""Problem-specific wave-energy dynamics and independent frequency-domain baselines."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from core.ode import second_order_system
from problem_data import PHYSICAL, PhysicalParameters, WaveCase


def damping_force(relative_velocity, scale: float, exponent: float = 0.0):
    """Force mapping D(v)=scale*|v|^p*v; positive D acts against positive relative motion."""
    if scale < 0.0 or exponent < 0.0:
        raise ValueError("damping scale and exponent must be nonnegative")
    velocity = np.asarray(relative_velocity, dtype=float)
    result = float(scale) * np.abs(velocity) ** float(exponent) * velocity
    return float(result) if result.ndim == 0 else result


def heave_acceleration(
    wave: WaveCase,
    damping_scale: float,
    damping_exponent: float = 0.0,
    physical: PhysicalParameters = PHYSICAL,
) -> Callable:
    if damping_scale < 0.0 or not 0.0 <= damping_exponent <= 1.0:
        raise ValueError("invalid heave damping law")
    effective_float_mass = physical.float_mass + wave.added_mass
    oscillator_mass = physical.oscillator_mass
    spring = physical.linear_spring_stiffness
    hydrostatic = physical.hydrostatic_heave_stiffness

    def acceleration(time_s, position, velocity):
        z_float, z_oscillator = position
        v_float, v_oscillator = velocity
        relative_displacement = z_oscillator - z_float
        relative_velocity = v_oscillator - v_float
        pto = damping_force(relative_velocity, damping_scale, damping_exponent)
        float_force = (
            wave.excitation_force * np.cos(wave.omega * time_s)
            - wave.radiation_heave_damping * v_float
            - hydrostatic * z_float
            + spring * relative_displacement
            + pto
        )
        oscillator_force = -spring * relative_displacement - pto
        return np.array([float_force / effective_float_mass, oscillator_force / oscillator_mass])

    return acceleration


def heave_rhs(wave: WaveCase, damping_scale: float, damping_exponent: float = 0.0, physical: PhysicalParameters = PHYSICAL):
    return second_order_system(heave_acceleration(wave, damping_scale, damping_exponent, physical))


def coupled_acceleration(
    wave: WaveCase,
    linear_damping: float,
    rotational_damping: float,
    physical: PhysicalParameters = PHYSICAL,
) -> Callable:
    if linear_damping < 0.0 or rotational_damping < 0.0:
        raise ValueError("damping coefficients must be nonnegative")
    heave = heave_acceleration(wave, linear_damping, 0.0, physical)
    float_inertia = physical.float_pitch_inertia + wave.added_pitch_inertia
    oscillator_inertia = physical.oscillator_pitch_inertia
    torsion = physical.torsional_spring_stiffness
    restoring = physical.hydrostatic_pitch_stiffness

    def acceleration(time_s, position, velocity):
        heave_values = heave(time_s, position[:2], velocity[:2])
        theta_float, theta_oscillator = position[2:]
        omega_float, omega_oscillator = velocity[2:]
        relative_angle = theta_oscillator - theta_float
        relative_omega = omega_oscillator - omega_float
        pto_moment = rotational_damping * relative_omega
        float_moment = (
            wave.excitation_moment * np.cos(wave.omega * time_s)
            - wave.radiation_pitch_damping * omega_float
            - restoring * theta_float
            + torsion * relative_angle
            + pto_moment
        )
        oscillator_moment = -torsion * relative_angle - pto_moment
        return np.array(
            [
                heave_values[0],
                heave_values[1],
                float_moment / float_inertia,
                oscillator_moment / oscillator_inertia,
            ]
        )

    return acceleration


def pitch_acceleration(wave: WaveCase, rotational_damping: float, physical: PhysicalParameters = PHYSICAL) -> Callable:
    if rotational_damping < 0.0:
        raise ValueError("rotational damping must be nonnegative")
    float_inertia = physical.float_pitch_inertia + wave.added_pitch_inertia
    oscillator_inertia = physical.oscillator_pitch_inertia
    torsion = physical.torsional_spring_stiffness
    restoring = physical.hydrostatic_pitch_stiffness

    def acceleration(time_s, position, velocity):
        theta_float, theta_oscillator = position
        omega_float, omega_oscillator = velocity
        relative_angle = theta_oscillator - theta_float
        relative_omega = omega_oscillator - omega_float
        pto_moment = rotational_damping * relative_omega
        return np.array(
            [
                (
                    wave.excitation_moment * np.cos(wave.omega * time_s)
                    - wave.radiation_pitch_damping * omega_float
                    - restoring * theta_float
                    + torsion * relative_angle
                    + pto_moment
                )
                / float_inertia,
                (-torsion * relative_angle - pto_moment) / oscillator_inertia,
            ]
        )

    return acceleration


def pitch_rhs(wave: WaveCase, rotational_damping: float, physical: PhysicalParameters = PHYSICAL):
    return second_order_system(pitch_acceleration(wave, rotational_damping, physical))


def coupled_rhs(wave: WaveCase, linear_damping: float, rotational_damping: float, physical: PhysicalParameters = PHYSICAL):
    """First-order small-angle block model, retained as an independent baseline."""
    return second_order_system(coupled_acceleration(wave, linear_damping, rotational_damping, physical))


def nonlinear_coupled_acceleration(
    wave: WaveCase,
    linear_damping: float,
    rotational_damping: float,
    physical: PhysicalParameters = PHYSICAL,
    *,
    float_inertia_override: float | None = None,
) -> Callable:
    """Lagrange mass-matrix model in q=[x_rel,z_float,theta_float,theta_axis].

    The oscillator centre is at r=r_eq+x_rel along the rotating shaft. The
    Coriolis term is -2*m*r*x_dot*theta_dot, including the required lever arm.
    """
    if linear_damping < 0.0 or rotational_damping < 0.0:
        raise ValueError("damping coefficients must be nonnegative")
    mass = physical.oscillator_mass
    float_mass = physical.float_mass + wave.added_mass
    float_inertia = (physical.float_pitch_inertia if float_inertia_override is None else float(float_inertia_override)) + wave.added_pitch_inertia
    if float_inertia <= 0.0:
        raise ValueError("float pitch inertia must be positive")
    oscillator_centroid_inertia = physical.oscillator_centroid_pitch_inertia
    spring = physical.linear_spring_stiffness
    torsion = physical.torsional_spring_stiffness
    heave_restoring = physical.hydrostatic_heave_stiffness
    pitch_restoring = physical.hydrostatic_pitch_stiffness
    equilibrium_radius = physical.oscillator_axis_distance

    def acceleration(time_s, position, velocity):
        relative_displacement, float_heave, theta_float, theta_axis = position
        relative_velocity, float_velocity, omega_float, omega_axis = velocity
        radius = equilibrium_radius + relative_displacement
        if radius <= 0.05:
            raise ValueError("oscillator centre crossed the pitch axis")
        cosine = np.cos(theta_axis)
        sine = np.sin(theta_axis)
        relative_angle = theta_axis - theta_float
        relative_omega = omega_axis - omega_float
        pto_axial = spring * relative_displacement + linear_damping * relative_velocity

        matrix = np.array(
            [
                [mass, mass * cosine, 0.0, 0.0],
                [mass * cosine, float_mass + mass, 0.0, -mass * radius * sine],
                [0.0, 0.0, float_inertia, 0.0],
                [0.0, -mass * radius * sine, 0.0, oscillator_centroid_inertia + mass * radius**2],
            ],
            dtype=float,
        )
        right = np.array(
            [
                mass * physical.gravity * (1.0 - cosine)
                + mass * radius * omega_axis**2
                - pto_axial,
                wave.excitation_force * np.cos(wave.omega * time_s)
                - wave.radiation_heave_damping * float_velocity
                - heave_restoring * float_heave
                + 2.0 * mass * sine * relative_velocity * omega_axis
                + mass * radius * cosine * omega_axis**2,
                torsion * relative_angle
                + rotational_damping * relative_omega
                + wave.excitation_moment * np.cos(wave.omega * time_s)
                - wave.radiation_pitch_damping * omega_float
                - pitch_restoring * theta_float,
                mass * physical.gravity * radius * sine
                - mass * physical.gravity * equilibrium_radius * theta_axis
                - 2.0 * mass * radius * relative_velocity * omega_axis
                - torsion * relative_angle
                - rotational_damping * relative_omega,
            ],
            dtype=float,
        )
        return np.linalg.solve(matrix, right)

    return acceleration


def nonlinear_coupled_rhs(
    wave: WaveCase,
    linear_damping: float,
    rotational_damping: float,
    physical: PhysicalParameters = PHYSICAL,
    *,
    float_inertia_override: float | None = None,
):
    return second_order_system(
        nonlinear_coupled_acceleration(
            wave,
            linear_damping,
            rotational_damping,
            physical,
            float_inertia_override=float_inertia_override,
        )
    )


def nonlinear_observables(state, physical: PhysicalParameters = PHYSICAL) -> np.ndarray:
    """Convert nonlinear generalized states to official absolute heave/pitch columns."""
    values = np.asarray(state, float)
    if values.shape[0] != 8:
        raise ValueError("nonlinear state order must have eight rows")
    x_rel, z_float, theta_float, theta_axis, x_dot, v_float, omega_float, omega_axis = values
    radius = physical.oscillator_axis_distance + x_rel
    z_oscillator = z_float + radius * np.cos(theta_axis) - physical.oscillator_axis_distance
    v_oscillator = v_float + x_dot * np.cos(theta_axis) - radius * np.sin(theta_axis) * omega_axis
    return np.vstack(
        [
            z_float,
            z_oscillator,
            theta_float,
            theta_axis,
            v_float,
            v_oscillator,
            omega_float,
            omega_axis,
        ]
    )


def _complex_response(mass, damping, stiffness, force, omega: float) -> np.ndarray:
    dynamic = np.asarray(stiffness, float) - omega**2 * np.asarray(mass, float) + 1j * omega * np.asarray(damping, float)
    return np.linalg.solve(dynamic, np.asarray(force, complex))


def heave_frequency_response(wave: WaveCase, damping: float, physical: PhysicalParameters = PHYSICAL) -> np.ndarray:
    """Complex displacement amplitudes Q for Re(Q exp(i*omega*t))."""
    mass = np.diag([physical.float_mass + wave.added_mass, physical.oscillator_mass])
    damping_matrix = np.array(
        [[wave.radiation_heave_damping + damping, -damping], [-damping, damping]], dtype=float
    )
    spring = physical.linear_spring_stiffness
    stiffness = np.array(
        [[physical.hydrostatic_heave_stiffness + spring, -spring], [-spring, spring]], dtype=float
    )
    return _complex_response(mass, damping_matrix, stiffness, [wave.excitation_force, 0.0], wave.omega)


def pitch_frequency_response(wave: WaveCase, damping: float, physical: PhysicalParameters = PHYSICAL) -> np.ndarray:
    mass = np.diag(
        [physical.float_pitch_inertia + wave.added_pitch_inertia, physical.oscillator_pitch_inertia]
    )
    damping_matrix = np.array(
        [[wave.radiation_pitch_damping + damping, -damping], [-damping, damping]], dtype=float
    )
    torsion = physical.torsional_spring_stiffness
    stiffness = np.array(
        [[physical.hydrostatic_pitch_stiffness + torsion, -torsion], [-torsion, torsion]], dtype=float
    )
    return _complex_response(mass, damping_matrix, stiffness, [wave.excitation_moment, 0.0], wave.omega)


def harmonic_state(time_s, omega: float, displacement_amplitude: np.ndarray) -> np.ndarray:
    time = np.asarray(time_s, float)
    phase = np.exp(1j * omega * time)
    q = np.real(np.asarray(displacement_amplitude)[:, None] * phase[None, :])
    v = np.real(1j * omega * np.asarray(displacement_amplitude)[:, None] * phase[None, :])
    return np.vstack([q, v])


def linear_heave_average_power(wave: WaveCase, damping: float, physical: PhysicalParameters = PHYSICAL) -> float:
    response = heave_frequency_response(wave, damping, physical)
    relative_velocity_amplitude = 1j * wave.omega * (response[1] - response[0])
    return 0.5 * damping * abs(relative_velocity_amplitude) ** 2


def linear_pitch_average_power(wave: WaveCase, damping: float, physical: PhysicalParameters = PHYSICAL) -> float:
    response = pitch_frequency_response(wave, damping, physical)
    relative_omega_amplitude = 1j * wave.omega * (response[1] - response[0])
    return 0.5 * damping * abs(relative_omega_amplitude) ** 2
