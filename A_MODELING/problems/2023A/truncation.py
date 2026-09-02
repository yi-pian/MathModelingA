"""Finite-sun, finite-cylinder interception calculations for 2023A."""

from __future__ import annotations

import numpy as np

from problem_data import RECEIVER_CENTER_Z_M, RECEIVER_HEIGHT_M, RECEIVER_RADIUS_M, SOLAR_HALF_ANGLE_RAD


def disk_directions(center_direction, count, half_angle=SOLAR_HALF_ANGLE_RAD):
    """Deterministic approximately equal-area directions over a uniform solar disk."""
    center = np.asarray(center_direction, dtype=float)
    center = center / np.linalg.norm(center)
    count = int(count)
    if count < 1 or half_angle < 0.0:
        raise ValueError("count must be positive and half_angle nonnegative")
    helper = np.array([0.0, 0.0, 1.0]) if abs(center[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(center, helper)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(center, e1)
    if count == 1 or half_angle == 0.0:
        return center[None, :]
    # One central ray plus a golden-angle equal-area spiral.
    k = np.arange(count - 1, dtype=float)
    radius = half_angle * np.sqrt((k + 0.5) / (count - 1))
    azimuth = k * np.pi * (3.0 - np.sqrt(5.0))
    transverse = np.cos(azimuth)[:, None] * e1 + np.sin(azimuth)[:, None] * e2
    ring = np.cos(radius)[:, None] * center + np.sin(radius)[:, None] * transverse
    ring /= np.linalg.norm(ring, axis=1)[:, None]
    return np.vstack((center, ring))


def rays_hit_receiver_cylinder(origins, directions, tower_xy, *, radius=RECEIVER_RADIUS_M, height=RECEIVER_HEIGHT_M, center_z=RECEIVER_CENTER_Z_M):
    """Return whether forward rays hit the finite cylindrical side surface."""
    origins = np.asarray(origins, dtype=float)
    directions = np.asarray(directions, dtype=float)
    if origins.shape != directions.shape or origins.ndim != 2 or origins.shape[1] != 3:
        raise ValueError("origins and directions must have shape (M,3)")
    tower_xy = np.asarray(tower_xy, dtype=float)
    offset = origins[:, :2] - tower_xy[None, :]
    dxy = directions[:, :2]
    a = np.sum(dxy * dxy, axis=1)
    b = 2.0 * np.sum(offset * dxy, axis=1)
    c = np.sum(offset * offset, axis=1) - float(radius) ** 2
    discriminant = b * b - 4.0 * a * c
    valid = (a > 1e-16) & (discriminant >= 0.0)
    root = np.zeros_like(discriminant)
    root[valid] = np.sqrt(discriminant[valid])
    t1 = np.full_like(a, np.inf)
    t2 = np.full_like(a, np.inf)
    t1[valid] = (-b[valid] - root[valid]) / (2.0 * a[valid])
    t2[valid] = (-b[valid] + root[valid]) / (2.0 * a[valid])
    t = np.where(t1 > 1e-10, t1, np.where(t2 > 1e-10, t2, np.inf))
    z = np.full_like(t, np.inf)
    finite = np.isfinite(t)
    z[finite] = origins[finite, 2] + t[finite] * directions[finite, 2]
    return np.isfinite(t) & (z >= center_z - height / 2.0 - 1e-10) & (z <= center_z + height / 2.0 + 1e-10)


def truncation_efficiency(sample_points, unblocked_mask, sun_vector, mirror_normal, tower_xy, sun_disk_points):
    """Trace finite-sun reflected rays from unblocked mirror surface samples."""
    points = np.asarray(sample_points, dtype=float)
    keep = np.asarray(unblocked_mask, dtype=bool)
    if keep.shape != (len(points),):
        raise ValueError("unblocked_mask shape mismatch")
    if not np.any(keep):
        return 0.0
    sun_dirs = disk_directions(sun_vector, sun_disk_points)
    incident = -sun_dirs
    normal = np.asarray(mirror_normal, dtype=float)
    reflected = incident - 2.0 * (incident @ normal)[:, None] * normal[None, :]
    reflected /= np.linalg.norm(reflected, axis=1)[:, None]
    origins = np.repeat(points[keep], len(reflected), axis=0)
    directions = np.tile(reflected, (int(np.sum(keep)), 1))
    hits = rays_hit_receiver_cylinder(origins, directions, tower_xy)
    return float(np.mean(hits))
