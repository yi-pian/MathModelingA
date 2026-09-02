"""Phase-aligned periodic steady-state detection for the 2022A ODEs."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

import numpy as np

from core.ode import ODEResult, solve_ode
from core.roots import RootResult, solve_system


@dataclass(frozen=True)
class PeriodicSimulation:
    ode: ODEResult
    period: float
    samples_per_cycle: int
    total_cycles: int
    steady_start_cycle: int
    steady_start: float
    settling_time: float
    cycle_metrics: np.ndarray
    steady_tolerance: float


@dataclass(frozen=True)
class PeriodicOrbit:
    ode: ODEResult
    period: float
    samples_per_cycle: int
    initial_state: np.ndarray
    root_result: RootResult
    periodic_residual: float


def periodic_sample_times(period: float, cycles: int, samples_per_cycle: int) -> np.ndarray:
    if period <= 0.0 or cycles < 2 or samples_per_cycle < 8:
        raise ValueError("invalid periodic sampling configuration")
    return np.linspace(0.0, cycles * period, cycles * samples_per_cycle + 1)


def cycle_change_metrics(state: np.ndarray, cycles: int, samples_per_cycle: int, absolute_floor=1e-8) -> np.ndarray:
    values = np.asarray(state, float)
    expected = cycles * samples_per_cycle + 1
    if values.ndim != 2 or values.shape[1] != expected:
        raise ValueError("state does not match the phase-aligned cycle grid")
    metrics = []
    for current in range(1, cycles):
        previous_slice = slice((current - 1) * samples_per_cycle, current * samples_per_cycle + 1)
        current_slice = slice(current * samples_per_cycle, (current + 1) * samples_per_cycle + 1)
        previous = values[:, previous_slice]
        latest = values[:, current_slice]
        scale = np.maximum(np.maximum(np.max(np.abs(previous), axis=1), np.max(np.abs(latest), axis=1)), absolute_floor)
        metrics.append(float(np.max(np.abs(latest - previous) / scale[:, None])))
    return np.asarray(metrics)


def detect_steady_cycle(
    metrics: np.ndarray,
    *,
    tolerance: float = 2e-4,
    required_consecutive: int = 3,
    reserve_cycles: int = 20,
) -> int:
    metrics = np.asarray(metrics, float)
    if tolerance <= 0.0 or required_consecutive < 1 or reserve_cycles < 1:
        raise ValueError("invalid steady-state criterion")
    run = 0
    last_usable_comparison = len(metrics) - reserve_cycles
    for index, metric in enumerate(metrics):
        if index > last_usable_comparison:
            break
        run = run + 1 if metric <= tolerance else 0
        if run >= required_consecutive:
            current_cycle = index + 1
            return current_cycle
    raise RuntimeError("periodic steady state was not reached with the reserved averaging window")


def simulate_periodic_steady(
    rhs,
    omega: float,
    initial_state,
    *,
    total_cycles: int = 100,
    samples_per_cycle: int = 64,
    averaging_cycles: int = 20,
    steady_tolerance: float = 2e-4,
    required_consecutive: int = 3,
    method: str = "DOP853",
    rtol: float = 2e-8,
    atol: float = 2e-10,
    max_steps_per_cycle: int = 24,
) -> PeriodicSimulation:
    period = 2.0 * np.pi / float(omega)
    times = periodic_sample_times(period, total_cycles, samples_per_cycle)
    solution = solve_ode(
        rhs,
        (0.0, times[-1]),
        initial_state,
        sample_times=times,
        method=method,
        rtol=rtol,
        atol=atol,
        max_step=period / max_steps_per_cycle,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    metrics = cycle_change_metrics(solution.state, total_cycles, samples_per_cycle)
    cycle = detect_steady_cycle(
        metrics,
        tolerance=steady_tolerance,
        required_consecutive=required_consecutive,
        reserve_cycles=averaging_cycles,
    )
    return PeriodicSimulation(
        ode=solution,
        period=period,
        samples_per_cycle=samples_per_cycle,
        total_cycles=total_cycles,
        steady_start_cycle=cycle,
        steady_start=cycle * period,
        settling_time=cycle * period,
        cycle_metrics=metrics,
        steady_tolerance=steady_tolerance,
    )


def samples_for_cycles(cycles: int, samples_per_cycle: int) -> int:
    return int(ceil(cycles * samples_per_cycle)) + 1


def solve_periodic_orbit(
    rhs,
    omega: float,
    initial_guess,
    *,
    samples_per_cycle: int = 96,
    method: str = "DOP853",
    rtol: float = 2e-8,
    atol: float = 2e-10,
    max_steps_per_cycle: int = 32,
    root_tolerance: float = 2e-8,
) -> PeriodicOrbit:
    """Find the stable forced periodic orbit by the shooting condition Phi_T(y0)-y0=0."""
    period = 2.0 * np.pi / float(omega)
    guess = np.asarray(initial_guess, float)

    def residual(initial_state):
        endpoint = solve_ode(
            rhs,
            (0.0, period),
            initial_state,
            sample_times=np.array([period]),
            method=method,
            rtol=rtol,
            atol=atol,
            max_step=period / max_steps_per_cycle,
        )
        if not endpoint.success:
            raise RuntimeError(endpoint.message)
        return endpoint.state[:, -1] - np.asarray(initial_state)

    root = solve_system(
        residual,
        guess,
        residual_tol=root_tolerance,
        options={"xtol": min(1e-8, root_tolerance), "maxfev": 120},
    )
    # MINPACK can report stagnation after already reaching a physically negligible
    # closure residual. Accept by residual, not by the message alone; retry only when
    # the residual is materially too large.
    acceptable_root_residual = max(1e-7, 10.0 * root_tolerance)
    if not root.converged and root.residual > acceptable_root_residual:
        root = solve_system(
            residual,
            root.root,
            method="lm",
            residual_tol=acceptable_root_residual,
            options={"ftol": 1e-11, "xtol": 1e-11, "maxiter": 160},
        )
    if root.residual > acceptable_root_residual:
        raise RuntimeError(f"periodic shooting failed: {root.message}; residual={root.residual:g}")
    times = np.linspace(0.0, period, samples_per_cycle + 1)
    orbit = solve_ode(
        rhs,
        (0.0, period),
        root.root,
        sample_times=times,
        method=method,
        rtol=rtol,
        atol=atol,
        max_step=period / max_steps_per_cycle,
    )
    closure = float(np.max(np.abs(orbit.state[:, -1] - orbit.state[:, 0])))
    if not orbit.success or closure > max(10.0 * root_tolerance, 1e-10):
        raise RuntimeError(f"periodic orbit closure check failed: {closure:g}")
    return PeriodicOrbit(orbit, period, samples_per_cycle, np.asarray(root.root), root, closure)
