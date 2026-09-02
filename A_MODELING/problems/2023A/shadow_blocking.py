"""Area-based shadowing/blocking with conservative corridor candidate screening."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from heliostat import mirror_sample_points
from problem_data import FIELD_RADIUS_M


@dataclass(frozen=True)
class CandidateStats:
    raw_comparisons: int
    candidate_comparisons: int
    average_candidates: float
    maximum_candidates: int


def _sample_segment(start_xy, end_xy, step_m):
    length = float(np.linalg.norm(end_xy - start_xy))
    count = max(2, int(np.ceil(length / step_m)) + 1)
    return np.linspace(start_xy, end_xy, count)


def _sun_ray_end(start_xy, sun_xy, field_radius=FIELD_RADIUS_M):
    speed2 = float(np.dot(sun_xy, sun_xy))
    if speed2 <= 1e-16:
        return np.asarray(start_xy, float)
    b = 2.0 * float(np.dot(start_xy, sun_xy))
    c = float(np.dot(start_xy, start_xy) - field_radius**2)
    disc = max(0.0, b * b - 4.0 * speed2 * c)
    roots = ((-b - np.sqrt(disc)) / (2.0 * speed2), (-b + np.sqrt(disc)) / (2.0 * speed2))
    positive = [root for root in roots if root >= 0.0]
    distance_parameter = max(positive) if positive else 0.0
    return np.asarray(start_xy, float) + distance_parameter * np.asarray(sun_xy, float)


def corridor_candidates(centers, widths, heights, sun_vector, tower_xy, *, step_m=4.0):
    """Build conservative per-target candidates for incoming and reflected ray corridors."""
    centers = np.asarray(centers, float)
    widths = np.asarray(widths, float)
    heights = np.asarray(heights, float)
    sun = np.asarray(sun_vector, float)
    tower_xy = np.asarray(tower_xy, float)
    tree = cKDTree(centers[:, :2])
    half_diagonal = 0.5 * np.hypot(widths, heights)
    # The center-line corridor must cover target-sample displacement and blocker extent.
    corridor_radius = 2.0 * float(np.max(half_diagonal)) + 0.5 * float(step_m) + 1e-9
    shadow_lists = []
    block_lists = []
    counts = []
    for index, center in enumerate(centers):
        shadow_end = _sun_ray_end(center[:2], sun[:2])
        shadow_path = _sample_segment(center[:2], shadow_end, step_m)
        block_path = _sample_segment(center[:2], tower_xy, step_m)
        shadow = set()
        for hits in tree.query_ball_point(shadow_path, corridor_radius):
            shadow.update(hits)
        block = set()
        for hits in tree.query_ball_point(block_path, corridor_radius):
            block.update(hits)
        shadow.discard(index)
        block.discard(index)
        shadow_array = np.fromiter(sorted(shadow), dtype=int)
        block_array = np.fromiter(sorted(block), dtype=int)
        shadow_lists.append(shadow_array)
        block_lists.append(block_array)
        counts.append(len(shadow_array) + len(block_array))
    total = int(sum(counts))
    n = len(centers)
    return shadow_lists, block_lists, CandidateStats(
        raw_comparisons=2 * n * (n - 1),
        candidate_comparisons=total,
        average_candidates=float(np.mean(counts)),
        maximum_candidates=int(max(counts, default=0)),
    )


def rays_intersect_rectangles(origins, direction, rectangle_centers, normals, width_axes, height_axes, widths, heights, *, positive_only=True):
    """For each origin, report whether its ray hits at least one finite oriented rectangle."""
    origins = np.asarray(origins, float)
    direction = np.asarray(direction, float)
    centers = np.asarray(rectangle_centers, float)
    if len(centers) == 0:
        return np.zeros(len(origins), dtype=bool)
    normals = np.asarray(normals, float)
    width_axes = np.asarray(width_axes, float)
    height_axes = np.asarray(height_axes, float)
    denominator = normals @ direction
    numerators = np.einsum("mci,ci->mc", centers[None, :, :] - origins[:, None, :], normals)
    with np.errstate(divide="ignore", invalid="ignore"):
        parameter = numerators / denominator[None, :]
    valid = np.broadcast_to(np.abs(denominator)[None, :] > 1e-12, parameter.shape).copy()
    if positive_only:
        valid &= parameter > 1e-9
    safe_parameter = np.where(np.isfinite(parameter), parameter, 0.0)
    intersection = origins[:, None, :] + safe_parameter[:, :, None] * direction[None, None, :]
    relative = intersection - centers[None, :, :]
    local_width = np.einsum("mci,ci->mc", relative, width_axes)
    local_height = np.einsum("mci,ci->mc", relative, height_axes)
    # Equality is geometric contact with zero blocked area and is not marked blocked.
    valid &= np.abs(local_width) < widths[None, :] / 2.0 - 1e-12
    valid &= np.abs(local_height) < heights[None, :] / 2.0 - 1e-12
    return np.any(valid, axis=1)


def mirror_unblocked_mask(index, centers, widths, heights, geometry, sun_vector, shadow_candidates, block_candidates, grid_size):
    """Return mirror-cell mask after unioning incoming shadows and outgoing blocks."""
    points = mirror_sample_points(
        centers[index], widths[index], heights[index], geometry.width_axes[index], geometry.height_axes[index], grid_size
    )
    shadow_idx = np.asarray(shadow_candidates[index], dtype=int)
    block_idx = np.asarray(block_candidates[index], dtype=int)
    shadowed = rays_intersect_rectangles(
        points,
        sun_vector,
        centers[shadow_idx],
        geometry.normals[shadow_idx],
        geometry.width_axes[shadow_idx],
        geometry.height_axes[shadow_idx],
        widths[shadow_idx],
        heights[shadow_idx],
    )
    blocked = rays_intersect_rectangles(
        points,
        geometry.receiver_directions[index],
        centers[block_idx],
        geometry.normals[block_idx],
        geometry.width_axes[block_idx],
        geometry.height_axes[block_idx],
        widths[block_idx],
        heights[block_idx],
    )
    return points, ~(shadowed | blocked)
