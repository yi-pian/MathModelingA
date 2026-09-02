"""Official constants for CUMCM 2025 problem A (SI units)."""

from __future__ import annotations

import numpy as np

GRAVITY_M_S2 = 9.8
MISSILE_SPEED_M_S = 300.0
UAV_SPEED_BOUNDS_M_S = (70.0, 140.0)
MIN_DROP_GAP_S = 1.0
CLOUD_RADIUS_M = 10.0
CLOUD_LIFETIME_S = 20.0
CLOUD_DESCENT_M_S = 3.0

DECOY_POSITION_M = np.array([0.0, 0.0, 0.0])
TARGET_BASE_CENTER_M = np.array([0.0, 200.0, 0.0])
TARGET_CENTER_M = np.array([0.0, 200.0, 5.0])
TARGET_RADIUS_M = 7.0
TARGET_HEIGHT_M = 10.0

MISSILE_INITIAL_M = {
    "M1": np.array([20000.0, 0.0, 2000.0]),
    "M2": np.array([19000.0, 600.0, 2100.0]),
    "M3": np.array([18000.0, -600.0, 1900.0]),
}

UAV_INITIAL_M = {
    "FY1": np.array([17800.0, 0.0, 1800.0]),
    "FY2": np.array([12000.0, 1400.0, 1400.0]),
    "FY3": np.array([6000.0, -3000.0, 700.0]),
    "FY4": np.array([11000.0, 2000.0, 1800.0]),
    "FY5": np.array([13000.0, -2000.0, 1300.0]),
}
