import numpy as np

from common import make_system, safety_metrics, simulate
from q2 import solve_q2
from q3 import solve_q3

H_OUT = 120.28446734458524
H_SKIN = 8.364567662641655


def test_q2_critical_design_is_feasible_and_smaller_neighbor_is_not():
    result = solve_q2(H_OUT, H_SKIN, target_dx_m=2e-4, dt_s=1.0)
    assert result.metrics["feasible"]
    smaller = max(0.0006, result.d_ii_m - 0.0001)
    system = make_system(65.0, H_OUT, H_SKIN, d_ii_m=smaller, d_iv_m=0.0055, target_dx_m=2e-4)
    metrics = safety_metrics(simulate(system, 3600.0, dt_s=1.0))
    assert not metrics["feasible"]


def test_q2_skin_temperature_is_nondecreasing():
    result = solve_q2(H_OUT, H_SKIN, target_dx_m=2e-4, dt_s=1.0)
    assert np.min(np.diff(result.simulation.skin_temperature_c)) >= -1e-9


def test_q3_design_is_feasible_and_within_official_bounds():
    result = solve_q3(H_OUT, H_SKIN, target_dx_m=2e-4, dt_s=1.0, coarse_points=7)
    assert result.critical_result.metrics["feasible"]
    assert 0.0006 <= result.d_ii_m <= 0.025
    assert 0.0006 <= result.d_iv_m <= 0.0064
    assert np.isclose(result.total_thickness_m, result.d_ii_m + result.d_iv_m)
