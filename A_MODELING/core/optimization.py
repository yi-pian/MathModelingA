"""Explicit-direction wrappers for local and global continuous optimization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import differential_evolution, minimize, minimize_scalar


@dataclass(frozen=True)
class OptimizationResult:
    x: float | np.ndarray
    objective: float
    success: bool
    message: str
    iterations: int | None
    nfev: int | None
    direction: str


def _direction(function: Callable, direction: str):
    if direction not in {"minimize", "maximize"}:
        raise ValueError("direction must be 'minimize' or 'maximize'")
    sign = 1.0 if direction == "minimize" else -1.0
    return lambda x: sign * float(function(x)), sign


def optimize_scalar(function, *, bounds=None, bracket=None, direction="minimize", method=None, **kwargs):
    wrapped, sign = _direction(function, direction)
    chosen = method or ("bounded" if bounds is not None else "brent")
    result = minimize_scalar(wrapped, bounds=bounds, bracket=bracket, method=chosen, **kwargs)
    return OptimizationResult(float(result.x), float(sign * result.fun), bool(result.success), str(result.message), getattr(result, "nit", None), getattr(result, "nfev", None), direction)


def optimize_local(function, x0, *, bounds=None, constraints=(), method="L-BFGS-B", direction="minimize", **kwargs):
    wrapped, sign = _direction(function, direction)
    result = minimize(wrapped, np.asarray(x0, float), bounds=bounds, constraints=constraints, method=method, **kwargs)
    return OptimizationResult(np.asarray(result.x), float(sign * result.fun), bool(result.success), str(result.message), getattr(result, "nit", None), getattr(result, "nfev", None), direction)


def optimize_global(function, bounds, *, direction="minimize", seed=0, polish=True, **kwargs):
    wrapped, sign = _direction(function, direction)
    result = differential_evolution(wrapped, bounds=bounds, seed=seed, polish=polish, **kwargs)
    return OptimizationResult(np.asarray(result.x), float(sign * result.fun), bool(result.success), str(result.message), getattr(result, "nit", None), getattr(result, "nfev", None), direction)


def coarse_to_fine(function, bounds, *, grid_points=101, direction="minimize", xatol=1e-10):
    """Coarse 1-D scan, bounded refinement, then direct high-precision re-evaluation."""
    low, high = map(float, bounds)
    xs = np.linspace(low, high, int(grid_points))
    values = np.array([float(function(x)) for x in xs])
    index = int(np.argmin(values) if direction == "minimize" else np.argmax(values))
    left, right = xs[max(0, index - 1)], xs[min(len(xs) - 1, index + 1)]
    refined = optimize_scalar(function, bounds=(left, right), direction=direction, options={"xatol": xatol})
    verified_value = float(function(refined.x))
    return refined, {"coarse_x": float(xs[index]), "coarse_objective": float(values[index]), "verified_objective": verified_value}


def local_perturbation_check(function, x, *, relative_step=1e-5, direction="minimize"):
    point = np.atleast_1d(np.asarray(x, float))
    baseline = float(function(point if np.ndim(x) else point[0]))
    samples = []
    for index in range(point.size):
        step = relative_step * max(1.0, abs(point[index]))
        for sign in (-1.0, 1.0):
            candidate = point.copy()
            candidate[index] += sign * step
            value = float(function(candidate if np.ndim(x) else candidate[0]))
            samples.append(value)
    passed = all(value >= baseline - 1e-8 for value in samples) if direction == "minimize" else all(value <= baseline + 1e-8 for value in samples)
    return {"passed": passed, "baseline": baseline, "neighbor_values": samples}

