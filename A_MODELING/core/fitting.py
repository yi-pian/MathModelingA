"""Parameter fitting and diagnostics using least_squares and curve_fit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import curve_fit, least_squares


@dataclass(frozen=True)
class FitResult:
    parameters: np.ndarray
    predictions: np.ndarray
    residuals: np.ndarray
    rmse: float
    mae: float
    r2: float
    success: bool
    message: str
    covariance: np.ndarray | None = None


def fit_metrics(observed, predicted):
    observed, predicted = np.asarray(observed, float), np.asarray(predicted, float)
    if observed.shape != predicted.shape or observed.size == 0:
        raise ValueError("observed and predicted must have the same non-empty shape")
    residuals = observed - predicted
    ss_res = float(np.dot(residuals.ravel(), residuals.ravel()))
    centered = observed - observed.mean()
    ss_tot = float(np.dot(centered.ravel(), centered.ravel()))
    return {
        "residuals": residuals,
        "rmse": float(np.sqrt(np.mean(residuals**2))),
        "mae": float(np.mean(np.abs(residuals))),
        "r2": float(1.0 - ss_res / ss_tot) if ss_tot > 0 else (1.0 if ss_res == 0 else np.nan),
    }


def fit_curve(model: Callable, x, y, *, p0=None, bounds=(-np.inf, np.inf), **kwargs) -> FitResult:
    x, y = np.asarray(x, float), np.asarray(y, float)
    parameters, covariance = curve_fit(model, x, y, p0=p0, bounds=bounds, **kwargs)
    predictions = np.asarray(model(x, *parameters), float)
    metrics = fit_metrics(y, predictions)
    message = _diagnostic_message(parameters, bounds, metrics["residuals"])
    return FitResult(parameters, predictions, metrics["residuals"], metrics["rmse"], metrics["mae"], metrics["r2"], True, message, covariance)


def fit_least_squares(residual_function: Callable, x0, *, bounds=(-np.inf, np.inf), prediction_function=None, observed=None, **kwargs) -> FitResult:
    result = least_squares(residual_function, np.asarray(x0, float), bounds=bounds, **kwargs)
    residuals = np.asarray(result.fun, float)
    if prediction_function is not None and observed is not None:
        observed = np.asarray(observed, float)
        predictions = np.asarray(prediction_function(result.x), float)
        metrics = fit_metrics(observed, predictions)
    else:
        predictions = np.array([])
        metrics = {"residuals": residuals, "rmse": float(np.sqrt(np.mean(residuals**2))), "mae": float(np.mean(np.abs(residuals))), "r2": np.nan}
    message = f"{result.message}; {_diagnostic_message(result.x, bounds, residuals)}"
    return FitResult(np.asarray(result.x), predictions, metrics["residuals"], metrics["rmse"], metrics["mae"], metrics["r2"], bool(result.success), message)


def _diagnostic_message(parameters, bounds, residuals):
    lower, upper = np.broadcast_arrays(np.asarray(bounds[0], float), np.asarray(bounds[1], float), np.asarray(parameters, float))[:2]
    at_bound = np.any(np.isclose(parameters, lower)) or np.any(np.isclose(parameters, upper))
    sign_changes = np.count_nonzero(np.diff(np.signbit(np.asarray(residuals).ravel())))
    notes = ["check parameter physical ranges", "inspect residual structure; high R2 alone is insufficient"]
    if at_bound:
        notes.append("one or more parameters are on a bound")
    if len(np.ravel(residuals)) >= 4 and sign_changes <= 1:
        notes.append("residual signs may show systematic bias")
    return "; ".join(notes)

