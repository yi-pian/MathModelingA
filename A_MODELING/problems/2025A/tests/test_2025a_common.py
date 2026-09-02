from math import pi

import numpy as np
import pytest

from common import (
    PRECISIONS,
    Strategy,
    bomb_position,
    burst_point,
    cloud_center,
    drop_point,
    event_value_m2,
    feasible_active_window,
    heading_vector,
    interval_duration,
    locate_nonpositive_intervals,
    marginal_interval_gains,
    merge_intervals,
    missile_arrival_time,
    missile_position,
    obscuration_intervals,
    point_segment_distance_sq_many,
    target_surface_points,
    uav_position,
    validate_drop_gaps,
)
from problem_data import CLOUD_DESCENT_M_S, MISSILE_INITIAL_M, TARGET_HEIGHT_M, TARGET_RADIUS_M


def example(**changes):
    values = dict(uav="FY1", missile="M1", heading_rad=pi, speed_m_s=120.0, drop_time_s=1.5, delay_s=3.6)
    values.update(changes)
    return Strategy(**values)


def test_heading_vector_is_unit_and_horizontal():
    vector = heading_vector(0.37)
    assert np.linalg.norm(vector) == pytest.approx(1.0)
    assert vector[2] == 0.0


def test_uav_motion_is_horizontal_with_requested_speed():
    p0 = uav_position("FY1", 0.4, 100.0, 2.0)
    p1 = uav_position("FY1", 0.4, 100.0, 2.01)
    assert p0[2] == p1[2] == 1800.0
    assert np.linalg.norm(p1 - p0) / 0.01 == pytest.approx(100.0)


@pytest.mark.parametrize("missile", ["M1", "M2", "M3"])
def test_missile_arrives_at_origin(missile):
    assert np.linalg.norm(missile_position(missile, missile_arrival_time(missile))) < 1e-10


@pytest.mark.parametrize("missile", ["M1", "M2", "M3"])
def test_missile_speed_is_300(missile):
    delta = missile_position(missile, 0.01) - missile_position(missile, 0.0)
    assert np.linalg.norm(delta) / 0.01 == pytest.approx(300.0)


def test_drop_point_matches_uav():
    strategy = example()
    assert np.allclose(drop_point(strategy), uav_position("FY1", pi, 120.0, 1.5))


def test_bomb_position_continuous_at_drop():
    strategy = example()
    assert np.allclose(bomb_position(strategy, strategy.drop_time_s), drop_point(strategy))


def test_bomb_position_matches_burst_point():
    strategy = example()
    assert np.allclose(bomb_position(strategy, strategy.burst_time_s), burst_point(strategy))


def test_q1_burst_point_analytic():
    point = burst_point(example())
    assert point[0] == pytest.approx(17800.0 - 120.0 * 5.1)
    assert point[1] == pytest.approx(0.0)
    assert point[2] == pytest.approx(1800.0 - 0.5 * 9.8 * 3.6**2)


def test_cloud_descends_at_three_m_per_s():
    strategy = example()
    first = cloud_center(strategy, strategy.burst_time_s)
    second = cloud_center(strategy, strategy.burst_time_s + 2.0)
    assert np.allclose(second - first, [0.0, 0.0, -2.0 * CLOUD_DESCENT_M_S])


def test_below_ground_burst_is_infeasible():
    strategy = example(uav="FY3", delay_s=20.0)
    assert feasible_active_window(strategy) is None


def test_active_window_starts_at_burst():
    strategy = example()
    start, stop = feasible_active_window(strategy)
    assert start == pytest.approx(5.1)
    assert stop > start


@pytest.mark.parametrize("level", ["FAST", "STANDARD", "FINAL"])
def test_target_samples_lie_on_cylinder_boundary(level):
    points = target_surface_points(level)
    radial = np.hypot(points[:, 0], points[:, 1] - 200.0)
    on_side = np.isclose(radial, TARGET_RADIUS_M)
    on_cap = np.isclose(points[:, 2], 0.0) | np.isclose(points[:, 2], TARGET_HEIGHT_M)
    assert np.all(on_side | on_cap)
    assert np.all((points[:, 2] >= 0.0) & (points[:, 2] <= TARGET_HEIGHT_M))


def test_surface_levels_strictly_refine():
    sizes = [len(target_surface_points(name)) for name in ("FAST", "STANDARD", "FINAL")]
    assert sizes[0] < sizes[1] < sizes[2]


def test_point_to_segment_distance_obvious_separation():
    value = point_segment_distance_sq_many(np.array([[0.0, 1.0, 0.0]]), np.zeros(3), np.array([[2.0, 0.0, 0.0]]))
    assert value[0] == pytest.approx(1.0)


