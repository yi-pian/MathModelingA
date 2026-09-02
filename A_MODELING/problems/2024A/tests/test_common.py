import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from common import (
    ArchimedeanSpiral, BODY_HANDLE_DISTANCE_M, HEAD_HANDLE_DISTANCE_M,
    LINK_LENGTHS_M, TurnaroundPath, build_path_chain, build_spiral_chain,
    head_theta_at_time, link_error_statistics, rectangle_from_center,
    rectangle_signed_clearance, velocity_constraint_residuals,
)


def test_spiral_arc_formula_and_inverse():
    spiral = ArchimedeanSpiral(0.55)
    theta = 12.3
    analytic = spiral.arc_primitive(theta) - spiral.arc_primitive(2.1)
    assert analytic == pytest.approx(spiral.arc_length_by_quad(2.1, theta), abs=2e-11)
    recovered, residual = spiral.theta_from_arc(spiral.arc_primitive(theta))
    assert recovered == pytest.approx(theta, abs=2e-11) and residual < 1e-10
    assert spiral.theta_from_arc_fast(spiral.arc_primitive(theta)) == pytest.approx(theta, abs=2e-10)


def test_initial_head_and_chain_constraints():
    theta, residual = head_theta_at_time(0)
    assert theta == pytest.approx(32 * np.pi, abs=1e-10) and residual < 1e-9
    state = build_spiral_chain(theta)
    stats = link_error_statistics(state.positions)
    assert stats.maximum < 2e-10
    assert np.max(np.abs(velocity_constraint_residuals(state))) < 2e-10
    assert np.linalg.norm(state.positions[1] - state.positions[0]) == pytest.approx(HEAD_HANDLE_DISTANCE_M, abs=2e-10)
    assert np.linalg.norm(state.positions[-1] - state.positions[-2]) == pytest.approx(BODY_HANDLE_DISTANCE_M, abs=2e-10)


@pytest.mark.parametrize("second_center, expected_sign", [
    ((3.0, 0.0), 1),
    ((2.0, 0.0), 0),
    ((1.5, 0.0), -1),
])
def test_rectangle_separation_touching_and_overlap(second_center, expected_sign):
    first = rectangle_from_center((0, 0), 0.0, 2.0, 0.30)
    second = rectangle_from_center(second_center, 0.0, 2.0, 0.30)
    clearance = rectangle_signed_clearance(first, second)
    if expected_sign > 0: assert clearance > 0
    elif expected_sign < 0: assert clearance < 0
    else: assert clearance == pytest.approx(0.0, abs=1e-12)


def test_rectangle_parallel_and_floating_boundary():
    first = rectangle_from_center((0, 0), 0.0, 2.0, 0.30)
    separated = rectangle_from_center((0, 0.300000001), 1e-10, 2.0, 0.30)
    overlapping = rectangle_from_center((0, 0.299999999), -1e-10, 2.0, 0.30)
    assert rectangle_signed_clearance(first, separated) > 0
    assert rectangle_signed_clearance(first, overlapping) < 0


def test_turn_path_geometry_and_chain():
    path = TurnaroundPath()
    assert path.radius1 / path.radius2 == pytest.approx(2.0)
    assert np.allclose(path.point(0), path.entry, atol=1e-10)
    assert np.allclose(path.point(path.turn_length), path.exit, atol=1e-10)
    assert path.max_turn_radius() <= 4.5 + 1e-10
    residuals = path.continuity_residuals()
    assert max(residuals["position"]) < 3e-7
    assert max(residuals["tangent"]) < 3e-7
    state = build_path_chain(path, 5.0)
    assert link_error_statistics(state.positions).maximum < 3e-9
    assert np.max(np.abs(velocity_constraint_residuals(state))) < 3e-9
