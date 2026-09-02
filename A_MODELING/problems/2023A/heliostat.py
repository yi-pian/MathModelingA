"""Vectorized heliostat orientation, cosine and atmosphere calculations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.geometry import normalize


@dataclass(frozen=True)
class HeliostatGeometry:
    receiver_directions: np.ndarray
    normals: np.ndarray
    width_axes: np.ndarray
    height_axes: np.ndarray
    distances_m: np.ndarray
    eta_cos: np.ndarray
    eta_at: np.ndarray


def _normalize_rows(values):
    values = np.asarray(values, dtype=float)
    norms = np.linalg.norm(values, axis=1)
    if np.any(norms <= 1e-14) or not np.all(np.isfinite(norms)):
        raise ValueError("cannot normalize invalid row vectors")
    return values / norms[:, None], norms


def scalar_ideal_normal(sun_vector, receiver_direction):
    """Small scalar reference implementation retained for regression tests."""
    sun = np.asarray(sun_vector, float)
    receiver = np.asarray(receiver_direction, float)
    return normalize(sun + receiver)


def mirror_geometry(centers, receiver_center, sun_vector):
    centers = np.asarray(centers, dtype=float)
    receiver_center = np.asarray(receiver_center, dtype=float)
    sun = np.asarray(sun_vector, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 3 or receiver_center.shape != (3,) or sun.shape != (3,):
        raise ValueError("invalid geometry shapes")
    if abs(np.linalg.norm(sun) - 1.0) > 1e-10:
        raise ValueError("sun_vector must be a unit vector")
    receiver_dirs, distances = _normalize_rows(receiver_center - centers)
    normals, _ = _normalize_rows(receiver_dirs + sun[None, :])
    eta_cos = normals @ sun
    if np.any((eta_cos < -1e-12) | (eta_cos > 1.0 + 1e-12)):
        raise FloatingPointError("cosine efficiency outside [0,1]")

    z_axis = np.array([0.0, 0.0, 1.0])
    width_raw = np.cross(np.broadcast_to(z_axis, normals.shape), normals)
    width_norms = np.linalg.norm(width_raw, axis=1)
    singular = width_norms < 1e-12
    if np.any(singular):
        width_raw[singular] = np.array([1.0, 0.0, 0.0])
    width_axes, _ = _normalize_rows(width_raw)
    height_axes = np.cross(normals, width_axes)
    flip = height_axes[:, 2] < 0.0
    width_axes[flip] *= -1.0
    height_axes[flip] *= -1.0

    eta_at = atmospheric_transmittance(distances)
    return HeliostatGeometry(receiver_dirs, normals, width_axes, height_axes, distances, eta_cos, eta_at)


def atmospheric_transmittance(distance_m):
    distance = np.asarray(distance_m, dtype=float)
    if np.any(distance < 0.0) or np.any(distance > 1000.0):
        raise ValueError("statement atmosphere formula is valid only for 0 <= d_HR <= 1000 m")
    eta = 0.99321 - 0.0001176 * distance + 1.97e-8 * distance**2
    if np.any(~np.isfinite(eta)) or np.any((eta < 0.0) | (eta > 1.0)):
        raise FloatingPointError("invalid atmospheric transmittance")
    return eta


def reflected_direction(incident_propagation, normals):
    incident = np.asarray(incident_propagation, dtype=float)
    normals = np.asarray(normals, dtype=float)
    if incident.shape == (3,):
        return incident[None, :] - 2.0 * (normals @ incident)[:, None] * normals
    if incident.shape != normals.shape:
        raise ValueError("incident directions must be (3,) or match normals")
    return incident - 2.0 * np.sum(incident * normals, axis=1)[:, None] * normals


def mirror_sample_offsets(grid_size):
    """Return equal-area cell-center coordinates in [-1/2,1/2]^2."""
    n = int(grid_size)
    if n < 1:
        raise ValueError("grid_size must be positive")
    axis = (np.arange(n, dtype=float) + 0.5) / n - 0.5
    aa, bb = np.meshgrid(axis, axis, indexing="xy")
    return np.column_stack((aa.ravel(), bb.ravel()))


def mirror_sample_points(center, width, height, width_axis, height_axis, grid_size):
    offsets = mirror_sample_offsets(grid_size)
    return (
        np.asarray(center, float)[None, :]
        + offsets[:, :1] * float(width) * np.asarray(width_axis, float)[None, :]
        + offsets[:, 1:] * float(height) * np.asarray(height_axis, float)[None, :]
    )
