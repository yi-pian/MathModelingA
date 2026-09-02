"""Problem-specific geometry and kinematics for CUMCM 2024A.

The reusable numerical primitives come from ``core``.  Dragon geometry, chain
ordering, official-template mappings, and the S-turn path stay local to 2024A.
All internal lengths are metres, times seconds, and angles radians.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

PROJECT_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.geometry import normalize
from core.integration import integrate_function
from core.roots import solve_bracketed


N_BENCHES = 223
N_HANDLES = 224
HEAD_BOARD_LENGTH_M = 3.41
BODY_BOARD_LENGTH_M = 2.20
BOARD_WIDTH_M = 0.30
HOLE_OFFSET_M = 0.275
HEAD_HANDLE_DISTANCE_M = HEAD_BOARD_LENGTH_M - 2.0 * HOLE_OFFSET_M
BODY_HANDLE_DISTANCE_M = BODY_BOARD_LENGTH_M - 2.0 * HOLE_OFFSET_M
LINK_LENGTHS_M = np.array([HEAD_HANDLE_DISTANCE_M] + [BODY_HANDLE_DISTANCE_M] * (N_HANDLES - 2), dtype=float)
TURN_RADIUS_M = 4.5
DEFAULT_EPS = 1e-11

NODE_LABELS = ["龙头"] + [f"第{i}节龙身" for i in range(1, 222)] + ["龙尾", "龙尾（后）"]
SELECTED_NODE_INDICES = np.array([0, 1, 51, 101, 151, 201, 223], dtype=int)


@dataclass(frozen=True)
class ChainState:
    coordinates: np.ndarray
    positions: np.ndarray
    tangents: np.ndarray
    speeds: np.ndarray


@dataclass(frozen=True)
class LinkErrorStats:
    maximum: float
    mean: float
    percentile95: float
    errors: np.ndarray


@dataclass(frozen=True)
class OrientedRectangle:
    center: np.ndarray
    axis_long: np.ndarray
    axis_wide: np.ndarray
    half_length: float
    half_width: float
    vertices: np.ndarray
    aabb_min: np.ndarray
    aabb_max: np.ndarray


@dataclass(frozen=True)
class CollisionResult:
    clearance: float
    pair: tuple[int, int] | None
    candidates: int


class ArchimedeanSpiral:
    def __init__(self, pitch_m: float):
        if not np.isfinite(pitch_m) or pitch_m <= 0:
            raise ValueError("pitch_m must be finite and positive")
        self.pitch_m = float(pitch_m)
        self.a = self.pitch_m / (2.0 * np.pi)

    def point(self, theta: float) -> np.ndarray:
        theta = float(theta)
        return self.a * theta * np.array([np.cos(theta), np.sin(theta)])

    def derivative(self, theta: float) -> np.ndarray:
        theta = float(theta)
        return self.a * np.array([np.cos(theta) - theta * np.sin(theta), np.sin(theta) + theta * np.cos(theta)])

    def inward_tangent(self, theta: float) -> np.ndarray:
        return -normalize(self.derivative(theta))

    def outward_symmetric_point(self, theta: float) -> np.ndarray:
        return -self.point(theta)

    def outward_symmetric_tangent(self, theta: float) -> np.ndarray:
        return -normalize(self.derivative(theta))

    def arc_primitive(self, theta: float | np.ndarray):
        theta = np.asarray(theta, dtype=float)
        value = 0.5 * self.a * (theta * np.sqrt(1.0 + theta**2) + np.arcsinh(theta))
        return float(value) if value.ndim == 0 else value

    def arc_length_by_quad(self, theta0: float, theta1: float) -> float:
        lo, hi = sorted((float(theta0), float(theta1)))
        return integrate_function(lambda value: self.a * np.sqrt(1.0 + value**2), lo, hi, epsabs=1e-12, epsrel=1e-12)["value"]

    def theta_from_arc(self, target_arc_m: float, *, upper_hint: float | None = None):
        """High-accuracy inverse using the shared bracketed root wrapper."""
        target = float(target_arc_m)
        if target < 0 or not np.isfinite(target):
            raise ValueError("target arc length must be finite and nonnegative")
        if target == 0:
            return 0.0, 0.0
        upper = float(upper_hint) if upper_hint is not None else max(1.0, np.sqrt(2.0 * target / self.a) + 1.0)
        while self.arc_primitive(upper) < target:
            upper *= 1.5
        result = solve_bracketed(lambda theta: self.arc_primitive(theta) - target, (0.0, upper), xtol=1e-12, rtol=1e-12)
        if not result.converged:
            raise RuntimeError(result.message)
        return float(result.root), float(result.residual)

    def theta_from_arc_fast(self, target_arc_m: float) -> float:
        """Safeguarded Newton inverse used inside repeated composite-path calls."""
        target = float(target_arc_m)
        if target < 0 or not np.isfinite(target):
            raise ValueError("target arc length must be finite and nonnegative")
        if target == 0:
            return 0.0
        scaled = target / self.a
        theta = scaled if scaled < 0.8 else np.sqrt(2.0 * scaled)
        theta = max(theta, 1e-12)
        for _ in range(12):
            residual = self.arc_primitive(theta) - target
            update = residual / (self.a * np.sqrt(1.0 + theta**2))
            candidate = theta - update
            if candidate <= 0:
                candidate = theta / 2.0
            theta = candidate
            if abs(residual) <= 2e-13 * max(1.0, target):
                break
        if abs(self.arc_primitive(theta) - target) > 2e-10 * max(1.0, target):
            theta, _ = self.theta_from_arc(target, upper_hint=max(1.0, theta * 1.2))
        return float(theta)


def head_theta_at_time(time_s: float, *, pitch_m=0.55, head_speed_m_s=1.0, initial_theta=32.0 * np.pi):
    spiral = ArchimedeanSpiral(pitch_m)
    target = spiral.arc_primitive(initial_theta) - head_speed_m_s * float(time_s)
    if target < 0:
        raise ValueError("head has passed the spiral origin")
    theta, residual = spiral.theta_from_arc(target, upper_hint=initial_theta)
    return theta, residual


def _next_spiral_theta(spiral: ArchimedeanSpiral, previous_theta: float, target_length_m: float):
    previous_point = spiral.point(previous_theta)

    def equation(theta):
        difference = spiral.point(theta) - previous_point
        return float(np.dot(difference, difference) - target_length_m**2)

    local_scale = target_length_m / (spiral.a * np.sqrt(1.0 + previous_theta**2))
    delta = max(0.75 * local_scale, 1e-5)
    upper = previous_theta + delta
    while equation(upper) < 0:
        delta *= 1.25
        if delta > np.pi:
            raise RuntimeError("failed to bracket the nearest outward spiral handle")
        upper = previous_theta + delta
    result = solve_bracketed(equation, (previous_theta, upper), xtol=1e-12, rtol=1e-12)
    if not result.converged:
        raise RuntimeError(result.message)
    return float(result.root), float(result.residual)


def propagate_speeds(positions: np.ndarray, tangents: np.ndarray, head_speed_m_s: float):
    positions = np.asarray(positions, float)
    tangents = np.asarray(tangents, float)
    if positions.shape != (N_HANDLES, 2) or tangents.shape != positions.shape:
        raise ValueError("positions and tangents must have shape (224, 2)")
    speeds = np.empty(N_HANDLES, dtype=float)
    speeds[0] = float(head_speed_m_s)
    for index in range(1, N_HANDLES):
        link = positions[index] - positions[index - 1]
        numerator = float(np.dot(link, tangents[index - 1]))
        denominator = float(np.dot(link, tangents[index]))
        if abs(denominator) <= 1e-12:
            raise RuntimeError(f"singular velocity propagation at node {index}")
        speeds[index] = speeds[index - 1] * numerator / denominator
        if not np.isfinite(speeds[index]) or speeds[index] <= 0:
            raise RuntimeError(f"nonphysical node speed at node {index}: {speeds[index]}")
    return speeds


def build_spiral_chain(theta_head: float, *, pitch_m=0.55, head_speed_m_s=1.0) -> ChainState:
    spiral = ArchimedeanSpiral(pitch_m)
    theta = np.empty(N_HANDLES, dtype=float)
    positions = np.empty((N_HANDLES, 2), dtype=float)
    tangents = np.empty_like(positions)
    theta[0] = float(theta_head)
    positions[0] = spiral.point(theta[0])
    tangents[0] = spiral.inward_tangent(theta[0])
    for index, target_length in enumerate(LINK_LENGTHS_M, start=1):
        theta[index], _ = _next_spiral_theta(spiral, theta[index - 1], float(target_length))
        positions[index] = spiral.point(theta[index])
        tangents[index] = spiral.inward_tangent(theta[index])
    speeds = propagate_speeds(positions, tangents, head_speed_m_s)
    return ChainState(theta, positions, tangents, speeds)


def link_error_statistics(positions: np.ndarray) -> LinkErrorStats:
    positions = np.asarray(positions, float)
    if positions.shape != (N_HANDLES, 2):
        raise ValueError("positions must have shape (224, 2)")
    errors = np.abs(np.linalg.norm(np.diff(positions, axis=0), axis=1) - LINK_LENGTHS_M)
    return LinkErrorStats(float(np.max(errors)), float(np.mean(errors)), float(np.percentile(errors, 95)), errors)


def velocity_constraint_residuals(state: ChainState):
    links = state.positions[1:] - state.positions[:-1]
    velocities = state.speeds[:, None] * state.tangents
    return np.einsum("ij,ij->i", links, velocities[1:] - velocities[:-1])


def rectangle_from_handles(start: np.ndarray, end: np.ndarray, *, board_length_m: float, width_m=BOARD_WIDTH_M) -> OrientedRectangle:
    start, end = np.asarray(start, float), np.asarray(end, float)
    axis_long = normalize(end - start)
    axis_wide = np.array([-axis_long[1], axis_long[0]])
    center = 0.5 * (start + end)
    half_length = 0.5 * float(board_length_m)
    half_width = 0.5 * float(width_m)
    vertices = np.array([
        center + half_length * axis_long + half_width * axis_wide,
        center + half_length * axis_long - half_width * axis_wide,
        center - half_length * axis_long - half_width * axis_wide,
        center - half_length * axis_long + half_width * axis_wide,
    ])
    return OrientedRectangle(center, axis_long, axis_wide, half_length, half_width, vertices, vertices.min(axis=0), vertices.max(axis=0))


def rectangle_from_center(center, angle_rad, length_m, width_m) -> OrientedRectangle:
    center = np.asarray(center, float)
    axis_long = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    start = center - 0.5 * (float(length_m) - 2.0 * HOLE_OFFSET_M) * axis_long
    end = center + 0.5 * (float(length_m) - 2.0 * HOLE_OFFSET_M) * axis_long
    return rectangle_from_handles(start, end, board_length_m=length_m, width_m=width_m)


def build_bench_rectangles(positions: np.ndarray) -> list[OrientedRectangle]:
    positions = np.asarray(positions, float)
    if positions.shape != (N_HANDLES, 2):
        raise ValueError("positions must have shape (224, 2)")
    lengths = [HEAD_BOARD_LENGTH_M] + [BODY_BOARD_LENGTH_M] * (N_BENCHES - 1)
    return [rectangle_from_handles(positions[index], positions[index + 1], board_length_m=lengths[index]) for index in range(N_BENCHES)]


def rectangle_signed_clearance(first: OrientedRectangle, second: OrientedRectangle) -> float:
    delta = second.center - first.center
    gaps = []
    for axis in (first.axis_long, first.axis_wide, second.axis_long, second.axis_wide):
        center_distance = abs(float(np.dot(delta, axis)))
        radius_first = first.half_length * abs(float(np.dot(first.axis_long, axis))) + first.half_width * abs(float(np.dot(first.axis_wide, axis)))
        radius_second = second.half_length * abs(float(np.dot(second.axis_long, axis))) + second.half_width * abs(float(np.dot(second.axis_wide, axis)))
        gaps.append(center_distance - radius_first - radius_second)
    return float(max(gaps))


def _candidate_pairs(rectangles: list[OrientedRectangle], near_margin_m: float):
    mins = np.array([rectangle.aabb_min for rectangle in rectangles])
    maxs = np.array([rectangle.aabb_max for rectangle in rectangles])
    overlap = np.all((maxs[:, None, :] + near_margin_m >= mins[None, :, :]) & (maxs[None, :, :] + near_margin_m >= mins[:, None, :]), axis=2)
    mask = np.triu(np.ones((len(rectangles), len(rectangles)), dtype=bool), k=2)
    return np.argwhere(overlap & mask)


def minimum_bench_clearance(positions: np.ndarray, *, near_margin_m=0.6) -> CollisionResult:
    rectangles = build_bench_rectangles(positions)
    candidates = _candidate_pairs(rectangles, near_margin_m)
    if len(candidates) == 0:
        return CollisionResult(float(near_margin_m), None, 0)
    best_clearance = np.inf
    best_pair = None
    for first_index, second_index in candidates:
        clearance = rectangle_signed_clearance(rectangles[int(first_index)], rectangles[int(second_index)])
        if clearance < best_clearance:
            best_clearance = clearance
            best_pair = (int(first_index), int(second_index))
    return CollisionResult(float(best_clearance), best_pair, int(len(candidates)))


def pair_clearance(positions: np.ndarray, pair: tuple[int, int]) -> float:
    rectangles = build_bench_rectangles(positions)
    return rectangle_signed_clearance(rectangles[pair[0]], rectangles[pair[1]])


class TurnaroundPath:
    """Inbound spiral, two tangent circular arcs, and central-symmetric outbound spiral."""

    def __init__(self, pitch_m=1.7, turn_radius_m=TURN_RADIUS_M):
        self.spiral = ArchimedeanSpiral(pitch_m)
        self.turn_radius_m = float(turn_radius_m)
        self.theta_boundary = self.turn_radius_m / self.spiral.a
        self.boundary_arc = self.spiral.arc_primitive(self.theta_boundary)
        self.entry = self.spiral.point(self.theta_boundary)
        self.exit = -self.entry
        self.entry_tangent = self.spiral.inward_tangent(self.theta_boundary)
        self.normal = np.array([-self.entry_tangent[1], self.entry_tangent[0]])
        self.radius2 = np.sqrt(self.turn_radius_m**2 + self.spiral.a**2) / 3.0
        self.radius1 = 2.0 * self.radius2
        self.center1 = self.entry - self.radius1 * self.normal
        self.center2 = self.exit + self.radius2 * self.normal
        centers = self.center2 - self.center1
        self.center_direction = normalize(centers)
        expected = self.radius1 + self.radius2
        if abs(np.linalg.norm(centers) - expected) > 1e-9:
            raise RuntimeError("turning circles are not externally tangent")
        self.join = self.center1 + self.radius1 * self.center_direction
        self.angle1_start = float(np.arctan2(*(self.entry - self.center1)[::-1]))
        self.angle1_end = float(np.arctan2(*(self.join - self.center1)[::-1]))
        self.angle2_start = float(np.arctan2(*(self.join - self.center2)[::-1]))
        self.angle2_end = float(np.arctan2(*(self.exit - self.center2)[::-1]))
        self.sweep1 = (self.angle1_start - self.angle1_end) % (2.0 * np.pi)
        self.sweep2 = (self.angle2_end - self.angle2_start) % (2.0 * np.pi)
        self.length1 = self.radius1 * self.sweep1
        self.length2 = self.radius2 * self.sweep2
        self.turn_length = self.length1 + self.length2

    def point(self, path_s: float) -> np.ndarray:
        path_s = float(path_s)
        if path_s <= 0.0:
            theta = self.spiral.theta_from_arc_fast(self.boundary_arc - path_s)
            return self.spiral.point(theta)
        if path_s <= self.length1:
            angle = self.angle1_start - path_s / self.radius1
            return self.center1 + self.radius1 * np.array([np.cos(angle), np.sin(angle)])
        if path_s <= self.turn_length:
            angle = self.angle2_start + (path_s - self.length1) / self.radius2
            return self.center2 + self.radius2 * np.array([np.cos(angle), np.sin(angle)])
        theta = self.spiral.theta_from_arc_fast(self.boundary_arc + path_s - self.turn_length)
        return self.spiral.outward_symmetric_point(theta)

    def tangent(self, path_s: float) -> np.ndarray:
        path_s = float(path_s)
        if path_s <= 0.0:
            theta = self.spiral.theta_from_arc_fast(self.boundary_arc - path_s)
            return self.spiral.inward_tangent(theta)
        if path_s <= self.length1:
            angle = self.angle1_start - path_s / self.radius1
            return np.array([np.sin(angle), -np.cos(angle)])
        if path_s <= self.turn_length:
            angle = self.angle2_start + (path_s - self.length1) / self.radius2
            return np.array([-np.sin(angle), np.cos(angle)])
        theta = self.spiral.theta_from_arc_fast(self.boundary_arc + path_s - self.turn_length)
        return self.spiral.outward_symmetric_tangent(theta)

    def segment_name(self, path_s: float) -> str:
        if path_s <= 0: return "inbound_spiral"
        if path_s <= self.length1: return "large_arc"
        if path_s <= self.turn_length: return "small_arc"
        return "outbound_spiral"

    def continuity_residuals(self):
        tiny = 1e-7
        junctions = (0.0, self.length1, self.turn_length)
        return {
            "position": [float(np.linalg.norm(self.point(value - tiny) - self.point(value + tiny))) for value in junctions],
            "tangent": [float(np.linalg.norm(self.tangent(value - tiny) - self.tangent(value + tiny))) for value in junctions],
        }

    def max_turn_radius(self, samples=2001):
        values = np.linspace(0.0, self.turn_length, int(samples))
        return float(max(np.linalg.norm(self.point(value)) for value in values))


def _previous_path_coordinate(path: TurnaroundPath, previous_s: float, target_length_m: float):
    def equation(candidate_s):
        return float(np.linalg.norm(path.point(candidate_s) - path.point(previous_s)) - target_length_m)

    distance = target_length_m
    previous_distance = 0.0
    previous_value = -target_length_m
    step = max(0.03, 0.04 * target_length_m)
    while distance <= max(20.0, 8.0 * target_length_m):
        value = equation(previous_s - distance)
        if value >= 0 and previous_value <= 0:
            result = solve_bracketed(equation, (previous_s - distance, previous_s - previous_distance), xtol=2e-12, rtol=1e-12)
            if not result.converged:
                raise RuntimeError(result.message)
            return float(result.root)
        previous_distance, previous_value = distance, value
        distance += step
    raise RuntimeError("failed to bracket nearest previous point on composite path")


def build_path_chain(path: TurnaroundPath, head_s: float, *, head_speed_m_s=1.0) -> ChainState:
    coordinates = np.empty(N_HANDLES, dtype=float)
    positions = np.empty((N_HANDLES, 2), dtype=float)
    tangents = np.empty_like(positions)
    coordinates[0] = float(head_s)
    positions[0] = path.point(head_s)
    tangents[0] = path.tangent(head_s)
    for index, target_length in enumerate(LINK_LENGTHS_M, start=1):
        coordinates[index] = _previous_path_coordinate(path, coordinates[index - 1], float(target_length))
        positions[index] = path.point(coordinates[index])
        tangents[index] = path.tangent(coordinates[index])
    speeds = propagate_speeds(positions, tangents, head_speed_m_s)
    return ChainState(coordinates, positions, tangents, speeds)


def benchmark_call(function, *args, repeats=1, **kwargs):
    times = []
    result = None
    for _ in range(repeats):
        start = perf_counter()
        result = function(*args, **kwargs)
        times.append(perf_counter() - start)
    return result, {"runs": repeats, "min_seconds": float(min(times)), "mean_seconds": float(np.mean(times)), "all_seconds": times}
