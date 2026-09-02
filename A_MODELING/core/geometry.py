"""Vector-first 2-D/3-D geometry, collision and line-of-sight helpers."""

from __future__ import annotations

import numpy as np

EPS = 1e-10


def _vector(value, dimensions=None):
    result = np.asarray(value, dtype=float)
    if result.ndim != 1 or (dimensions is not None and result.size != dimensions):
        raise ValueError(f"expected a vector{f' of length {dimensions}' if dimensions else ''}")
    if not np.all(np.isfinite(result)):
        raise ValueError("geometry input must be finite")
    return result


def normalize(vector, *, eps=EPS):
    vector = _vector(vector)
    norm = float(np.linalg.norm(vector))
    if norm <= eps:
        raise ValueError("cannot normalize a zero vector")
    return vector / norm


def angle_between(first, second, *, eps=EPS):
    first, second = _vector(first), _vector(second)
    if first.shape != second.shape:
        raise ValueError("vectors must have matching dimensions")
    cosine = float(np.dot(normalize(first, eps=eps), normalize(second, eps=eps)))
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))


def point_distance(first, second):
    first, second = _vector(first), _vector(second)
    if first.shape != second.shape:
        raise ValueError("points must have matching dimensions")
    return float(np.linalg.norm(first - second))


def project_point_to_line(point, line_point, direction, *, eps=EPS):
    point, line_point, direction = _vector(point), _vector(line_point), _vector(direction)
    if point.shape != line_point.shape or point.shape != direction.shape:
        raise ValueError("all vectors must have matching dimensions")
    denominator = float(np.dot(direction, direction))
    if denominator <= eps**2:
        raise ValueError("line direction must be nonzero")
    parameter = float(np.dot(point - line_point, direction) / denominator)
    return line_point + parameter * direction, parameter


def point_to_line_distance(point, line_point, direction, *, eps=EPS):
    projection, _ = project_point_to_line(point, line_point, direction, eps=eps)
    return point_distance(point, projection)


def project_point_to_segment(point, start, end, *, eps=EPS):
    point, start, end = _vector(point), _vector(start), _vector(end)
    if point.shape != start.shape or point.shape != end.shape:
        raise ValueError("all points must have matching dimensions")
    segment = end - start
    length_squared = float(np.dot(segment, segment))
    if length_squared <= eps**2:
        return start.copy(), 0.0
    parameter = float(np.clip(np.dot(point - start, segment) / length_squared, 0.0, 1.0))
    return start + parameter * segment, parameter


def point_to_segment_distance(point, start, end, *, eps=EPS):
    projection, _ = project_point_to_segment(point, start, end, eps=eps)
    return point_distance(point, projection)


def project_point_to_plane(point, plane_point, normal, *, eps=EPS):
    point, plane_point, normal = _vector(point, 3), _vector(plane_point, 3), _vector(normal, 3)
    unit = normalize(normal, eps=eps)
    signed_distance = float(np.dot(point - plane_point, unit))
    return point - signed_distance * unit, signed_distance


def point_to_plane_distance(point, plane_point, normal, *, eps=EPS):
    _, signed_distance = project_point_to_plane(point, plane_point, normal, eps=eps)
    return abs(signed_distance)


def _cross2d(first, second):
    return float(first[0] * second[1] - first[1] * second[0])


def segments_intersect_2d(a, b, c, d, *, eps=EPS):
    a, b, c, d = (_vector(value, 2) for value in (a, b, c, d))
    r, s = b - a, d - c
    rxs, qxr = _cross2d(r, s), _cross2d(c - a, r)
    if abs(rxs) <= eps and abs(qxr) <= eps:
        rr = float(np.dot(r, r))
        ss = float(np.dot(s, s))
        if rr <= eps**2 and ss <= eps**2:
            return point_distance(a, c) <= eps
        if rr <= eps**2:
            return point_to_segment_distance(a, c, d) <= eps
        t0, t1 = float(np.dot(c - a, r) / rr), float(np.dot(d - a, r) / rr)
        return max(min(t0, t1), 0.0) <= min(max(t0, t1), 1.0) + eps
    if abs(rxs) <= eps:
        return False
    t = _cross2d(c - a, s) / rxs
    u = _cross2d(c - a, r) / rxs
    return -eps <= t <= 1.0 + eps and -eps <= u <= 1.0 + eps


def point_in_polygon_2d(point, polygon, *, include_boundary=True, eps=EPS):
    point = _vector(point, 2)
    polygon = np.asarray(polygon, dtype=float)
    if polygon.ndim != 2 or polygon.shape[1] != 2 or polygon.shape[0] < 3:
        raise ValueError("polygon must have shape (n, 2), n >= 3")
    inside = False
    for index in range(len(polygon)):
        start, end = polygon[index], polygon[(index + 1) % len(polygon)]
        if point_to_segment_distance(point, start, end) <= eps:
            return bool(include_boundary)
        crosses = (start[1] > point[1]) != (end[1] > point[1])
        if crosses:
            x_cross = start[0] + (point[1] - start[1]) * (end[0] - start[0]) / (end[1] - start[1])
            if x_cross > point[0]:
                inside = not inside
    return inside


