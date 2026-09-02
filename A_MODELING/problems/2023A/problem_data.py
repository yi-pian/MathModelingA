"""Official constants, input loading, and precision levels for CUMCM 2023A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_DIR = ROOT / "data" / "2023A" / "official" / "A"
RESULT_DIR = ROOT / "results" / "2023A"

LATITUDE_DEG = 39.4
LONGITUDE_DEG = 98.5
ALTITUDE_KM = 3.0
FIELD_RADIUS_M = 350.0
TOWER_EXCLUSION_M = 100.0
RECEIVER_CENTER_Z_M = 80.0
RECEIVER_HEIGHT_M = 8.0
RECEIVER_RADIUS_M = 3.5
REFLECTIVITY = 0.92
SOLAR_CONSTANT_KW_M2 = 1.366
SOLAR_HALF_ANGLE_RAD = 4.65e-3
RATED_POWER_MW = 60.0
LOCAL_TIMES_H = np.array([9.0, 10.5, 12.0, 13.5, 15.0])


@dataclass(frozen=True)
class PrecisionConfig:
    name: str
    mirror_grid: int
    sun_disk_points: int
    corridor_step_m: float


PRECISION = {
    "FAST": PrecisionConfig("FAST", mirror_grid=3, sun_disk_points=7, corridor_step_m=7.0),
    "STANDARD": PrecisionConfig("STANDARD", mirror_grid=5, sun_disk_points=13, corridor_step_m=4.0),
    "FINAL": PrecisionConfig("FINAL", mirror_grid=9, sun_disk_points=49, corridor_step_m=2.0),
}


@dataclass(frozen=True)
class FieldDesign:
    centers: np.ndarray
    widths: np.ndarray
    heights: np.ndarray
    tower_xy: np.ndarray

    def __post_init__(self):
        centers = np.asarray(self.centers, dtype=float)
        widths = np.asarray(self.widths, dtype=float)
        heights = np.asarray(self.heights, dtype=float)
        tower_xy = np.asarray(self.tower_xy, dtype=float)
        n = len(centers)
        if centers.shape != (n, 3) or widths.shape != (n,) or heights.shape != (n,):
            raise ValueError("centers must be (N,3), widths/heights must be (N,)")
        if tower_xy.shape != (2,) or n == 0:
            raise ValueError("tower_xy must be (2,) and the field must be non-empty")
        if not all(np.all(np.isfinite(x)) for x in (centers, widths, heights, tower_xy)):
            raise ValueError("field design values must be finite")
        if np.any(widths <= 0) or np.any(heights <= 0):
            raise ValueError("mirror dimensions must be positive")
        object.__setattr__(self, "centers", centers)
        object.__setattr__(self, "widths", widths)
        object.__setattr__(self, "heights", heights)
        object.__setattr__(self, "tower_xy", tower_xy)

    @property
    def areas(self):
        return self.widths * self.heights

    @property
    def receiver_center(self):
        return np.array([self.tower_xy[0], self.tower_xy[1], RECEIVER_CENTER_Z_M])


def load_q1_design() -> FieldDesign:
    """Load the official attachment without modifying it."""
    path = OFFICIAL_DIR / "附件.xlsx"
    frame = pd.read_excel(path)
    expected = ["x坐标 (m)", "y坐标 (m)"]
    if frame.columns.tolist() != expected:
        raise ValueError(f"unexpected attachment columns: {frame.columns.tolist()}")
    xy = frame.to_numpy(float)
    if xy.shape != (1745, 2) or not np.all(np.isfinite(xy)):
        raise ValueError(f"unexpected Q1 coordinates shape/data: {xy.shape}")
    centers = np.column_stack((xy, np.full(len(xy), 4.0)))
    return FieldDesign(centers, np.full(len(xy), 6.0), np.full(len(xy), 6.0), np.zeros(2))


def precision_config(level: str | PrecisionConfig) -> PrecisionConfig:
    if isinstance(level, PrecisionConfig):
        return level
    try:
        return PRECISION[str(level).upper()]
    except KeyError as error:
        raise ValueError("precision must be FAST, STANDARD, or FINAL") from error
