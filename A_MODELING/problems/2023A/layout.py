"""Problem-specific radial-staggered layouts and transparent constraints."""

from __future__ import annotations

import numpy as np

from core.spatial import nearest_neighbors, pairs_within_radius
from problem_data import FIELD_RADIUS_M, TOWER_EXCLUSION_M, FieldDesign


def generate_radial_staggered_layout(
    tower_xy,
    width,
    height,
    installation_height,
    *,
    radial_gap=0.25,
    tangential_gap=0.25,
    outer_radius=520.0,
    phase_fraction=0.5,
):
    """Generate rings around the tower and clip their centers to the official field circle."""
    tower_xy = np.asarray(tower_xy, float)
    width = float(width)
    height = float(height)
    min_distance = width + 5.0 + float(tangential_gap)
    radial_step = width + 5.0 + float(radial_gap)
    if min_distance <= 0.0 or radial_step <= width + 5.0 or outer_radius <= TOWER_EXCLUSION_M:
        raise ValueError("invalid layout spacing/radius")
    points = []
    ring = 0
    radius = TOWER_EXCLUSION_M + 0.05
    while radius <= outer_radius + 1e-12:
        ratio = min(0.999999999, min_distance / (2.0 * radius))
        count = max(1, int(np.floor(np.pi / np.arcsin(ratio))))
        offset = (ring % 2) * float(phase_fraction) * 2.0 * np.pi / count
        angles = offset + 2.0 * np.pi * np.arange(count) / count
        ring_points = tower_xy[None, :] + radius * np.column_stack((np.cos(angles), np.sin(angles)))
        keep = np.linalg.norm(ring_points, axis=1) <= FIELD_RADIUS_M - 0.05
        points.extend(ring_points[keep])
        radius += radial_step
        ring += 1
    if not points:
        raise ValueError("layout contains no mirrors")
    xy = np.asarray(points, float)
    # Deterministic lexicographic order makes Excel and cache keys reproducible.
    order = np.lexsort((xy[:, 0], xy[:, 1]))
    xy = xy[order]
    centers = np.column_stack((xy, np.full(len(xy), float(installation_height))))
    return FieldDesign(centers, np.full(len(xy), width), np.full(len(xy), height), tower_xy)


def generate_hexagonal_layout(tower_xy, width, height, installation_height, *, spacing_gap=0.25, lattice_angle_rad=0.0):
    """Generate a clipped triangular lattice, the dense regular-layout alternative used in Q2/Q3."""
    tower_xy = np.asarray(tower_xy, float)
    width = float(width)
    height = float(height)
    distance = width + 5.0 + float(spacing_gap)
    if distance <= width + 5.0:
        raise ValueError("spacing_gap must make the strict spacing constraint positive")
    dy = np.sqrt(3.0) * distance / 2.0
    y_values = np.arange(-FIELD_RADIUS_M - dy, FIELD_RADIUS_M + dy, dy)
    points = []
    for row, y in enumerate(y_values):
        x_offset = 0.5 * distance if row % 2 else 0.0
        x_values = np.arange(-FIELD_RADIUS_M - distance, FIELD_RADIUS_M + distance, distance) + x_offset
        points.extend(np.column_stack((x_values, np.full_like(x_values, y))))
    xy = np.asarray(points, float)
    if lattice_angle_rad:
        cosine, sine = np.cos(lattice_angle_rad), np.sin(lattice_angle_rad)
        xy = xy @ np.array([[cosine, sine], [-sine, cosine]])
    in_field = np.linalg.norm(xy, axis=1) <= FIELD_RADIUS_M - 0.05
    outside_tower = np.linalg.norm(xy - tower_xy, axis=1) >= TOWER_EXCLUSION_M + 0.05
    xy = xy[in_field & outside_tower]
    order = np.lexsort((xy[:, 0], xy[:, 1]))
    xy = xy[order]
    centers = np.column_stack((xy, np.full(len(xy), float(installation_height))))
    return FieldDesign(centers, np.full(len(xy), width), np.full(len(xy), height), tower_xy)


