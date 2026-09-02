import numpy as np
import pytest

from core.geometry import (
    aabb_intersects, angle_between, boolean_time_intervals, line_plane_intersection,
    line_sphere_intersections, normalize, point_in_polygon_2d, point_to_line_distance,
    point_to_plane_distance, point_to_ray_distance, point_to_segment_distance,
    project_point_to_segment, ray_sphere_intersections, rodrigues_matrix, rotate_2d,
    segment_intersects_sphere, segments_intersect_2d, trajectory_minimum_distance,
)


def test_vector_angle_and_degenerate_normalization():
    assert np.allclose(normalize([3, 0, 0]), [1, 0, 0])
    assert angle_between([1, 0], [0, 1]) == pytest.approx(np.pi / 2)
    with pytest.raises(ValueError):
        normalize([0, 0, 0])


def test_distances_and_projection():
    assert point_to_line_distance([1, 2], [0, 0], [1, 0]) == pytest.approx(2)
    assert point_to_segment_distance([2, 1], [0, 0], [1, 0]) == pytest.approx(np.sqrt(2))
    point, parameter = project_point_to_segment([0.5, 2], [0, 0], [1, 0])
    assert np.allclose(point, [0.5, 0]) and parameter == pytest.approx(0.5)
    assert point_to_segment_distance([1, 1], [0, 0], [0, 0]) == pytest.approx(np.sqrt(2))
    assert point_to_plane_distance([1, 2, 3], [0, 0, 0], [0, 0, 1]) == pytest.approx(3)
    assert point_to_ray_distance([-2, 1], [0, 0], [1, 0]) == pytest.approx(np.sqrt(5))


@pytest.mark.parametrize("a,b,c,d,expected", [
    ((0, 0), (2, 2), (0, 2), (2, 0), True),
    ((0, 0), (1, 0), (2, 0), (3, 0), False),
    ((0, 0), (2, 0), (1, 0), (3, 0), True),
    ((0, 0), (1, 0), (1, 0), (1, 1), True),
    ((0, 0), (0, 0), (0, 0), (1, 0), True),
])
def test_segment_intersection(a, b, c, d, expected):
    assert segments_intersect_2d(a, b, c, d) is expected


def test_polygon_and_rotations():
    square = np.array([[0, 0], [2, 0], [2, 2], [0, 2]])
    assert point_in_polygon_2d([1, 1], square)
    assert point_in_polygon_2d([2, 1], square)
    assert not point_in_polygon_2d([3, 1], square)
    assert np.allclose(rotate_2d([1, 0], np.pi / 2), [0, 1], atol=1e-12)
    rotation = rodrigues_matrix([0, 0, 1], np.pi / 2)
    assert np.allclose(rotation @ [1, 0, 0], [0, 1, 0], atol=1e-12)
    assert np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)


def test_line_plane_and_sphere_cases():
    point, parameter = line_plane_intersection([0, 0, 1], [0, 0, -1], [0, 0, 0], [0, 0, 1])
    assert parameter == pytest.approx(1) and np.allclose(point, [0, 0, 0])
    assert line_plane_intersection([0, 0, 1], [1, 0, 0], [0, 0, 0], [0, 0, 1]) is None
    crossing = line_sphere_intersections([-2, 0, 0], [1, 0, 0], [0, 0, 0], 1)
    tangent = line_sphere_intersections([-2, 1, 0], [1, 0, 0], [0, 0, 0], 1)
    missing = line_sphere_intersections([-2, 2, 0], [1, 0, 0], [0, 0, 0], 1)
    assert [item[0] for item in crossing] == pytest.approx([1, 3])
    assert len(tangent) == 1 and not missing
    assert len(ray_sphere_intersections([2, 0, 0], [1, 0, 0], [0, 0, 0], 1)) == 0


def test_collision_aabb_trajectory_and_intervals():
    assert segment_intersects_sphere([-2, 0, 0], [2, 0, 0], [0, 0, 0], 1)
    assert not segment_intersects_sphere([-2, 2, 0], [2, 2, 0], [0, 0, 0], 1)
    assert aabb_intersects([0, 0, 0], [1, 1, 1], [1, 1, 1], [2, 2, 2])
    assert not aabb_intersects([0, 0], [1, 1], [1.1, 0], [2, 1])
    distance, index = trajectory_minimum_distance([[0, 0], [1, 0]], [[0, 2], [1, 0.5]])
    assert distance == pytest.approx(0.5) and index == 1
    assert boolean_time_intervals([0, 1, 2, 3, 4], [False, True, True, False, True]) == [(1.0, 2.0), (4.0, 4.0)]

