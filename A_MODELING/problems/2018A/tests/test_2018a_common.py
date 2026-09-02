"""2018A-specific PDE tests; year in filename prevents pytest name collisions."""

import numpy as np
import pytest

from common import (
    Layer,
    BODY_TEMPERATURE_C,
    assemble_heat_system,
    build_grid,
    duration_above_threshold,
    energy_balance_residual,
    explicit_stable_dt,
    first_crossing_time,
    interface_diagnostics,
    load_official_data,
    make_system,
    official_layers,
    simulate,
    simulate_explicit,
    single_layer_sine_benchmark,
)
from scipy.sparse.linalg import spsolve
from core.units import mm_to_m, minute_to_second


def test_official_workbook_shape_time_and_finite_values():
    materials, measurements = load_official_data()
    assert materials.shape == (4, 5)
    assert measurements.shape == (5401, 2)
    assert np.array_equal(measurements.iloc[:, 0], np.arange(5401))
    assert np.isfinite(measurements.to_numpy(float)).all()


def test_official_grid_hits_all_interfaces_and_total_thickness():
    layers = official_layers()
    grid = build_grid(layers, 1.0e-4)
    expected = np.cumsum([0.0] + [layer.thickness_m for layer in layers])
    assert np.allclose(grid.layer_boundaries_m, expected, atol=1e-15)
    assert np.isclose(np.sum(grid.widths_m), expected[-1], atol=1e-15)


def test_equal_environment_preserves_uniform_temperature():
    system = make_system(37.0, 25.0, 8.0, target_dx_m=2.0e-4)
    result = simulate(system, 100.0, dt_s=1.0)
    assert np.max(np.abs(result.temperature_c - BODY_TEMPERATURE_C)) < 2e-11


def test_cn_obeys_maximum_principle_for_garment_case():
    system = make_system(75.0, 100.0, 8.0, target_dx_m=2.0e-4)
    result = simulate(system, 600.0, dt_s=0.5)
    assert result.temperature_c.min() >= 37.0 - 1e-10
    assert result.temperature_c.max() <= 75.0 + 1e-10


def test_interface_temperature_and_flux_are_continuous():
    system = make_system(75.0, 100.0, 8.0, target_dx_m=1.0e-4)
    result = simulate(system, 300.0, dt_s=1.0)
    diagnostics = interface_diagnostics(system, result.temperature_c[-1])
    assert len(diagnostics) == 3
    assert diagnostics["temperature_residual_c"].abs().max() < 1e-12
    assert diagnostics["heat_flux_residual_w_m2"].abs().max() < 1e-12


def test_cn_energy_balance_residual_is_roundoff_scale():
    system = make_system(75.0, 100.0, 8.0, target_dx_m=2.0e-4)
    result = simulate(system, 100.0, dt_s=1.0)
    residual = energy_balance_residual(system, result)
    assert np.max(np.abs(residual)) < 2e-8


def test_single_layer_cn_matches_analytic_solution():
    benchmark = single_layer_sine_benchmark(final_time_s=0.2, nx=101, dt_s=0.001, method="cn")
    assert benchmark["max_error"] < 2e-5


def test_single_layer_explicit_matches_analytic_solution():
    benchmark = single_layer_sine_benchmark(final_time_s=0.02, nx=51, dt_s=1.0e-4, method="explicit")
    assert benchmark["r"] <= 0.5
    assert benchmark["max_error"] < 2e-4


def test_full_model_explicit_and_cn_short_time_agree():
    system = make_system(75.0, 100.0, 8.0, target_dx_m=5.0e-4)
    dt = explicit_stable_dt(system, safety=0.8)
    explicit = simulate_explicit(system, 2.0, dt_s=dt, store_every=max(1, int(round(0.1 / dt))))
    cn = simulate(system, 2.0, dt_s=dt, store_every=max(1, int(round(0.1 / dt))))
    assert np.max(np.abs(explicit.temperature_c[-1] - cn.temperature_c[-1])) < 0.02


def test_explicit_rejects_unstable_time_step():
    system = make_system(75.0, 100.0, 8.0, target_dx_m=5.0e-4)
    with pytest.raises(ValueError, match="exceeds stable limit"):
        simulate_explicit(system, 1.0, explicit_stable_dt(system) * 1.01)


def test_threshold_crossing_and_duration_are_interpolated():
    time = np.array([0.0, 10.0, 20.0])
    values = np.array([40.0, 45.0, 46.0])
    assert np.isclose(first_crossing_time(time, values, 44.0), 8.0)
    assert np.isclose(duration_above_threshold(time, values, 44.0), 12.0)


def test_material_thickness_bounds_are_enforced():
    with pytest.raises(ValueError):
        official_layers(d_ii_m=0.0005)
    with pytest.raises(ValueError):
        official_layers(d_iv_m=0.0065)


def test_units_mm_and_minutes_are_converted_to_si():
    assert np.isclose(mm_to_m(5.5), 0.0055)
    assert np.isclose(minute_to_second(90), 5400.0)


def test_two_layer_steady_solution_matches_manual_resistance_network():
    layers = (
        Layer("A", 1000.0, 1000.0, 0.1, 0.002),
        Layer("B", 800.0, 1200.0, 0.05, 0.002),
    )
    grid = build_grid(layers, 0.0002)
    system = assemble_heat_system(grid, 100.0, 10.0, 20.0, body_temperature_c=0.0)
    steady = spsolve(system.operator, -system.source_c_per_s)
    expected_flux = 100.0 / (1 / 10.0 + 0.002 / 0.1 + 0.002 / 0.05 + 1 / 20.0)
    q_outer = system.outer_conductance_w_m2k * (100.0 - steady[0])
    q_skin = system.skin_conductance_w_m2k * steady[-1]
    diagnostics = interface_diagnostics(system, steady)
    expected_interface = 100.0 - expected_flux * (1 / 10.0 + 0.002 / 0.1)
    assert np.isclose(q_outer, expected_flux, rtol=1e-12)
    assert np.isclose(q_skin, expected_flux, rtol=1e-12)
    assert np.isclose(diagnostics.loc[0, "temperature_left_c"], expected_interface, rtol=1e-12)
    assert abs(diagnostics.loc[0, "temperature_residual_c"]) < 1e-12


def test_sine_benchmark_spatial_refinement_reduces_error():
    errors = []
    for nx in (26, 51, 101):
        dx = 0.01 / (nx - 1)
        dt = 0.1 * dx**2 / 1e-5
        errors.append(single_layer_sine_benchmark(final_time_s=0.02, nx=nx, dt_s=dt, method="cn")["max_error"])
    assert errors[2] < errors[1] < errors[0]


def test_sine_benchmark_time_refinement_is_consistent():
    coarse = single_layer_sine_benchmark(final_time_s=0.02, nx=101, dt_s=0.002, method="cn")
    medium = single_layer_sine_benchmark(final_time_s=0.02, nx=101, dt_s=0.001, method="cn")
    fine = single_layer_sine_benchmark(final_time_s=0.02, nx=101, dt_s=0.0005, method="cn")
    assert abs(coarse["numerical"][50] - fine["numerical"][50]) > abs(medium["numerical"][50] - fine["numerical"][50])
