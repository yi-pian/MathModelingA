"""Explicit unit conversions. Core algorithms should use SI and radians."""

from __future__ import annotations

import numpy as np


def _finite(value):
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError("unit conversion input must contain only finite values")
    result = array
    return float(result) if result.ndim == 0 else result


def degree_to_rad(value):
    return _finite(value) * np.pi / 180.0


def rad_to_degree(value):
    return _finite(value) * 180.0 / np.pi


def kmh_to_ms(value):
    return _finite(value) / 3.6


def ms_to_kmh(value):
    return _finite(value) * 3.6


def mm_to_m(value):
    return _finite(value) / 1000.0


def cm_to_m(value):
    return _finite(value) / 100.0


def minute_to_second(value):
    return _finite(value) * 60.0


def hour_to_second(value):
    return _finite(value) * 3600.0

