"""Solar position and DNI using the formulas supplied in the 2023A statement."""

from __future__ import annotations

from datetime import date

import numpy as np

from core.units import degree_to_rad
from problem_data import ALTITUDE_KM, LATITUDE_DEG, LOCAL_TIMES_H, SOLAR_CONSTANT_KW_M2


MONTH_DAYS_FROM_EQUINOX = np.array([(date(2023, month, 21) - date(2023, 3, 21)).days for month in range(1, 13)])


def solar_declination(day_from_equinox):
    """Return solar declination in radians, exactly following the statement."""
    day = np.asarray(day_from_equinox, dtype=float)
    sin_delta = np.sin(2.0 * np.pi * day / 365.0) * np.sin(degree_to_rad(23.45))
    return np.arcsin(sin_delta)


def solar_position(day_from_equinox, local_time_h, latitude_deg=LATITUDE_DEG):
    """Return altitude, south-west-positive azimuth, and observer-to-sun ENU vector."""
    delta = solar_declination(day_from_equinox)
    phi = degree_to_rad(float(latitude_deg))
    omega = np.pi * (np.asarray(local_time_h, dtype=float) - 12.0) / 12.0
    sin_alpha = np.cos(delta) * np.cos(phi) * np.cos(omega) + np.sin(delta) * np.sin(phi)
    if np.any((sin_alpha < -1.0 - 1e-12) | (sin_alpha > 1.0 + 1e-12)):
        raise FloatingPointError("solar altitude sine outside [-1,1]")
    alpha = np.arcsin(np.minimum(1.0, np.maximum(-1.0, sin_alpha)))
    cos_alpha = np.cos(alpha)
    if np.any(cos_alpha <= 1e-12):
        raise ValueError("solar azimuth is undefined at the zenith")
    cos_gamma = (np.sin(delta) - np.sin(alpha) * np.sin(phi)) / (cos_alpha * np.cos(phi))
    sin_gamma = np.cos(delta) * np.sin(omega) / cos_alpha
    gamma = np.arctan2(sin_gamma, cos_gamma)
    vector = np.stack(
        (-cos_alpha * np.sin(gamma), -cos_alpha * np.cos(gamma), np.sin(alpha)), axis=-1
    )
    norm_error = np.max(np.abs(np.linalg.norm(vector, axis=-1) - 1.0))
    if norm_error > 2e-12:
        raise FloatingPointError(f"solar vector normalization residual {norm_error:g}")
    return alpha, gamma, vector


def direct_normal_irradiance(altitude_rad, altitude_km=ALTITUDE_KM):
    """DNI in kW/m² from the empirical formula in the statement."""
    altitude = np.asarray(altitude_rad, dtype=float)
    sin_alpha = np.sin(altitude)
    if np.any(sin_alpha <= 0.0):
        raise ValueError("DNI is defined here only while the sun is above the horizon")
    h = float(altitude_km)
    a = 0.4237 - 0.00821 * (6.0 - h) ** 2
    b = 0.5055 + 0.00595 * (6.5 - h) ** 2
    c = 0.2711 + 0.01858 * (2.5 - h) ** 2
    dni = SOLAR_CONSTANT_KW_M2 * (a + b * np.exp(-c / sin_alpha))
    if np.any(~np.isfinite(dni)) or np.any(dni < 0.0):
        raise FloatingPointError("invalid DNI")
    return dni


def representative_times():
    """Return month, local time, equinox-relative day, sun data and DNI for all 60 points."""
    rows = []
    for month, day in enumerate(MONTH_DAYS_FROM_EQUINOX, start=1):
        for local_time in LOCAL_TIMES_H:
            alpha, gamma, vector = solar_position(day, local_time)
            rows.append((month, float(local_time), int(day), float(alpha), float(gamma), vector, float(direct_normal_irradiance(alpha))))
    return rows
