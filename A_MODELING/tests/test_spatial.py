import numpy as np
import pytest

from core.spatial import cross_pairs_within_radius, nearest_neighbors, pairs_within_radius


def test_nearest_neighbors_matches_manual_distances():
    reference = np.array([[0, 0], [2, 0], [0, 3]], float)
    query = np.array([[1.8, 0.1], [0.1, 2.7]], float)
    distances, indices = nearest_neighbors(reference, query)
    manual = np.linalg.norm(query[:, None, :] - reference[None, :, :], axis=2)
    assert np.array_equal(indices, np.argmin(manual, axis=1))
    assert np.allclose(distances, np.min(manual, axis=1))


def test_radius_pairs_and_cross_pairs():
    points = np.array([[0, 0], [1, 0], [3, 0]], float)
    assert np.array_equal(pairs_within_radius(points, 1.0), [[0, 1]])
    pairs = cross_pairs_within_radius([[0, 0], [4, 0]], [[0.5, 0], [5, 0]], 1.0)
    assert {tuple(pair) for pair in pairs} == {(0, 0), (1, 1)}


def test_missing_neighbor_and_invalid_input():
    distances, indices = nearest_neighbors([[0, 0]], [[10, 0]], max_distance=1.0)
    assert np.isinf(distances[0]) and indices[0] == -1
    with pytest.raises(ValueError): pairs_within_radius([[0, 0]], -1)

