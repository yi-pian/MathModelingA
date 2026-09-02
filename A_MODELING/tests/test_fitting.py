import numpy as np
import pytest

from core.fitting import fit_curve, fit_least_squares, fit_metrics


def test_linear_curve_fit_exact_data():
    x = np.linspace(0, 5, 20); y = 2.5 * x - 1.2
    result = fit_curve(lambda x, a, b: a * x + b, x, y)
    assert result.success and np.allclose(result.parameters, [2.5, -1.2], atol=1e-10)
    assert result.rmse < 1e-10 and result.r2 == pytest.approx(1)


def test_exponential_least_squares():
    x = np.linspace(0, 2, 30); y = 3 * np.exp(0.4 * x)
    residual = lambda p: p[0] * np.exp(p[1] * x) - y
    prediction = lambda p: p[0] * np.exp(p[1] * x)
    result = fit_least_squares(residual, [2, 0.2], bounds=([0, 0], [10, 2]), prediction_function=prediction, observed=y)
    assert result.success and np.allclose(result.parameters, [3, 0.4], atol=1e-8)


def test_constant_observations_metric():
    metrics = fit_metrics([2, 2], [2, 2])
    assert metrics["r2"] == 1