def test_point_to_segment_distance_tangent():
    value = point_segment_distance_sq_many(np.array([[1.0, 10.0, 0.0]]), np.zeros(3), np.array([[2.0, 0.0, 0.0]]))
    assert value[0] == pytest.approx(100.0)


def test_point_to_segment_clamps_beyond_endpoint():
    value = point_segment_distance_sq_many(np.array([[3.0, 1.0, 0.0]]), np.zeros(3), np.array([[2.0, 0.0, 0.0]]))
    assert value[0] == pytest.approx(2.0)


def test_point_to_segment_handles_zero_length():
    value = point_segment_distance_sq_many(np.array([[1.0, 2.0, 2.0]]), np.zeros(3), np.zeros((1, 3)))
    assert value[0] == pytest.approx(9.0)


def test_locate_single_negative_interval_and_roots():
    intervals, roots = locate_nonpositive_intervals(lambda t: (t - 1.0) * (t - 2.0), 0.0, 3.0, step=0.4)
    assert np.allclose(intervals, [(1.0, 2.0)], atol=1e-8)
    assert roots == pytest.approx([1.0, 2.0])


def test_locate_two_negative_intervals():
    f = lambda t: (t - 1.0) * (t - 2.0) * (t - 3.0) * (t - 4.0)
    intervals, _ = locate_nonpositive_intervals(f, 0.0, 5.0, step=0.3)
    assert np.allclose(intervals, [(1.0, 2.0), (3.0, 4.0)], atol=1e-8)


def test_tangent_point_has_zero_duration():
    intervals, roots = locate_nonpositive_intervals(lambda t: (t - 1.5) ** 2, 0.0, 3.0, step=0.4)
    assert interval_duration(intervals) < 1e-8
    assert any(abs(root - 1.5) < 1e-5 for root in roots)


def test_narrow_negative_pocket_is_recovered_by_minimum_refinement():
    intervals, _ = locate_nonpositive_intervals(lambda t: (t - 1.0) ** 2 - 0.01**2, 0.0, 2.0, step=0.2)
    assert interval_duration(intervals) == pytest.approx(0.02, abs=1e-7)


@pytest.mark.parametrize(
    "intervals,expected",
    [
        ([(0, 1), (2, 3)], [(0, 1), (2, 3)]),
        ([(0, 2), (1, 3)], [(0, 3)]),
        ([(0, 1), (1, 2)], [(0, 2)]),
        ([(0, 4), (1, 2)], [(0, 4)]),
        ([(2, 3), (0, 1), (1, 2)], [(0, 3)]),
    ],
)
def test_merge_intervals_cases(intervals, expected):
    assert merge_intervals(intervals) == expected


def test_interval_duration_uses_union():
    assert interval_duration([(0.0, 2.0), (1.0, 4.0)]) == pytest.approx(4.0)


def test_marginal_interval_gains():
    gains = marginal_interval_gains([[(0.0, 2.0)], [(1.0, 3.0)], [(5.0, 6.0)]])
    assert gains == pytest.approx([2.0, 1.0, 1.0])


def test_strategy_rejects_speed_out_of_bounds():
    with pytest.raises(ValueError, match="speed"):
        example(speed_m_s=69.9)


def test_strategy_rejects_negative_time():
    with pytest.raises(ValueError, match="nonnegative"):
        example(drop_time_s=-0.1)


def test_heading_output_is_wrapped_degrees():
    assert example(heading_rad=-pi / 2).heading_deg == pytest.approx(270.0)


def test_drop_gap_validation_accepts_one_second():
    assert validate_drop_gaps([example(drop_time_s=1.0), example(drop_time_s=2.0, bomb_no=2)])


def test_drop_gap_validation_rejects_short_gap():
    assert not validate_drop_gaps([example(drop_time_s=1.0), example(drop_time_s=1.9, bomb_no=2)])


def test_full_model_is_never_easier_than_point_for_same_time():
    strategy = example()
    time_s = strategy.burst_time_s + 1.0
    point = event_value_m2(strategy, time_s, model="point")
    full = event_value_m2(strategy, time_s, model="full", surface_points=target_surface_points("FAST"))
    assert full >= point - 1e-9


def test_q1_obscuration_result_is_finite_for_both_models():
    strategy = example()
    for model in ("point", "full"):
        result = obscuration_intervals(strategy, model=model, precision="FAST")
        assert result.feasible
        assert np.isfinite(result.duration_s)
        assert result.duration_s >= 0.0


def test_missile_initial_positions_unchanged():
    assert np.array_equal(missile_position("M1", 0.0), MISSILE_INITIAL_M["M1"])


def test_precision_steps_are_strictly_refined():
    assert PRECISIONS["FAST"].event_step_s > PRECISIONS["STANDARD"].event_step_s > PRECISIONS["FINAL"].event_step_s
