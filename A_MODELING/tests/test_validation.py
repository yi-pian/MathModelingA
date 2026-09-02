import numpy as np

from core.validation import ValidationReport, check_bounds, check_constraints, check_convergence, check_finite, check_monotonic_time, check_residual, standard_report


def test_individual_checks_and_failures():
    assert check_finite([1, 2]) and not check_finite([1, np.nan])
    assert check_bounds([0, 1], 0, 1) and not check_bounds([2], 0, 1)
    assert check_constraints([0, 1], sense="ge") and check_constraints([0, 1e-9], sense="eq")
    assert check_monotonic_time([0, 1, 2]) and not check_monotonic_time([0, 1, 1])
    assert check_residual([1e-10], tolerance=1e-8)
    assert check_convergence([0.1, 0.03, 0.008])


def test_report_render_and_manual_marker():
    report = standard_report(arrays=[1, 2], parameters=[0.5], bounds=([0], [1]), constraints=[0.1], residual=[1e-10], time=[0, 1])
    text = report.render()
    assert report.passed and "MANUAL CHECK REQUIRED" in text and "Finite values" in text
    failed = ValidationReport().add("Example", False)
    assert not failed.passed and "FAIL" in failed.render()