def apply_radial_zones(design, zone_fractions, zone_widths, zone_heights, zone_installation_heights):
    fractions = np.asarray(zone_fractions, float)
    widths = np.asarray(zone_widths, float)
    heights = np.asarray(zone_heights, float)
    z_values = np.asarray(zone_installation_heights, float)
    if len(widths) != len(heights) or len(widths) != len(z_values) or len(fractions) != len(widths) - 1:
        raise ValueError("zone arrays have inconsistent lengths")
    if np.any(np.diff(fractions) <= 0.0) or np.any((fractions <= 0.0) | (fractions >= 1.0)):
        raise ValueError("zone fractions must increase strictly inside (0,1)")
    radii = np.linalg.norm(design.centers[:, :2] - design.tower_xy, axis=1)
    quantiles = np.quantile(radii, fractions)
    zone = np.digitize(radii, quantiles)
    centers = design.centers.copy()
    centers[:, 2] = z_values[zone]
    return FieldDesign(centers, widths[zone], heights[zone], design.tower_xy), zone


def constraint_report(design, *, rated_power_mw=None):
    centers = design.centers
    widths = design.widths
    heights = design.heights
    field_margin = FIELD_RADIUS_M - np.linalg.norm(centers[:, :2], axis=1)
    tower_margin = np.linalg.norm(centers[:, :2] - design.tower_xy, axis=1) - TOWER_EXCLUSION_M
    dimension_margin = np.minimum.reduce((widths - 2.0, 8.0 - widths, heights - 2.0, 8.0 - heights, widths - heights))
    height_margin = np.minimum.reduce((centers[:, 2] - 2.0, 6.0 - centers[:, 2], centers[:, 2] - heights / 2.0))
    candidate_pairs = pairs_within_radius(centers[:, :2], float(np.max(widths) + 5.0) + 1e-9)
    if len(candidate_pairs):
        pair_distance = np.linalg.norm(centers[candidate_pairs[:, 0], :2] - centers[candidate_pairs[:, 1], :2], axis=1)
        required = np.maximum(widths[candidate_pairs[:, 0]], widths[candidate_pairs[:, 1]]) + 5.0
        spacing_min = float(np.min(pair_distance - required))
    else:
        spacing_min = float("inf")
    nearest_distance, nearest_index = nearest_neighbors(centers[:, :2], centers[:, :2], k=2)
    nearest_nonself = nearest_distance[:, 1]
    nearest_required = np.maximum(widths, widths[nearest_index[:, 1]]) + 5.0
    nearest_spacing_margin = float(np.min(nearest_nonself - nearest_required))
    if not np.isfinite(spacing_min):
        spacing_min = nearest_spacing_margin
    report = {
        "mirror_count": int(len(centers)),
        "total_area_m2": float(np.sum(design.areas)),
        "field_center_margin_min_m": float(np.min(field_margin)),
        "tower_exclusion_margin_min_m": float(np.min(tower_margin)),
        "dimension_margin_min_m": float(np.min(dimension_margin)),
        "installation_margin_min_m": float(np.min(height_margin)),
        "spacing_margin_min_m": spacing_min,
        "nearest_distance_min_m": float(np.min(nearest_nonself)),
        "tower_inside_field_margin_m": float(FIELD_RADIUS_M - np.linalg.norm(design.tower_xy)),
    }
    if rated_power_mw is not None:
        report["rated_power_margin_mw"] = float(rated_power_mw - 60.0)
    report["all_geometric_constraints_pass"] = bool(
        report["field_center_margin_min_m"] >= 0.0
        and report["tower_exclusion_margin_min_m"] >= 0.0
        and report["dimension_margin_min_m"] >= -1e-12
        and report["installation_margin_min_m"] >= -1e-12
        and report["spacing_margin_min_m"] > 0.0
        and report["tower_inside_field_margin_m"] >= 0.0
    )
    return report


def subset_design(design, indices):
    indices = np.asarray(indices, dtype=int)
    return FieldDesign(design.centers[indices], design.widths[indices], design.heights[indices], design.tower_xy)
