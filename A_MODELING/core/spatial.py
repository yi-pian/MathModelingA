"""Small cKDTree wrappers for reusable low-dimensional spatial searches."""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def _points(values, name):
    points = np.asarray(values, float)
    if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] not in (2, 3) or not np.all(np.isfinite(points)):
        raise ValueError(f"{name} must be a finite non-empty array of shape (n, 2) or (n, 3)")
    return points


def nearest_neighbors(reference_points, query_points, *, k=1, max_distance=np.inf):
    """Return distances and indices into reference_points; missing neighbors use index -1."""
    reference = _points(reference_points, "reference_points")
    query = _points(query_points, "query_points")
    if reference.shape[1] != query.shape[1] or int(k) < 1 or max_distance <= 0:
        raise ValueError("dimensions must match, k >= 1, and max_distance > 0")
    distances, indices = cKDTree(reference).query(query, k=int(k), distance_upper_bound=float(max_distance))
    indices = np.asarray(indices)
    indices = np.where(indices == len(reference), -1, indices)
    return np.asarray(distances), indices.astype(int)


def pairs_within_radius(points, radius):
    """Return unique unordered index pairs whose Euclidean distance is <= radius."""
    points = _points(points, "points")
    if radius < 0:
        raise ValueError("radius must be nonnegative")
    pairs = cKDTree(points).query_pairs(float(radius), output_type="ndarray")
    return np.asarray(pairs, dtype=int).reshape(-1, 2)


def cross_pairs_within_radius(first_points, second_points, radius):
    """Return (first_index, second_index) candidate pairs within a radius."""
    first, second = _points(first_points, "first_points"), _points(second_points, "second_points")
    if first.shape[1] != second.shape[1] or radius < 0:
        raise ValueError("dimensions must match and radius must be nonnegative")
    neighborhoods = cKDTree(second).query_ball_point(first, float(radius))
    return np.asarray([(i, j) for i, js in enumerate(neighborhoods) for j in js], dtype=int).reshape(-1, 2)

