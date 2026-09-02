import numpy as np
import pytest

from core.optimization import coarse_to_fine, local_perturbation_check, optimize_global, optimize_local, optimize_scalar


def test_scalar_minimum_and_explicit_maximum():
    minimum = optimize_scalar(lambda x: (x - 3) ** 2, bounds=(0, 5))
    maximum = optimize_scalar(lambda x: -(x - 2) ** 2 + 4, bounds=(0, 4), direction="maximize")
    assert minimum.success and minimum.x == pytest.approx(3, abs=1e-6)
    assert maximum.success and maximum.x == pytest.approx(2, abs=1e-6) and maximum.objective == pytest.approx(4)


def test_two_dimensional_local_and_global():
    function = lambda x: (x[0] - 1) ** 2 + 2 * (x[1] + 2) ** 2
    local = optimize_local(function, [0, 0], bounds=[(-5, 5), (-5, 5)])
    global_result = optimize_global(function, [(-5, 5), (-5, 5)], tol=1e-8)
    assert local.success and np.allclose(local.x, [1, -2], atol=1e-6)
    assert global_result.success and np.allclose(global_result.x, [1, -2], atol=1e-5)


def test_coarse_fine_and_local_verification():
    result, details = coarse_to_fine(lambda x: (x - 3) ** 2, (0, 10), grid_points=21)
    check = local_perturbation_check(lambda x: (x - 3) ** 2, result.x)
    assert result.x == pytest.approx(3, abs=1e-7)
    assert details["verified_objective"] < 1e-12 and check["passed"]

