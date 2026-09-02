from pathlib import Path
import sys

import numpy as np

PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems" / "2023A"
sys.path.insert(0, str(PROBLEM_DIR))
# Pytest also collects historical problem-local tests. Their flat modules have names
# such as ``problem_data``; evict those names so this year's test imports its own files.
for _module_name in ("problem_data", "solar", "heliostat", "truncation", "shadow_blocking", "field", "layout"):
    sys.modules.pop(_module_name, None)

from heliostat import atmospheric_transmittance, mirror_geometry, reflected_direction, scalar_ideal_normal
from problem_data import FieldDesign
from problem_data import RESULT_DIR
from field import evaluate_time
from layout import apply_radial_zones, constraint_report, generate_hexagonal_layout
from shadow_blocking import corridor_candidates, rays_intersect_rectangles
from solar import direct_normal_irradiance, solar_position
from truncation import rays_hit_receiver_cylinder


def test_solar_direction_is_unit_and_morning_afternoon_are_mirrored():
    alpha_am, gamma_am, sun_am = solar_position(0, 9.0)
    alpha_pm, gamma_pm, sun_pm = solar_position(0, 15.0)
    assert np.isclose(np.linalg.norm(sun_am), 1.0, atol=1e-12)
    assert np.isclose(np.linalg.norm(sun_pm), 1.0, atol=1e-12)
    assert np.isclose(alpha_am, alpha_pm, atol=1e-12)
    assert gamma_am < 0.0 < gamma_pm
    assert sun_am[0] > 0.0 > sun_pm[0]
    assert np.isclose(sun_am[1], sun_pm[1], atol=1e-12)
    assert direct_normal_irradiance(alpha_am) > 0.0


def test_vectorized_normals_match_scalar_and_obey_reflection_law():
    centers = np.array([[120.0, 0.0, 4.0], [-80.0, 40.0, 5.0], [0.0, -150.0, 3.0]])
    _, _, sun = solar_position(0, 10.5)
    receiver = np.array([0.0, 0.0, 80.0])
    geometry = mirror_geometry(centers, receiver, sun)
    for i in range(len(centers)):
        scalar = scalar_ideal_normal(sun, geometry.receiver_directions[i])
        assert np.allclose(geometry.normals[i], scalar, atol=1e-13)
    reflected = reflected_direction(-sun, geometry.normals)
    assert np.max(np.linalg.norm(reflected - geometry.receiver_directions, axis=1)) < 2e-12
    assert np.max(np.abs(np.linalg.norm(geometry.normals, axis=1) - 1.0)) < 1e-12
    assert np.all((geometry.eta_cos >= 0.0) & (geometry.eta_cos <= 1.0))


def test_atmospheric_transmittance_uses_three_dimensional_distance():
    center = np.array([[0.0, 0.0, 4.0]])
    receiver = np.array([0.0, 0.0, 80.0])
    _, _, sun = solar_position(0, 12.0)
    geometry = mirror_geometry(center, receiver, sun)
    assert np.isclose(geometry.distances_m[0], 76.0)
    assert np.isclose(geometry.eta_at[0], atmospheric_transmittance(np.array([76.0]))[0])


def test_rectangle_ray_cases_separated_full_partial_edge_and_parallel():
    center = np.array([[2.0, 0.0, 0.0]])
    normal = np.array([[-1.0, 0.0, 0.0]])
    width_axis = np.array([[0.0, 1.0, 0.0]])
    height_axis = np.array([[0.0, 0.0, 1.0]])
    widths = np.array([1.0])
    heights = np.array([2.0])
    origins = np.array([[0.0, -0.75, 0.0], [0.0, -0.25, 0.0], [0.0, 0.25, 0.0], [0.0, 0.75, 0.0]])
    hit = rays_intersect_rectangles(origins, np.array([1.0, 0.0, 0.0]), center, normal, width_axis, height_axis, widths, heights)
    assert hit.tolist() == [False, True, True, False]  # 50% partial coverage of these samples
    edge = rays_intersect_rectangles(np.array([[0.0, 0.5, 0.0]]), np.array([1.0, 0.0, 0.0]), center, normal, width_axis, height_axis, widths, heights)
    assert not edge[0]  # exact edge contact has zero area
    away = rays_intersect_rectangles(np.array([[0.0, 0.0, 0.0]]), np.array([-1.0, 0.0, 0.0]), center, normal, width_axis, height_axis, widths, heights)
    assert not away[0]
    parallel = rays_intersect_rectangles(np.array([[0.0, 0.0, 0.0]]), np.array([0.0, 1.0, 0.0]), center, normal, width_axis, height_axis, widths, heights)
    assert not parallel[0]


def test_receiver_cylinder_full_partial_and_miss_cases():
    origins = np.array([[10.0, y, 80.0] for y in (-4.0, -3.0, 0.0, 3.0, 4.0)])
    directions = np.tile(np.array([-1.0, 0.0, 0.0]), (5, 1))
    hit = rays_hit_receiver_cylinder(origins, directions, np.zeros(2))
    assert hit.tolist() == [False, True, True, True, False]
    assert np.mean(hit) == 0.6
    assert np.all(rays_hit_receiver_cylinder(origins[1:4], directions[1:4], np.zeros(2)))
    assert not np.any(rays_hit_receiver_cylinder(origins, -directions, np.zeros(2)))


