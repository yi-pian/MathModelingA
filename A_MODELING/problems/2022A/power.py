"""PTO power definitions and integer-cycle integration checks."""

from __future__ import annotations

import numpy as np

from core.integration import integrate_samples
from steady_state import PeriodicSimulation


def heave_power(relative_velocity, damping_scale: float, exponent: float = 0.0):
    velocity = np.asarray(relative_velocity, float)
    result = float(damping_scale) * np.abs(velocity) ** (float(exponent) + 2.0)
    return float(result) if result.ndim == 0 else result


def rotational_power(relative_angular_velocity, damping: float):
    velocity = np.asarray(relative_angular_velocity, float)
    result = float(damping) * velocity**2
    return float(result) if result.ndim == 0 else result


def average_last_cycles(time, values, samples_per_cycle: int, cycles: int, *, method="simpson") -> float:
    if cycles < 1:
        raise ValueError("cycles must be positive")
    count = cycles * samples_per_cycle + 1
    if count > len(time):
        raise ValueError("not enough samples for requested averaging cycles")
    selected_time = np.asarray(time[-count:], float)
    selected_values = np.asarray(values[-count:], float)
    duration = selected_time[-1] - selected_time[0]
    return integrate_samples(selected_time, selected_values, method=method) / duration


def heave_power_summary(
    simulation: PeriodicSimulation,
    damping_scale: float,
    exponent: float = 0.0,
    *,
    windows=(5, 10, 20),
) -> dict:
    relative_velocity = simulation.ode.state[3] - simulation.ode.state[2]
    instantaneous = heave_power(relative_velocity, damping_scale, exponent)
    means = {
        f"{cycles}_cycles_simpson": average_last_cycles(
            simulation.ode.time, instantaneous, simulation.samples_per_cycle, cycles, method="simpson"
        )
        for cycles in windows
    }
    means.update(
        {
            f"{cycles}_cycles_trapezoid": average_last_cycles(
                simulation.ode.time, instantaneous, simulation.samples_per_cycle, cycles, method="trapezoid"
            )
            for cycles in windows
        }
    )
    return {"instantaneous": instantaneous, "means": means, "relative_velocity": relative_velocity}


def coupled_power_summary(
    simulation: PeriodicSimulation,
    linear_damping: float,
    rotational_damping: float,
    *,
    windows=(5, 10, 20),
) -> dict:
    relative_velocity = simulation.ode.state[5] - simulation.ode.state[4]
    relative_omega = simulation.ode.state[7] - simulation.ode.state[6]
    heave = heave_power(relative_velocity, linear_damping)
    rotation = rotational_power(relative_omega, rotational_damping)
    total = heave + rotation
    result = {"heave": heave, "rotation": rotation, "total": total, "means": {}}
    for cycles in windows:
        for method in ("simpson", "trapezoid"):
            for name, values in (("heave", heave), ("rotation", rotation), ("total", total)):
                result["means"][f"{name}_{cycles}_cycles_{method}"] = average_last_cycles(
                    simulation.ode.time, values, simulation.samples_per_cycle, cycles, method=method
                )
    return result


def nonlinear_coupled_power_summary(
    simulation: PeriodicSimulation,
    linear_damping: float,
    rotational_damping: float,
    *,
    windows=(5, 10, 20),
) -> dict:
    """Power for generalized state [x,z,theta_f,theta_o,x_dot,z_dot,...]."""
    axial_velocity = simulation.ode.state[4]
    relative_omega = simulation.ode.state[7] - simulation.ode.state[6]
    heave = heave_power(axial_velocity, linear_damping)
    rotation = rotational_power(relative_omega, rotational_damping)
    total = heave + rotation
    result = {"heave": heave, "rotation": rotation, "total": total, "means": {}}
    for cycles in windows:
        for method in ("simpson", "trapezoid"):
            for name, values in (("heave", heave), ("rotation", rotation), ("total", total)):
                result["means"][f"{name}_{cycles}_cycles_{method}"] = average_last_cycles(
                    simulation.ode.time, values, simulation.samples_per_cycle, cycles, method=method
                )
    return result
