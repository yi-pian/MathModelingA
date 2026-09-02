"""Local finite-difference and percentage perturbation sensitivity analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def one_parameter_sensitivity(function, baseline, parameter, *, changes=(-0.10, -0.05, -0.01, 0.0, 0.01, 0.05, 0.10)):
    params = dict(baseline)
    if parameter not in params:
        raise KeyError(parameter)
    base_value = float(function(params))
    rows = []
    for change in changes:
        varied = dict(params)
        varied[parameter] = params[parameter] * (1.0 + change)
        value = float(function(varied))
        rows.append({"parameter": parameter, "change_rate": float(change), "parameter_value": float(varied[parameter]), "output": value, "output_change": value - base_value, "output_change_rate": (value - base_value) / base_value if base_value != 0 else np.nan})
    return pd.DataFrame(rows)


def multi_parameter_sensitivity(function, baseline, *, changes=(-0.05, 0.05)):
    frames = [one_parameter_sensitivity(function, baseline, name, changes=changes) for name in baseline]
    return pd.concat(frames, ignore_index=True)


def finite_difference_sensitivity(function, parameters, *, relative_step=1e-5):
    point = np.asarray(parameters, float)
    if point.ndim != 1:
        raise ValueError("parameters must be one-dimensional")
    gradient = np.empty_like(point)
    for index in range(point.size):
        step = relative_step * max(1.0, abs(point[index]))
        upper, lower = point.copy(), point.copy()
        upper[index] += step
        lower[index] -= step
        gradient[index] = (float(function(upper)) - float(function(lower))) / (2.0 * step)
    return gradient


def normalized_sensitivity(function, parameters, *, relative_step=1e-5):
    point = np.asarray(parameters, float)
    base = float(function(point))
    gradient = finite_difference_sensitivity(function, point, relative_step=relative_step)
    return np.divide(gradient * point, base, out=np.full_like(point, np.nan), where=base != 0)

