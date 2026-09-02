import numpy as np
import pytest

from core.ode import second_order_system, solve_ode, tolerance_convergence


def test_exponential_growth_analytic_solution():
    result = solve_ode(lambda t, y: y, (0, 1), [1], sample_times=np.linspace(0, 1, 11), method="DOP853")
    assert result.success
    assert result.state[0, -1] == pytest.approx(np.e, rel=1e-8)


def test_harmonic_oscillator_and_state_order():
    rhs = second_order_system(lambda t, q, v: -q)
    result = solve_ode(rhs, (0, 2 * np.pi), [1, 0], sample_times=np.linspace(0, 2 * np.pi, 101), method="DOP853")
    assert result.state[0, -1] == pytest.approx(1, abs=1e-7)
    assert result.state[1, -1] == pytest.approx(0, abs=1e-7)


def test_terminal_event_and_tolerance_study():
    def event(t, y): return y[0] - 2
    event.terminal = True
    event.direction = 1
    result = solve_ode(lambda t, y: y, (0, 2), [1], events=event)
    assert result.event_times[0][0] == pytest.approx(np.log(2), rel=1e-7)
    study = tolerance_convergence(lambda t, y: y, (0, 1), [1], np.linspace(0, 1, 21), tolerances=(1e-4, 1e-6, 1e-8))
    assert all(solution.success for solution in study["solutions"])
    assert study["convergent"]
    assert study["max_differences"][-1] <= study["acceptance_threshold"]
    assert study["solutions"][-1].state[0, -1] == pytest.approx(np.e, rel=1e-7)