def test_corridor_candidates_do_not_miss_brute_force_hits_on_random_small_field():
    rng = np.random.default_rng(2023)
    angle = rng.uniform(0.0, 2.0 * np.pi, 30)
    radius = rng.uniform(105.0, 300.0, 30)
    centers = np.column_stack((radius * np.cos(angle), radius * np.sin(angle), rng.uniform(3.0, 5.0, 30)))
    widths = rng.uniform(3.0, 7.0, 30)
    heights = rng.uniform(2.0, widths)
    _, _, sun = solar_position(80, 9.0)
    geometry = mirror_geometry(centers, np.array([0.0, 0.0, 80.0]), sun)
    shadow, block, _ = corridor_candidates(centers, widths, heights, sun, np.zeros(2), step_m=4.0)
    all_indices = np.arange(len(centers))
    for i in range(len(centers)):
        origins = centers[i][None, :]
        others = all_indices[all_indices != i]
        shadow_hit = rays_intersect_rectangles(origins, sun, centers[others], geometry.normals[others], geometry.width_axes[others], geometry.height_axes[others], widths[others], heights[others])
        block_hit = rays_intersect_rectangles(origins, geometry.receiver_directions[i], centers[others], geometry.normals[others], geometry.width_axes[others], geometry.height_axes[others], widths[others], heights[others])
        if shadow_hit[0]:
            # Identify individual true blockers and require each to survive screening.
            for j in others:
                one = rays_intersect_rectangles(origins, sun, centers[[j]], geometry.normals[[j]], geometry.width_axes[[j]], geometry.height_axes[[j]], widths[[j]], heights[[j]])
                if one[0]:
                    assert j in set(shadow[i])
        if block_hit[0]:
            for j in others:
                one = rays_intersect_rectangles(origins, geometry.receiver_directions[i], centers[[j]], geometry.normals[[j]], geometry.width_axes[[j]], geometry.height_axes[[j]], widths[[j]], heights[[j]])
                if one[0]:
                    assert j in set(block[i])


def test_field_design_rejects_bad_shapes():
    try:
        FieldDesign(np.zeros((2, 2)), np.ones(2), np.ones(2), np.zeros(2))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid center shape was accepted")


def test_corridor_and_brute_field_efficiencies_match_for_sampled_small_field():
    centers = np.array(
        [
            [-120.0, -80.0, 4.0],
            [-100.0, -70.0, 4.0],
            [-60.0, 120.0, 4.0],
            [20.0, -150.0, 4.0],
            [100.0, 80.0, 4.0],
            [140.0, -20.0, 4.0],
        ]
    )
    design = FieldDesign(centers, np.full(6, 6.0), np.full(6, 6.0), np.zeros(2))
    alpha, _, sun = solar_position(30, 9.0)
    dni = float(direct_normal_irradiance(alpha))
    fast = evaluate_time(design, sun, dni, precision="FAST", candidate_mode="corridor")
    brute = evaluate_time(design, sun, dni, precision="FAST", candidate_mode="brute")
    assert np.array_equal(fast.eta_sb, brute.eta_sb)
    assert np.allclose(fast.eta_total, brute.eta_total, atol=1e-14)


def test_final_q2_q3_geometric_constraints_and_excel_roundtrip():
    q2 = generate_hexagonal_layout([0.0, 50.0], 6.5, 6.5, 3.3, spacing_gap=0.05)
    q2_report = constraint_report(q2, rated_power_mw=60.89583835926479)
    assert q2_report["all_geometric_constraints_pass"]
    assert q2_report["rated_power_margin_mw"] > 0.0
    q3, _ = apply_radial_zones(
        q2,
        (0.25, 0.50, 0.75),
        (6.54, 6.48, 6.42, 6.36),
        (6.54, 6.48, 6.42, 6.36),
        tuple(value / 2.0 + 0.05 for value in (6.54, 6.48, 6.42, 6.36)),
    )
    q3_report = constraint_report(q3, rated_power_mw=60.65629578501832)
    assert q3_report["all_geometric_constraints_pass"]
    assert q3_report["rated_power_margin_mw"] > 0.0
    import pandas as pd

    for filename, design in (("result2.xlsx", q2), ("result3.xlsx", q3)):
        frame = pd.read_excel(RESULT_DIR / filename)
        assert frame.shape == (len(design.centers), 8)
        assert frame.iloc[:, 2].tolist() == list(range(1, len(design.centers) + 1))
        assert np.all(np.isfinite(frame.iloc[:, 2:].to_numpy(float)))
        expected = np.column_stack((design.widths, design.heights, design.centers))
        assert np.allclose(frame.iloc[:, 3:].to_numpy(float), expected, rtol=0.0, atol=1e-12)
