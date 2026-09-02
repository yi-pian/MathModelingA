from calibration import calibrate


def test_multistart_calibration_is_bounded_accurate_and_repeatable():
    result = calibrate(
        starts=((20.0, 5.0), (250.0, 20.0)),
        target_dx_m=2e-4,
        final_dx_m=2e-4,
        dt_s=1.0,
    )
    assert 1.0 < result.h_out_w_m2k < 500.0
    assert 1.0 < result.h_skin_w_m2k < 100.0
    assert result.rmse_c < 0.01
    assert result.r2 > 0.9999
    assert result.multistart["h_out_w_m2k"].max() - result.multistart["h_out_w_m2k"].min() < 0.01
    assert result.multistart["h_skin_w_m2k"].max() - result.multistart["h_skin_w_m2k"].min() < 0.001
