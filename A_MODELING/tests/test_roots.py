import numpy as np
import pytest

from core.roots import find_all_roots, scan_sign_changes, solve_bracketed, solve_scalar, solve_system


def test_brentq_known_root():
    result = solve_bracketed(lambda x: x**2 - 4.0, (0.0, 3.0))
    assert result.converged
    assert result.root == pytest.approx(2.0, abs=1e-10)
    assert result.residual < 1e-10


def test_no_root_and_boundary_root():
    with pytest.raises(ValueError):
        solve_bracketed(lambda x: x**2 + 1.0, (-1.0, 1.0))
    result = solve_bracketed(lambda x: x * (x - 2), (0.0, 1.0))
    assert result.root == 0.0 and result.iterations == 0


def test_multiple_roots_and_general_scalar():
    roots = find_all_roots(lambda x: (x + 1) * x * (x - 1), -1.5, 1.5, samples=601)
    assert np.allclose([item.root for item in roots], [-1.0, 0.0, 1.0], atol=1e-8)
    scalar = solve_scalar(lambda x: np.cos(x) - x, bracket=(0.0, 1.0))
    assert scalar.root == pytest.approx(0.7390851332, abs=1e-9)


def test_nonlinear_system():
    result = solve_system(lambda v: [v[0] + v[1] - 3, v[0] - v[1] - 1], [1.0, 1.0])
    assert result.converged
    assert np.allclose(result.root, [2.0, 1.0])

