"""Numerical integration helpers for energy, distance and accumulated quantities."""

from __future__ import annotations

import numpy as np
from scipy.integrate import cumulative_trapezoid, quad, simpson, trapezoid


def integrate_function(function, a, b, **kwargs):
    value, error = quad(function, a, b, **kwargs)
    return {"value": float(value), "error_estimate": float(error)}


def integrate_samples(x, y, *, method="simpson") -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.shape[-1] != x.size or x.size < 2:
        raise ValueError("x must be 1-D and match the last dimension of y")
    if np.any(np.diff(x) <= 0) or not np.all(np.isfinite(y)):
        raise ValueError("x must increase strictly and all values must be finite")
    if method == "simpson":
        return float(simpson(y, x=x))
    if method == "trapezoid":
        return float(trapezoid(y, x=x))
    raise ValueError("method must be 'simpson' or 'trapezoid'")


def cumulative_integral(x, y, *, initial=0.0):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.shape[-1] != x.size or np.any(np.diff(x) <= 0):
        raise ValueError("x must increase strictly and match y")
    return cumulative_trapezoid(y, x, initial=initial)


def path_length(points) -> float:
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[0] < 2 or points.shape[1] not in (2, 3):
        raise ValueError("points must have shape (n, 2) or (n, 3), n >= 2")
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def time_average(time, values) -> float:
    time = np.asarray(time, dtype=float)
    if time.size < 2 or time[-1] <= time[0]:
        raise ValueError("time span must be positive")
    return integrate_samples(time, values, method="trapezoid") / float(time[-1] - time[0])

