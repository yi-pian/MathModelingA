"""Single-time and annual heliostat-field evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd

from heliostat import mirror_geometry
from problem_data import FieldDesign, REFLECTIVITY, precision_config
from shadow_blocking import CandidateStats, corridor_candidates, mirror_unblocked_mask
from solar import representative_times
from truncation import truncation_efficiency


@dataclass(frozen=True)
class FieldTimeResult:
    eta_cos: np.ndarray
    eta_at: np.ndarray
    eta_sb: np.ndarray
    eta_trunc: np.ndarray
    eta_total: np.ndarray
    power_kw: np.ndarray
    dni_kw_m2: float
    candidate_stats: CandidateStats
    timings_s: dict

    def summary(self, areas):
        areas = np.asarray(areas, float)
        total_area = float(np.sum(areas))
        weighted = lambda value: float(np.sum(areas * value) / total_area)
        return {
            "eta_cos": weighted(self.eta_cos),
            "eta_at": weighted(self.eta_at),
            "eta_sb": weighted(self.eta_sb),
            "eta_trunc": weighted(self.eta_trunc),
            "eta_total": weighted(self.eta_total),
            "power_kw": float(np.sum(self.power_kw)),
            "power_per_area_kw_m2": float(np.sum(self.power_kw) / total_area),
        }


def _validate_efficiencies(**values):
    for name, value in values.items():
        array = np.asarray(value, float)
        if np.any(~np.isfinite(array)) or np.any(array < -1e-12) or np.any(array > 1.0 + 1e-12):
            raise FloatingPointError(f"{name} outside [0,1] or non-finite")


def evaluate_time(design: FieldDesign, sun_vector, dni_kw_m2, *, precision="STANDARD", candidate_mode="corridor"):
    config = precision_config(precision)
    timing = {}
    start = perf_counter()
    geometry = mirror_geometry(design.centers, design.receiver_center, sun_vector)
    timing["geometry"] = perf_counter() - start

    start = perf_counter()
    if candidate_mode == "brute":
        all_indices = np.arange(len(design.centers))
        shadow_candidates = [all_indices[all_indices != i] for i in range(len(design.centers))]
        block_candidates = [all_indices[all_indices != i] for i in range(len(design.centers))]
        n = len(design.centers)
        stats = CandidateStats(2 * n * (n - 1), 2 * n * (n - 1), 2.0 * (n - 1), 2 * (n - 1))
    elif candidate_mode == "corridor":
        shadow_candidates, block_candidates, stats = corridor_candidates(
            design.centers, design.widths, design.heights, sun_vector, design.tower_xy, step_m=config.corridor_step_m
        )
    else:
        raise ValueError("candidate_mode must be corridor or brute")
    timing["candidates"] = perf_counter() - start

    n = len(design.centers)
    eta_sb = np.empty(n)
    eta_trunc = np.empty(n)
    start = perf_counter()
    stored = []
    for index in range(n):
        points, unblocked = mirror_unblocked_mask(
            index,
            design.centers,
            design.widths,
            design.heights,
            geometry,
            sun_vector,
            shadow_candidates,
            block_candidates,
            config.mirror_grid,
        )
        eta_sb[index] = float(np.mean(unblocked))
        stored.append((points, unblocked))
    timing["shadow_blocking"] = perf_counter() - start

    start = perf_counter()
    for index, (points, unblocked) in enumerate(stored):
        eta_trunc[index] = truncation_efficiency(
            points,
            unblocked,
            sun_vector,
            geometry.normals[index],
            design.tower_xy,
            config.sun_disk_points,
        )
    timing["truncation"] = perf_counter() - start
    eta_total = eta_sb * geometry.eta_cos * geometry.eta_at * eta_trunc * REFLECTIVITY
    _validate_efficiencies(
        eta_cos=geometry.eta_cos,
        eta_at=geometry.eta_at,
        eta_sb=eta_sb,
        eta_trunc=eta_trunc,
        eta_total=eta_total,
    )
    power = float(dni_kw_m2) * design.areas * eta_total
    if np.any(~np.isfinite(power)) or np.any(power < 0.0):
        raise FloatingPointError("invalid mirror power")
    timing["total"] = sum(timing.values())
    return FieldTimeResult(
        geometry.eta_cos,
        geometry.eta_at,
        eta_sb,
        eta_trunc,
        eta_total,
        power,
        float(dni_kw_m2),
        stats,
        timing,
    )


def evaluate_representative_year(design: FieldDesign, *, precision="STANDARD", detail_time=None):
    rows = []
    detail = None
    time_results = []
    for month, local_time, day, altitude, azimuth, sun, dni in representative_times():
        result = evaluate_time(design, sun, dni, precision=precision)
        summary = result.summary(design.areas)
        rows.append(
            {
                "month": month,
                "local_time_h": local_time,
                "day_from_equinox": day,
                "solar_altitude_rad": altitude,
                "solar_azimuth_rad": azimuth,
                "dni_kw_m2": dni,
                **summary,
                **{f"time_{key}_s": value for key, value in result.timings_s.items()},
                "average_candidates": result.candidate_stats.average_candidates,
                "maximum_candidates": result.candidate_stats.maximum_candidates,
            }
        )
        time_results.append(result)
        if detail_time is not None and (month, local_time) == detail_time:
            detail = result
    return pd.DataFrame(rows), time_results, detail


def aggregate_monthly_and_annual(time_frame):
    metrics = ["eta_total", "eta_cos", "eta_at", "eta_sb", "eta_trunc", "power_kw", "power_per_area_kw_m2"]
    monthly = time_frame.groupby("month", sort=True)[metrics].mean().reset_index()
    annual = monthly[metrics].mean().to_dict()
    annual["power_mw"] = annual["power_kw"] / 1000.0
    return monthly, annual


def mirror_detail_frame(design, result):
    return pd.DataFrame(
        {
            "mirror_id": np.arange(1, len(design.centers) + 1),
            "x_m": design.centers[:, 0],
            "y_m": design.centers[:, 1],
            "z_m": design.centers[:, 2],
            "width_m": design.widths,
            "height_m": design.heights,
            "eta_cos": result.eta_cos,
            "eta_at": result.eta_at,
            "eta_sb": result.eta_sb,
            "eta_trunc": result.eta_trunc,
            "eta_total": result.eta_total,
            "power_kw": result.power_kw,
        }
    )

