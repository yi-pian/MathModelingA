"""Verified solve_ivp wrappers, event support and tolerance convergence studies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class ODEResult:
    time: np.ndarray
    state: np.ndarray
    success: bool
    message: str
    nfev: int
    event_times: list[np.ndarray]
    raw: object


def solve_ode(rhs, time_span, initial_state, *, sample_times=None, method="RK45", rtol=1e-8, atol=1e-10, events=None, dense_output=False, max_step=np.inf, args=None):
    initial_state = np.atleast_1d(np.asarray(initial_state, float))
    if initial_state.ndim != 1 or not np.all(np.isfinite(initial_state)):
        raise ValueError("initial_state must be a finite one-dimensional array")
    start, stop = map(float, time_span)
    if stop <= start or rtol <= 0 or atol <= 0:
        raise ValueError("invalid time span or tolerance")
    if sample_times is not None:
        sample_times = np.asarray(sample_times, float)
        if np.any(np.diff(sample_times) <= 0) or sample_times[0] < start or sample_times[-1] > stop:
            raise ValueError("sample_times must increase strictly inside time_span")
    result = solve_ivp(rhs, (start, stop), initial_state, method=method, t_eval=sample_times, rtol=rtol, atol=atol, events=events, dense_output=dense_output, max_step=max_step, args=args)
    finite = np.all(np.isfinite(result.y))
    success = bool(result.success and finite)
    message = str(result.message) if finite else f"{result.message}; non-finite state encountered"
    return ODEResult(result.t, result.y, success, message, int(result.nfev), list(result.t_events or []), result)


def second_order_system(acceleration):
    """Convert q''=a(t,q,v) to state order [q..., v...]."""
    def rhs(time, state):
        state = np.asarray(state, float)
        if state.size % 2:
            raise ValueError("second-order state must contain equal position and velocity blocks")
        half = state.size // 2
        position, velocity = state[:half], state[half:]
        accel = np.atleast_1d(np.asarray(acceleration(time, position, velocity), float))
        if accel.shape != position.shape:
            raise ValueError("acceleration output shape must match position")
        return np.concatenate((velocity, accel))
    return rhs


def tolerance_convergence(rhs, time_span, initial_state, sample_times, *, tolerances=(1e-5, 1e-7, 1e-9), method="DOP853", atol_ratio=0.01):
    """Solve with tightening tolerances and compare successive state arrays.

    Adaptive solvers do not guarantee strictly monotone successive differences, so
    convergence is judged by whether the last change is small relative to the
    finest state scale and the penultimate requested tolerance.
    """
    if len(tolerances) < 2 or any(tol <= 0 for tol in tolerances) or any(later >= earlier for earlier, later in zip(tolerances[:-1], tolerances[1:])):
        raise ValueError("provide at least two strictly decreasing positive tolerances")
    solutions = [solve_ode(rhs, time_span, initial_state, sample_times=sample_times, method=method, rtol=tol, atol=tol * atol_ratio) for tol in tolerances]
    errors = [float(np.max(np.abs(first.state - second.state))) for first, second in zip(solutions[:-1], solutions[1:])]
    scale = max(1.0, float(np.max(np.abs(solutions[-1].state))))
    threshold = 10.0 * tolerances[-2] * scale
    return {"tolerances": list(tolerances), "solutions": solutions, "max_differences": errors, "acceptance_threshold": threshold, "convergent": bool(all(solution.success for solution in solutions) and errors[-1] <= threshold)}
