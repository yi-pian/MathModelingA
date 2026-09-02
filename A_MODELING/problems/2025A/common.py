"""Problem-specific kinematics, obscuration events and interval arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Callable, Iterable, Literal

import numpy as np
from scipy.optimize import minimize_scalar

from core.geometry import point_to_segment_distance
from core.roots import solve_bracketed
from core.units import rad_to_degree

from problem_data import (
    CLOUD_DESCENT_M_S,
    CLOUD_LIFETIME_S,
    CLOUD_RADIUS_M,
    DECOY_POSITION_M,
    GRAVITY_M_S2,
    MIN_DROP_GAP_S,
    MISSILE_INITIAL_M,
    MISSILE_SPEED_M_S,
    TARGET_BASE_CENTER_M,
    TARGET_CENTER_M,
    TARGET_HEIGHT_M,
    TARGET_RADIUS_M,
    UAV_INITIAL_M,
    UAV_SPEED_BOUNDS_M_S,
)

ModelName = Literal["point", "full"]


@dataclass(frozen=True)
class Precision:
    name: str
    event_step_s: float
    surface_angles: int
    surface_heights: int
    surface_radii: int
    root_xtol_s: float = 1e-9
    event_tol_m2: float = 1e-7


PRECISIONS = {
    "FAST": Precision("FAST", 0.20, 12, 3, 2, 1e-7, 1e-4),
    "STANDARD": Precision("STANDARD", 0.05, 32, 5, 3, 1e-9, 1e-6),
    "FINAL": Precision("FINAL", 0.01, 96, 9, 5, 1e-10, 1e-8),
}


@dataclass(frozen=True)
class Strategy:
    uav: str
    missile: str
    heading_rad: float
    speed_m_s: float
    drop_time_s: float
    delay_s: float
    bomb_no: int = 1

    def __post_init__(self):
        values = np.array([self.heading_rad, self.speed_m_s, self.drop_time_s, self.delay_s], dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError("strategy values must be finite")
        if self.uav not in UAV_INITIAL_M or self.missile not in MISSILE_INITIAL_M:
            raise ValueError("unknown UAV or missile")
        if not UAV_SPEED_BOUNDS_M_S[0] <= self.speed_m_s <= UAV_SPEED_BOUNDS_M_S[1]:
            raise ValueError("UAV speed outside [70, 140] m/s")
        if self.drop_time_s < 0 or self.delay_s < 0:
            raise ValueError("drop time and delay must be nonnegative")
        if self.bomb_no < 1:
            raise ValueError("bomb number must be positive")

    @property
    def burst_time_s(self) -> float:
        return self.drop_time_s + self.delay_s

    @property
    def heading_deg(self) -> float:
        return float(rad_to_degree(self.heading_rad) % 360.0)


@dataclass(frozen=True)
class ObscurationResult:
    strategy: Strategy
    model: ModelName
    precision: str
    intervals_s: tuple[tuple[float, float], ...]
    duration_s: float
    root_residual_max_m2: float
    burst_point_m: np.ndarray
    feasible: bool
    reason: str = ""


def heading_vector(heading_rad: float) -> np.ndarray:
    if not np.isfinite(heading_rad):
        raise ValueError("heading must be finite")
    return np.array([np.cos(heading_rad), np.sin(heading_rad), 0.0])


def missile_arrival_time(missile: str) -> float:
    return float(np.linalg.norm(MISSILE_INITIAL_M[missile] - DECOY_POSITION_M) / MISSILE_SPEED_M_S)


def missile_position(missile: str, time_s: float | np.ndarray) -> np.ndarray:
    initial = MISSILE_INITIAL_M[missile]
    direction = (DECOY_POSITION_M - initial) / np.linalg.norm(DECOY_POSITION_M - initial)
    time = np.asarray(time_s, dtype=float)
    if not np.all(np.isfinite(time)):
        raise ValueError("time must be finite")
    return initial + np.expand_dims(time, axis=-1) * MISSILE_SPEED_M_S * direction


def uav_position(uav: str, heading_rad: float, speed_m_s: float, time_s: float | np.ndarray) -> np.ndarray:
    time = np.asarray(time_s, dtype=float)
    return UAV_INITIAL_M[uav] + np.expand_dims(time, axis=-1) * speed_m_s * heading_vector(heading_rad)


def drop_point(strategy: Strategy) -> np.ndarray:
    return np.asarray(uav_position(strategy.uav, strategy.heading_rad, strategy.speed_m_s, strategy.drop_time_s), dtype=float)


def burst_point(strategy: Strategy, *, gravity_m_s2: float = GRAVITY_M_S2) -> np.ndarray:
    point = np.asarray(uav_position(strategy.uav, strategy.heading_rad, strategy.speed_m_s, strategy.burst_time_s), dtype=float)
    point[2] -= 0.5 * gravity_m_s2 * strategy.delay_s**2
    return point


def bomb_position(strategy: Strategy, time_s: float, *, gravity_m_s2: float = GRAVITY_M_S2) -> np.ndarray:
    if time_s < strategy.drop_time_s or time_s > strategy.burst_time_s:
        raise ValueError("bomb position is only defined from release through burst")
    elapsed = time_s - strategy.drop_time_s
    point = drop_point(strategy) + strategy.speed_m_s * elapsed * heading_vector(strategy.heading_rad)
    point[2] -= 0.5 * gravity_m_s2 * elapsed**2
    return point


def cloud_center(strategy: Strategy, time_s: float, *, gravity_m_s2: float = GRAVITY_M_S2) -> np.ndarray:
    if time_s < strategy.burst_time_s or time_s > strategy.burst_time_s + CLOUD_LIFETIME_S:
        raise ValueError("cloud center requested outside the nominal active interval")
    center = burst_point(strategy, gravity_m_s2=gravity_m_s2)
    center[2] -= CLOUD_DESCENT_M_S * (time_s - strategy.burst_time_s)
    return center


def target_surface_points(precision: str | Precision = "STANDARD") -> np.ndarray:
    cfg = PRECISIONS[precision] if isinstance(precision, str) else precision
    angles = np.linspace(0.0, 2.0 * np.pi, cfg.surface_angles, endpoint=False)
    cosine, sine = np.cos(angles), np.sin(angles)
    heights = np.linspace(0.0, TARGET_HEIGHT_M, cfg.surface_heights)
    side = np.array(
        [[TARGET_RADIUS_M * c, TARGET_BASE_CENTER_M[1] + TARGET_RADIUS_M * s, z] for z in heights for c, s in zip(cosine, sine)],
        dtype=float,
    )
    radii = np.linspace(0.0, TARGET_RADIUS_M, cfg.surface_radii)
    caps = np.array(
        [[r * c, TARGET_BASE_CENTER_M[1] + r * s, z] for z in (0.0, TARGET_HEIGHT_M) for r in radii for c, s in zip(cosine, sine)],
        dtype=float,
    )
    points = np.unique(np.vstack((side, caps)), axis=0)
    return points


def point_segment_distance_sq_many(points: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    points = np.atleast_2d(np.asarray(points, dtype=float))
    start = np.broadcast_to(np.asarray(start, dtype=float), points.shape)
    end = np.broadcast_to(np.asarray(end, dtype=float), points.shape)
    segment = end - start
    denom = np.sum(segment**2, axis=1)
    numerator = np.sum((points - start) * segment, axis=1)
    parameter = np.divide(numerator, denom, out=np.zeros_like(numerator), where=denom > 1e-20)
    parameter = np.clip(parameter, 0.0, 1.0)
    projection = start + parameter[:, None] * segment
    return np.sum((points - projection) ** 2, axis=1)


def event_value_m2(
    strategy: Strategy,
    time_s: float,
    *,
    model: ModelName = "full",
    surface_points: np.ndarray | None = None,
    gravity_m_s2: float = GRAVITY_M_S2,
) -> float:
    observer = np.asarray(missile_position(strategy.missile, time_s), dtype=float)
    center = cloud_center(strategy, time_s, gravity_m_s2=gravity_m_s2)
    if model == "point":
        distance_m = point_to_segment_distance(center, observer, TARGET_CENTER_M)
        return float(distance_m**2 - CLOUD_RADIUS_M**2)
    if model != "full":
        raise ValueError("model must be 'point' or 'full'")
    points = target_surface_points("STANDARD") if surface_points is None else np.asarray(surface_points, dtype=float)
    distance_sq_m2 = point_segment_distance_sq_many(np.repeat(center[None, :], len(points), axis=0), observer, points)
    return float(np.max(distance_sq_m2) - CLOUD_RADIUS_M**2)


def feasible_active_window(
    strategy: Strategy,
    *,
    gravity_m_s2: float = GRAVITY_M_S2,
    truncate_at_ground: bool = True,
) -> tuple[float, float] | None:
    burst = burst_point(strategy, gravity_m_s2=gravity_m_s2)
    if burst[2] < 0:
        return None
    start = strategy.burst_time_s
    stop = min(start + CLOUD_LIFETIME_S, missile_arrival_time(strategy.missile))
    if truncate_at_ground:
        stop = min(stop, start + burst[2] / CLOUD_DESCENT_M_S)
    return (start, stop) if stop > start else None


def merge_intervals(intervals: Iterable[tuple[float, float]], *, tolerance_s: float = 1e-9) -> list[tuple[float, float]]:
    ordered = sorted((float(a), float(b)) for a, b in intervals if b >= a)
    merged: list[list[float]] = []
    for start, stop in ordered:
        if not merged or start > merged[-1][1] + tolerance_s:
            merged.append([start, stop])
        else:
            merged[-1][1] = max(merged[-1][1], stop)
    return [(a, b) for a, b in merged]


def interval_duration(intervals: Iterable[tuple[float, float]]) -> float:
    return float(sum(max(0.0, b - a) for a, b in merge_intervals(intervals)))


def marginal_interval_gains(interval_groups: Iterable[Iterable[tuple[float, float]]]) -> list[float]:
    current: list[tuple[float, float]] = []
    gains = []
    for group in interval_groups:
        before = interval_duration(current)
        current = merge_intervals([*current, *group])
        gains.append(interval_duration(current) - before)
    return gains


def locate_nonpositive_intervals(
    function: Callable[[float], float],
    start: float,
    stop: float,
    *,
    step: float,
    xtol: float = 1e-9,
    value_tol: float = 1e-8,
) -> tuple[list[tuple[float, float]], list[float]]:
    """Locate all f(t)<=0 intervals with sign-change roots and tangent checks."""
    if not (np.isfinite(start) and np.isfinite(stop) and np.isfinite(step)) or stop <= start or step <= 0:
        raise ValueError("require finite start < stop and positive step")
    count = max(2, int(ceil((stop - start) / step)) + 1)
    time = np.linspace(start, stop, count)
    values = np.array([float(function(t)) for t in time])
    if not np.all(np.isfinite(values)):
        raise ValueError("event function returned non-finite values")
    roots: list[float] = []

    def add_root(value: float):
        if start - xtol <= value <= stop + xtol and all(abs(value - old) > 20 * xtol for old in roots):
            roots.append(float(np.clip(value, start, stop)))

    for index in range(count - 1):
        a, b = time[index], time[index + 1]
        fa, fb = values[index], values[index + 1]
        if abs(fa) <= value_tol:
            add_root(a)
        if np.signbit(fa) != np.signbit(fb):
            result = solve_bracketed(function, (a, b), xtol=xtol, rtol=max(4 * np.finfo(float).eps, xtol))
            add_root(float(result.root))
    if abs(values[-1]) <= value_tol:
        add_root(stop)

    # Even-multiplicity contact or a narrow negative pocket may not change sign at coarse nodes.
    for index in range(1, count - 1):
        if values[index] <= values[index - 1] and values[index] <= values[index + 1]:
            refined = minimize_scalar(function, bounds=(time[index - 1], time[index + 1]), method="bounded", options={"xatol": xtol})
            if not refined.success or not np.isfinite(refined.fun):
                continue
            t_min, f_min = float(refined.x), float(refined.fun)
            if abs(f_min) <= value_tol:
                add_root(t_min)
            if f_min < -value_tol:
                if function(time[index - 1]) > 0:
                    add_root(float(solve_bracketed(function, (time[index - 1], t_min), xtol=xtol).root))
                if function(time[index + 1]) > 0:
                    add_root(float(solve_bracketed(function, (t_min, time[index + 1]), xtol=xtol).root))

    roots.sort()
    boundaries = [start, *roots, stop]
    intervals = []
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        if right - left <= 10 * xtol:
            continue
        middle = 0.5 * (left + right)
        if function(middle) <= value_tol:
            intervals.append((left, right))
    if function(start) <= value_tol and (not intervals or intervals[0][0] > start + xtol):
        right = roots[0] if roots else stop
        if right > start:
            intervals.insert(0, (start, right))
    return merge_intervals(intervals, tolerance_s=20 * xtol), roots


def obscuration_intervals(
    strategy: Strategy,
    *,
    model: ModelName = "full",
    precision: str | Precision = "STANDARD",
    gravity_m_s2: float = GRAVITY_M_S2,
    truncate_at_ground: bool = True,
) -> ObscurationResult:
    cfg = PRECISIONS[precision] if isinstance(precision, str) else precision
    burst = burst_point(strategy, gravity_m_s2=gravity_m_s2)
    window = feasible_active_window(strategy, gravity_m_s2=gravity_m_s2, truncate_at_ground=truncate_at_ground)
    if window is None:
        return ObscurationResult(strategy, model, cfg.name, (), 0.0, 0.0, burst, False, "burst below ground or empty active window")
    points = target_surface_points(cfg) if model == "full" else None
    event = lambda time_s: event_value_m2(
        strategy,
        time_s,
        model=model,
        surface_points=points,
        gravity_m_s2=gravity_m_s2,
    )
    intervals, roots = locate_nonpositive_intervals(
        event,
        *window,
        step=cfg.event_step_s,
        xtol=cfg.root_xtol_s,
        value_tol=cfg.event_tol_m2,
    )
    residual = max((abs(event(root)) for root in roots), default=0.0)
    return ObscurationResult(
        strategy,
        model,
        cfg.name,
        tuple(intervals),
        interval_duration(intervals),
        float(residual),
        burst,
        True,
    )


def validate_drop_gaps(strategies: Iterable[Strategy], *, tolerance_s: float = 1e-9) -> bool:
    by_uav: dict[str, list[float]] = {}
    for strategy in strategies:
        by_uav.setdefault(strategy.uav, []).append(strategy.drop_time_s)
    return all(np.all(np.diff(sorted(times)) >= MIN_DROP_GAP_S - tolerance_s) for times in by_uav.values())
