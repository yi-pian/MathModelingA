"""Checked wrappers around SciPy scalar and vector root solvers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from scipy.optimize import brentq, root, root_scalar


@dataclass(frozen=True)
class RootResult:
    root: float | np.ndarray
    residual: float
    converged: bool
    iterations: int | None
    message: str = ""


def _scalar_value(function: Callable[[float], float], x: float) -> float:
    value = float(function(float(x)))
    if not np.isfinite(value):
        raise ValueError(f"non-finite function value at x={x}")
    return value


def solve_bracketed(function, bracket, *, xtol=1e-12, rtol=1e-12, maxiter=100) -> RootResult:
    """Solve a scalar root on a reliable sign-changing interval using Brent's method."""
    a, b = map(float, bracket)
    if a > b:
        a, b = b, a
    fa, fb = _scalar_value(function, a), _scalar_value(function, b)
    if abs(fa) <= xtol:
        return RootResult(a, abs(fa), True, 0, "left endpoint is a root")
    if abs(fb) <= xtol:
        return RootResult(b, abs(fb), True, 0, "right endpoint is a root")
    if np.signbit(fa) == np.signbit(fb):
        raise ValueError("bracket endpoints do not have opposite signs")
    value, details = brentq(function, a, b, xtol=xtol, rtol=rtol, maxiter=maxiter, full_output=True)
    residual = abs(_scalar_value(function, value))
    return RootResult(value, residual, bool(details.converged), int(details.iterations), str(details.flag))


def solve_scalar(function, *, bracket=None, x0=None, x1=None, method=None, **kwargs) -> RootResult:
    """General root_scalar wrapper; a bracket defaults to the robust Brent method."""
    if bracket is None and x0 is None:
        raise ValueError("provide bracket or x0")
    chosen = method or ("brentq" if bracket is not None else "secant")
    result = root_scalar(function, bracket=bracket, x0=x0, x1=x1, method=chosen, **kwargs)
    residual = abs(_scalar_value(function, result.root))
    return RootResult(float(result.root), residual, bool(result.converged), int(result.iterations), str(result.flag))


def scan_sign_changes(function, start, stop, *, samples=1001, zero_tol=1e-12):
    """Return disjoint brackets and exact sampled roots in an interval."""
    if samples < 2 or stop <= start:
        raise ValueError("require samples >= 2 and stop > start")
    xs = np.linspace(float(start), float(stop), int(samples))
    ys = np.array([_scalar_value(function, x) for x in xs])
    brackets: list[tuple[float, float]] = []
    for index in range(len(xs) - 1):
        if abs(ys[index]) <= zero_tol:
            brackets.append((float(xs[index]), float(xs[index])))
        elif np.signbit(ys[index]) != np.signbit(ys[index + 1]):
            brackets.append((float(xs[index]), float(xs[index + 1])))
    if abs(ys[-1]) <= zero_tol:
        brackets.append((float(xs[-1]), float(xs[-1])))
    return brackets


def find_all_roots(function, start, stop, *, samples=1001, xtol=1e-10):
    """Find sampled exact roots and sign-changing roots; even-multiplicity roots need prior knowledge."""
    roots_found: list[RootResult] = []
    for a, b in scan_sign_changes(function, start, stop, samples=samples, zero_tol=xtol):
        result = RootResult(a, abs(_scalar_value(function, a)), True, 0, "sampled root") if a == b else solve_bracketed(function, (a, b), xtol=xtol)
        if not roots_found or abs(float(result.root) - float(roots_found[-1].root)) > 10 * xtol:
            roots_found.append(result)
    return roots_found


def solve_system(function, x0: Iterable[float], *, method="hybr", residual_tol=1e-8, **kwargs) -> RootResult:
    """Solve a nonlinear system and verify the infinity-norm residual."""
    result = root(function, np.asarray(x0, dtype=float), method=method, **kwargs)
    values = np.asarray(function(result.x), dtype=float)
    residual = float(np.linalg.norm(values, ord=np.inf))
    converged = bool(result.success and np.all(np.isfinite(result.x)) and residual <= residual_tol)
    return RootResult(np.asarray(result.x), residual, converged, getattr(result, "nit", None), str(result.message))

