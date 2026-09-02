import numpy as np
import pytest

from core.integration import cumulative_integral, integrate_function, integrate_samples, path_length, time_average


def test_quad_and_sampled_integrals():
    result = integrate_function(lambda x: x**2, 0, 1)
    assert result["value"] == pytest.approx(1 / 3, abs=1e-12)
    x = np.linspace(0, np.pi, 101)
    assert integrate_samples(x, np.sin(x)) == pytest.approx(2, rel=1e-7)


def test_cumulative_path_and_average():
    x = np.linspace(0, 1, 11)
    cumulative = cumulative_integral(x, 2 * x)
    assert cumulative[-1] == pytest.approx(1, rel=1e-12)
    assert path_length([[0, 0], [3, 4], [6, 4]]) == pytest.approx(8)
    assert time_average(x, np.full_like(x, 4.0)) == pytest.approx(4)


def test_nonmonotone_grid_rejected():
    with pytest.raises(ValueError):
        integrate_samples([0, 1, 1], [0, 1, 2])

