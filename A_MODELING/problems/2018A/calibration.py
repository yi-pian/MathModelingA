"""Q1 calibration and identifiability diagnostics for the two Robin boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.fitting import FitResult, fit_least_squares, fit_metrics

from common import load_official_data, make_system, simulate


@dataclass(frozen=True)
class CalibrationResult:
    h_out_w_m2k: float
    h_skin_w_m2k: float
    prediction_c: np.ndarray
    residual_c: np.ndarray
    rmse_c: float
    mae_c: float
    r2: float
    success: bool
    message: str
    multistart: pd.DataFrame
    jacobian_singular_values: np.ndarray
    jacobian_condition_number: float
    parameter_correlation: float
    elapsed_seconds: float
    target_dx_m: float
    dt_s: float


def predict_skin_temperature(
    parameters: np.ndarray | tuple[float, float],
    *,
    target_dx_m: float = 2.0e-4,
    dt_s: float = 1.0,
) -> np.ndarray:
    h_out, h_skin = map(float, parameters)
    system = make_system(75.0, h_out, h_skin, d_ii_m=0.006, d_iv_m=0.005, target_dx_m=target_dx_m)
    return simulate(system, 5400.0, dt_s=dt_s).skin_temperature_c


def _finite_difference_jacobian(parameters: np.ndarray, target_dx_m: float, dt_s: float) -> np.ndarray:
    columns = []
    for index, value in enumerate(parameters):
        step = max(1.0e-3, abs(value) * 1.0e-3)
        plus, minus = parameters.copy(), parameters.copy()
        plus[index] += step
        minus[index] -= step
        columns.append((predict_skin_temperature(plus, target_dx_m=target_dx_m, dt_s=dt_s) - predict_skin_temperature(minus, target_dx_m=target_dx_m, dt_s=dt_s)) / (2.0 * step))
    return np.column_stack(columns)


def _fit_from_start(start: tuple[float, float], observed: np.ndarray, target_dx_m: float, dt_s: float) -> FitResult:
    prediction = lambda p: predict_skin_temperature(p, target_dx_m=target_dx_m, dt_s=dt_s)
    return fit_least_squares(
        lambda p: prediction(p) - observed,
        np.asarray(start, float),
        bounds=([1.0, 1.0], [500.0, 100.0]),
        prediction_function=prediction,
        observed=observed,
        x_scale="jac",
        xtol=2.0e-8,
        ftol=2.0e-8,
        gtol=2.0e-8,
        max_nfev=80,
    )


def calibrate(
    starts: tuple[tuple[float, float], ...] = ((10.0, 5.0), (50.0, 8.0), (120.0, 12.0), (250.0, 8.0), (450.0, 25.0)),
    *,
    target_dx_m: float = 2.0e-4,
    final_dx_m: float = 1.0e-4,
    dt_s: float = 1.0,
) -> CalibrationResult:
    """Run deterministic multi-start fitting, then refine once on the final grid."""
    _, measurements = load_official_data()
    observed = measurements.iloc[:, 1].to_numpy(float)
    started = perf_counter()
    fits = [_fit_from_start(start, observed, target_dx_m, dt_s) for start in starts]
    rows = []
    for start, fit in zip(starts, fits):
        rows.append(
            {
                "start_h_out_w_m2k": start[0],
                "start_h_skin_w_m2k": start[1],
                "h_out_w_m2k": fit.parameters[0],
                "h_skin_w_m2k": fit.parameters[1],
                "rmse_c": fit.rmse,
                "mae_c": fit.mae,
                "r2": fit.r2,
                "success": fit.success,
            }
        )
    table = pd.DataFrame(rows).sort_values("rmse_c", ignore_index=True)
    if not bool(table.iloc[0]["success"]):
        raise RuntimeError("no successful calibration start")
    best = table.iloc[0]
    refined = _fit_from_start((float(best.h_out_w_m2k), float(best.h_skin_w_m2k)), observed, final_dx_m, dt_s)
    if not refined.success:
        raise RuntimeError(refined.message)
    parameters = refined.parameters
    prediction = predict_skin_temperature(parameters, target_dx_m=final_dx_m, dt_s=dt_s)
    metrics = fit_metrics(observed, prediction)
    jacobian = _finite_difference_jacobian(parameters, final_dx_m, dt_s)
    singular_values = np.linalg.svd(jacobian, full_matrices=False, compute_uv=False)
    condition = float(singular_values[0] / singular_values[-1])
    covariance_shape = np.linalg.pinv(jacobian.T @ jacobian)
    correlation = float(covariance_shape[0, 1] / np.sqrt(covariance_shape[0, 0] * covariance_shape[1, 1]))
    return CalibrationResult(
        h_out_w_m2k=float(parameters[0]),
        h_skin_w_m2k=float(parameters[1]),
        prediction_c=prediction,
        residual_c=observed - prediction,
        rmse_c=metrics["rmse"],
        mae_c=metrics["mae"],
        r2=metrics["r2"],
        success=True,
        message=refined.message,
        multistart=table,
        jacobian_singular_values=singular_values,
        jacobian_condition_number=condition,
        parameter_correlation=correlation,
        elapsed_seconds=perf_counter() - started,
        target_dx_m=final_dx_m,
        dt_s=dt_s,
    )


if __name__ == "__main__":
    result = calibrate()
    print(
        {
            "h_out_w_m2k": result.h_out_w_m2k,
            "h_skin_w_m2k": result.h_skin_w_m2k,
            "rmse_c": result.rmse_c,
            "mae_c": result.mae_c,
            "r2": result.r2,
            "jacobian_condition_number": result.jacobian_condition_number,
            "parameter_correlation": result.parameter_correlation,
            "elapsed_seconds": result.elapsed_seconds,
        }
    )
    print(result.multistart.to_string(index=False))
