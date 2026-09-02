import numpy as np
import pytest

from core.units import cm_to_m, degree_to_rad, hour_to_second, kmh_to_ms, minute_to_second, mm_to_m, ms_to_kmh, rad_to_degree


def test_angle_round_trip():
    angles = np.array([-180.0, 0.0, 45.0, 360.0])
    assert np.allclose(rad_to_degree(degree_to_rad(angles)), angles)
    assert degree_to_rad(180.0) == pytest.approx(np.pi)


def test_speed_and_length_conversions():
    assert kmh_to_ms(36.0) == pytest.approx(10.0)
    assert ms_to_kmh(10.0) == pytest.approx(36.0)
    assert mm_to_m(1000.0) == pytest.approx(1.0)
    assert cm_to_m(100.0) == pytest.approx(1.0)


def test_time_conversions_and_nonfinite_rejection():
    assert minute_to_second(2.0) == pytest.approx(120.0)
    assert hour_to_second(2.0) == pytest.approx(7200.0)
    with pytest.raises(ValueError):
        kmh_to_ms(np.inf)