def rotate_2d(point, angle, *, center=(0.0, 0.0)):
    point, center = _vector(point, 2), _vector(center, 2)
    cosine, sine = np.cos(float(angle)), np.sin(float(angle))
    matrix = np.array([[cosine, -sine], [sine, cosine]])
    return center + matrix @ (point - center)


def rotation_matrix_3d(axis, angle):
    if isinstance(axis, str):
        axes = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
        try:
            axis = axes[axis.lower()]
        except KeyError as error:
            raise ValueError("axis must be x, y, z, or a 3-vector") from error
    return rodrigues_matrix(axis, angle)


def rodrigues_matrix(axis, angle, *, eps=EPS):
    x, y, z = normalize(_vector(axis, 3), eps=eps)
    skew = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    identity = np.eye(3)
    return identity * np.cos(angle) + (1.0 - np.cos(angle)) * np.outer((x, y, z), (x, y, z)) + np.sin(angle) * skew


def line_plane_intersection(line_point, direction, plane_point, normal, *, eps=EPS):
    line_point, direction, plane_point, normal = (_vector(value, 3) for value in (line_point, direction, plane_point, normal))
    if np.linalg.norm(direction) <= eps or np.linalg.norm(normal) <= eps:
        raise ValueError("direction and normal must be nonzero")
    denominator = float(np.dot(direction, normal))
    if abs(denominator) <= eps:
        return None
    parameter = float(np.dot(plane_point - line_point, normal) / denominator)
    return line_point + parameter * direction, parameter


def line_sphere_intersections(line_point, direction, center, radius, *, eps=EPS):
    line_point, direction, center = (_vector(value, 3) for value in (line_point, direction, center))
    radius = float(radius)
    if radius < 0 or np.linalg.norm(direction) <= eps:
        raise ValueError("radius must be nonnegative and direction nonzero")
    offset = line_point - center
    a = float(np.dot(direction, direction))
    b = 2.0 * float(np.dot(offset, direction))
    c = float(np.dot(offset, offset) - radius**2)
    discriminant = b * b - 4.0 * a * c
    if discriminant < -eps:
        return []
    if abs(discriminant) <= eps:
        parameters = [-b / (2.0 * a)]
    else:
        root_disc = np.sqrt(max(0.0, discriminant))
        parameters = sorted(((-b - root_disc) / (2.0 * a), (-b + root_disc) / (2.0 * a)))
    return [(float(parameter), line_point + parameter * direction) for parameter in parameters]


def ray_sphere_intersections(origin, direction, center, radius, *, eps=EPS):
    return [(parameter, point) for parameter, point in line_sphere_intersections(origin, direction, center, radius, eps=eps) if parameter >= -eps]


def segment_intersects_sphere(start, end, center, radius, *, eps=EPS):
    start, end, center = (_vector(value, 3) for value in (start, end, center))
    if radius < 0:
        raise ValueError("radius must be nonnegative")
    return point_to_segment_distance(center, start, end, eps=eps) <= radius + eps


def point_to_ray_distance(point, origin, direction, *, eps=EPS):
    point, origin, direction = _vector(point), _vector(origin), _vector(direction)
    projection, parameter = project_point_to_line(point, origin, direction, eps=eps)
    return point_distance(point, origin if parameter < 0 else projection)


def aabb_intersects(minimum_a, maximum_a, minimum_b, maximum_b, *, eps=EPS):
    minimum_a, maximum_a, minimum_b, maximum_b = (_vector(value) for value in (minimum_a, maximum_a, minimum_b, maximum_b))
    if not (minimum_a.shape == maximum_a.shape == minimum_b.shape == maximum_b.shape):
        raise ValueError("AABB vectors must have matching dimensions")
    if np.any(minimum_a > maximum_a) or np.any(minimum_b > maximum_b):
        raise ValueError("each minimum must be <= its maximum")
    return bool(np.all(maximum_a + eps >= minimum_b) and np.all(maximum_b + eps >= minimum_a))


def line_of_sight_blocked_by_sphere(observer, target, center, radius, *, eps=EPS):
    """Return whether the closed sight segment intersects a spherical obstacle."""
    return segment_intersects_sphere(observer, target, center, radius, eps=eps)


def trajectory_minimum_distance(first, second):
    first, second = np.asarray(first, float), np.asarray(second, float)
    if first.shape != second.shape or first.ndim != 2 or first.shape[1] not in (2, 3):
        raise ValueError("trajectories must have equal shape (n, 2) or (n, 3)")
    distances = np.linalg.norm(first - second, axis=1)
    index = int(np.argmin(distances))
    return float(distances[index]), index


def boolean_time_intervals(time, mask):
    """Convert a sampled Boolean condition to inclusive [start, end] intervals."""
    time, mask = np.asarray(time, float), np.asarray(mask, bool)
    if time.ndim != 1 or mask.shape != time.shape or np.any(np.diff(time) <= 0):
        raise ValueError("time must increase strictly and match mask")
    intervals = []
    start = None
    for index, active in enumerate(mask):
        if active and start is None:
            start = index
        if start is not None and (not active or index == len(mask) - 1):
            end = index if active else index - 1
            intervals.append((float(time[start]), float(time[end])))
            start = None
    return intervals

