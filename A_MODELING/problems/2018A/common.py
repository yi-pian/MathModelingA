"""Problem-specific multilayer transient heat-transfer model for CUMCM 2018 A."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, diags, eye
from scipy.sparse.linalg import splu

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.units import mm_to_m

BODY_TEMPERATURE_C = 37.0
OFFICIAL_BOOK = (
    ROOT
    / "data"
    / "2018A"
    / "official"
    / "extracted"
    / "2018-A-Chinese"
    / "CUMCM-2018-Problem-A-Chinese-Appendix.xlsx"
)


@dataclass(frozen=True)
class Layer:
    name: str
    density_kg_m3: float
    heat_capacity_j_kgk: float
    conductivity_w_mk: float
    thickness_m: float


@dataclass(frozen=True)
class Grid:
    centers_m: np.ndarray
    widths_m: np.ndarray
    density_kg_m3: np.ndarray
    heat_capacity_j_kgk: np.ndarray
    conductivity_w_mk: np.ndarray
    layer_index: np.ndarray
    layer_names: tuple[str, ...]
    layer_boundaries_m: np.ndarray


@dataclass(frozen=True)
class HeatSystem:
    grid: Grid
    operator: csr_matrix
    source_c_per_s: np.ndarray
    capacity_j_m2k: np.ndarray
    internal_conductance_w_m2k: np.ndarray
    outer_conductance_w_m2k: float
    skin_conductance_w_m2k: float
    environment_temperature_c: float
    body_temperature_c: float
    h_out_w_m2k: float
    h_skin_w_m2k: float


@dataclass(frozen=True)
class SimulationResult:
    time_s: np.ndarray
    temperature_c: np.ndarray
    skin_temperature_c: np.ndarray
    outer_surface_temperature_c: np.ndarray
    dt_s: float
    method: str


def official_layers(d_ii_m: float = 0.006, d_iv_m: float = 0.005) -> tuple[Layer, ...]:
    """Return the four official layers; thickness inputs are already SI."""
    if not (mm_to_m(0.6) <= d_ii_m <= mm_to_m(25.0)):
        raise ValueError("layer II thickness is outside the official range")
    if not (mm_to_m(0.6) <= d_iv_m <= mm_to_m(6.4)):
        raise ValueError("layer IV thickness is outside the official range")
    return (
        Layer("I", 300.0, 1377.0, 0.082, mm_to_m(0.6)),
        Layer("II", 862.0, 2100.0, 0.37, float(d_ii_m)),
        Layer("III", 74.2, 1726.0, 0.045, mm_to_m(3.6)),
        Layer("IV", 1.18, 1005.0, 0.028, float(d_iv_m)),
    )


def load_official_data(path: Path = OFFICIAL_BOOK) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read, but never modify, the official material and measurement sheets."""
    materials = pd.read_excel(path, sheet_name="附件1", header=1)
    measurements = pd.read_excel(path, sheet_name="附件2", header=1)
    if measurements.shape != (5401, 2):
        raise ValueError(f"unexpected measurement shape: {measurements.shape}")
    if measurements.isna().any().any() or not np.isfinite(measurements.to_numpy(float)).all():
        raise ValueError("official measurement sheet contains NaN or Inf")
    times = measurements.iloc[:, 0].to_numpy(float)
    if not np.array_equal(times, np.arange(5401, dtype=float)):
        raise ValueError("official measurement time must be exactly 0..5400 s")
    return materials, measurements


def build_grid(layers: tuple[Layer, ...], target_dx_m: float = 1.0e-4) -> Grid:
    """Build a cell-centred grid that hits every material interface exactly."""
    if target_dx_m <= 0 or not np.isfinite(target_dx_m):
        raise ValueError("target_dx_m must be finite and positive")
    centers: list[np.ndarray] = []
    widths: list[np.ndarray] = []
    densities: list[np.ndarray] = []
    heat_capacities: list[np.ndarray] = []
    conductivities: list[np.ndarray] = []
    layer_ids: list[np.ndarray] = []
    boundaries = [0.0]
    offset = 0.0
    for index, layer in enumerate(layers):
        if min(layer.density_kg_m3, layer.heat_capacity_j_kgk, layer.conductivity_w_mk, layer.thickness_m) <= 0:
            raise ValueError("all material properties and thicknesses must be positive")
        count = max(1, int(round(layer.thickness_m / target_dx_m)))
        dx = layer.thickness_m / count
        local_centers = offset + (np.arange(count) + 0.5) * dx
        centers.append(local_centers)
        widths.append(np.full(count, dx))
        densities.append(np.full(count, layer.density_kg_m3))
        heat_capacities.append(np.full(count, layer.heat_capacity_j_kgk))
        conductivities.append(np.full(count, layer.conductivity_w_mk))
        layer_ids.append(np.full(count, index, dtype=int))
        offset += layer.thickness_m
        boundaries.append(offset)
    return Grid(
        centers_m=np.concatenate(centers),
        widths_m=np.concatenate(widths),
        density_kg_m3=np.concatenate(densities),
        heat_capacity_j_kgk=np.concatenate(heat_capacities),
        conductivity_w_mk=np.concatenate(conductivities),
        layer_index=np.concatenate(layer_ids),
        layer_names=tuple(layer.name for layer in layers),
        layer_boundaries_m=np.asarray(boundaries),
    )


def assemble_heat_system(
    grid: Grid,
    environment_temperature_c: float,
    h_out_w_m2k: float,
    h_skin_w_m2k: float,
    body_temperature_c: float = BODY_TEMPERATURE_C,
) -> HeatSystem:
    """Assemble C dT/dt = conductance fluxes on a unit garment area."""
    if min(h_out_w_m2k, h_skin_w_m2k) <= 0:
        raise ValueError("heat-transfer coefficients must be positive")
    dx, k = grid.widths_m, grid.conductivity_w_mk
    capacity = grid.density_kg_m3 * grid.heat_capacity_j_kgk * dx
    internal_g = 1.0 / (0.5 * dx[:-1] / k[:-1] + 0.5 * dx[1:] / k[1:])
    outer_g = 1.0 / (1.0 / h_out_w_m2k + 0.5 * dx[0] / k[0])
    skin_g = 1.0 / (1.0 / h_skin_w_m2k + 0.5 * dx[-1] / k[-1])

    lower = internal_g / capacity[1:]
    upper = internal_g / capacity[:-1]
    diagonal = np.empty_like(capacity)
    diagonal[0] = -(outer_g + internal_g[0]) / capacity[0]
    diagonal[-1] = -(internal_g[-1] + skin_g) / capacity[-1]
    if len(capacity) > 2:
        diagonal[1:-1] = -(internal_g[:-1] + internal_g[1:]) / capacity[1:-1]
    operator = diags((lower, diagonal, upper), offsets=(-1, 0, 1), format="csr")
    source = np.zeros_like(capacity)
    source[0] = outer_g * environment_temperature_c / capacity[0]
    source[-1] = skin_g * body_temperature_c / capacity[-1]
    return HeatSystem(
        grid=grid,
        operator=operator,
        source_c_per_s=source,
        capacity_j_m2k=capacity,
        internal_conductance_w_m2k=internal_g,
        outer_conductance_w_m2k=float(outer_g),
        skin_conductance_w_m2k=float(skin_g),
        environment_temperature_c=float(environment_temperature_c),
        body_temperature_c=float(body_temperature_c),
        h_out_w_m2k=float(h_out_w_m2k),
        h_skin_w_m2k=float(h_skin_w_m2k),
    )


def _surface_temperatures(system: HeatSystem, temperature_c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.atleast_2d(np.asarray(temperature_c, float))
    q_outer = system.outer_conductance_w_m2k * (system.environment_temperature_c - values[:, 0])
    outer_surface = system.environment_temperature_c - q_outer / system.h_out_w_m2k
    q_skin = system.skin_conductance_w_m2k * (values[:, -1] - system.body_temperature_c)
    skin_surface = system.body_temperature_c + q_skin / system.h_skin_w_m2k
    return outer_surface, skin_surface


def simulate(
    system: HeatSystem,
    final_time_s: float,
    dt_s: float = 1.0,
    initial_temperature_c: float | np.ndarray = BODY_TEMPERATURE_C,
    method: str = "cn",
    store_every: int = 1,
) -> SimulationResult:
    """Advance the constant-coefficient semi-discrete system by CN or backward Euler."""
    if final_time_s <= 0 or dt_s <= 0 or store_every < 1:
        raise ValueError("final_time_s, dt_s and store_every must be positive")
    steps = int(np.ceil(final_time_s / dt_s))
    dt = final_time_s / steps
    theta = {"cn": 0.5, "backward_euler": 1.0}.get(method)
    if theta is None:
        raise ValueError("method must be 'cn' or 'backward_euler'")
    node_count = len(system.capacity_j_m2k)
    temperature = np.broadcast_to(np.asarray(initial_temperature_c, float), (node_count,)).copy()
    identity = eye(node_count, format="csr")
    left = identity - theta * dt * system.operator
    right = identity + (1.0 - theta) * dt * system.operator
    solve_left = splu(left.tocsc()).solve

    stored_steps = list(range(0, steps + 1, store_every))
    if stored_steps[-1] != steps:
        stored_steps.append(steps)
    field = np.empty((len(stored_steps), node_count))
    times = np.empty(len(stored_steps))
    field[0] = temperature
    times[0] = 0.0
    write_index = 1
    for step in range(1, steps + 1):
        temperature = solve_left(right @ temperature + dt * system.source_c_per_s)
        if step == stored_steps[write_index]:
            field[write_index] = temperature
            times[write_index] = step * dt
            write_index += 1
    outer, skin = _surface_temperatures(system, field)
    return SimulationResult(times, field, skin, outer, dt, method)


def explicit_stable_dt(system: HeatSystem, safety: float = 1.0) -> float:
    """Monotonic Forward-Euler limit C_i/sum(G_i), including Robin faces."""
    if not (0 < safety <= 1):
        raise ValueError("safety must be in (0,1]")
    diagonal_rates = -system.operator.diagonal()
    return float(safety / np.max(diagonal_rates))


def simulate_explicit(
    system: HeatSystem,
    final_time_s: float,
    dt_s: float,
    initial_temperature_c: float | np.ndarray = BODY_TEMPERATURE_C,
    store_every: int = 1,
) -> SimulationResult:
    """Forward Euler used only for controlled cross-validation."""
    limit = explicit_stable_dt(system)
    if dt_s > limit * (1.0 + 1e-12):
        raise ValueError(f"explicit dt={dt_s:g} exceeds stable limit {limit:g}")
    steps = int(np.ceil(final_time_s / dt_s))
    dt = final_time_s / steps
    node_count = len(system.capacity_j_m2k)
    temperature = np.broadcast_to(np.asarray(initial_temperature_c, float), (node_count,)).copy()
    stored_steps = list(range(0, steps + 1, store_every))
    if stored_steps[-1] != steps:
        stored_steps.append(steps)
    field = np.empty((len(stored_steps), node_count))
    times = np.empty(len(stored_steps))
    field[0], times[0] = temperature, 0.0
    write_index = 1
    for step in range(1, steps + 1):
        temperature = temperature + dt * (system.operator @ temperature + system.source_c_per_s)
        if step == stored_steps[write_index]:
            field[write_index] = temperature
            times[write_index] = step * dt
            write_index += 1
    outer, skin = _surface_temperatures(system, field)
    return SimulationResult(times, field, skin, outer, dt, "explicit")


def interface_diagnostics(system: HeatSystem, temperature_c: np.ndarray) -> pd.DataFrame:
    """Reconstruct both sides of each material interface and report continuity residuals."""
    temperature = np.asarray(temperature_c, float)
    if temperature.shape != system.capacity_j_m2k.shape:
        raise ValueError("temperature must be one complete grid snapshot")
    grid = system.grid
    faces = np.flatnonzero(grid.layer_index[:-1] != grid.layer_index[1:])
    rows = []
    for face in faces:
        left_resistance = 0.5 * grid.widths_m[face] / grid.conductivity_w_mk[face]
        right_resistance = 0.5 * grid.widths_m[face + 1] / grid.conductivity_w_mk[face + 1]
        heat_flux = (temperature[face] - temperature[face + 1]) / (left_resistance + right_resistance)
        left_interface = temperature[face] - heat_flux * left_resistance
        right_interface = temperature[face + 1] + heat_flux * right_resistance
        rows.append(
            {
                "interface": f"{grid.layer_names[grid.layer_index[face]]}-{grid.layer_names[grid.layer_index[face + 1]]}",
                "x_m": grid.layer_boundaries_m[grid.layer_index[face] + 1],
                "temperature_left_c": left_interface,
                "temperature_right_c": right_interface,
                "temperature_residual_c": left_interface - right_interface,
                "heat_flux_left_w_m2": heat_flux,
                "heat_flux_right_w_m2": heat_flux,
                "heat_flux_residual_w_m2": 0.0,
            }
        )
    return pd.DataFrame(rows)


def energy_balance_residual(system: HeatSystem, result: SimulationResult) -> np.ndarray:
    """CN trapezoidal energy residual per time interval, in W/m²."""
    if result.method != "cn" or len(result.time_s) < 2:
        raise ValueError("energy residual currently requires consecutive CN output")
    dt = np.diff(result.time_s)
    if not np.allclose(dt, result.dt_s):
        raise ValueError("energy residual requires store_every=1")
    stored_energy_rate = ((result.temperature_c[1:] - result.temperature_c[:-1]) @ system.capacity_j_m2k) / result.dt_s
    q_in = system.h_out_w_m2k * (system.environment_temperature_c - result.outer_surface_temperature_c)
    q_out = system.h_skin_w_m2k * (result.skin_temperature_c - system.body_temperature_c)
    boundary_rate = 0.5 * ((q_in[1:] - q_out[1:]) + (q_in[:-1] - q_out[:-1]))
    return stored_energy_rate - boundary_rate


def first_crossing_time(time_s: np.ndarray, values: np.ndarray, threshold: float) -> float | None:
    """First upward crossing under piecewise-linear interpolation."""
    time_s, values = np.asarray(time_s, float), np.asarray(values, float)
    if time_s.shape != values.shape or len(time_s) == 0 or np.any(np.diff(time_s) <= 0):
        raise ValueError("time and values must be same-length with strictly increasing time")
    if values[0] > threshold:
        return float(time_s[0])
    indices = np.flatnonzero((values[:-1] <= threshold) & (values[1:] > threshold))
    if not len(indices):
        return None
    i = int(indices[0])
    fraction = (threshold - values[i]) / (values[i + 1] - values[i])
    return float(time_s[i] + fraction * (time_s[i + 1] - time_s[i]))


def duration_above_threshold(time_s: np.ndarray, values: np.ndarray, threshold: float) -> float:
    """Integrate time above a threshold using linear interpolation on every segment."""
    time_s, values = np.asarray(time_s, float), np.asarray(values, float)
    if time_s.shape != values.shape or len(time_s) < 2 or np.any(np.diff(time_s) <= 0):
        raise ValueError("time and values must be same-length with strictly increasing time")
    duration = 0.0
    for t0, t1, y0, y1 in zip(time_s[:-1], time_s[1:], values[:-1], values[1:]):
        interval = t1 - t0
        if y0 > threshold and y1 > threshold:
            duration += interval
        elif (y0 > threshold) != (y1 > threshold):
            fraction = (threshold - y0) / (y1 - y0)
            duration += interval * (fraction if y0 > threshold else 1.0 - fraction)
    return float(duration)


def safety_metrics(result: SimulationResult) -> dict[str, float | None | bool]:
    duration = duration_above_threshold(result.time_s, result.skin_temperature_c, 44.0)
    maximum = float(np.max(result.skin_temperature_c))
    crossing = first_crossing_time(result.time_s, result.skin_temperature_c, 44.0)
    return {
        "max_skin_temperature_c": maximum,
        "duration_above_44_s": duration,
        "first_crossing_44_s": crossing,
        "margin_47_c": 47.0 - maximum,
        "margin_duration_s": 300.0 - duration,
        "feasible": bool(maximum <= 47.0 + 1e-9 and duration <= 300.0 + 1e-9),
    }


def single_layer_sine_benchmark(
    alpha_m2_s: float = 1.0e-5,
    length_m: float = 0.01,
    final_time_s: float = 1.0,
    nx: int = 101,
    dt_s: float = 0.01,
    method: str = "cn",
) -> dict[str, np.ndarray | float]:
    """Dirichlet sine-mode benchmark independent of the garment Robin boundaries."""
    if nx < 3 or min(alpha_m2_s, length_m, final_time_s, dt_s) <= 0:
        raise ValueError("invalid benchmark parameters")
    x = np.linspace(0.0, length_m, nx)
    dx = x[1] - x[0]
    steps = int(np.ceil(final_time_s / dt_s))
    dt = final_time_s / steps
    r = alpha_m2_s * dt / dx**2
    interior = nx - 2
    lap = diags((np.ones(interior - 1), -2.0 * np.ones(interior), np.ones(interior - 1)), (-1, 0, 1), format="csr")
    temperature = np.sin(np.pi * x[1:-1] / length_m)
    if method == "explicit":
        if r > 0.5 + 1e-14:
            raise ValueError("explicit sine benchmark violates r <= 0.5")
        for _ in range(steps):
            temperature = temperature + r * (lap @ temperature)
    elif method == "cn":
        identity = eye(interior, format="csr")
        solve_left = splu((identity - 0.5 * r * lap).tocsc()).solve
        right = identity + 0.5 * r * lap
        for _ in range(steps):
            temperature = solve_left(right @ temperature)
    else:
        raise ValueError("method must be cn or explicit")
    numerical = np.zeros(nx)
    numerical[1:-1] = temperature
    exact = np.sin(np.pi * x / length_m) * np.exp(-alpha_m2_s * (np.pi / length_m) ** 2 * final_time_s)
    return {
        "x_m": x,
        "numerical": numerical,
        "exact": exact,
        "max_error": float(np.max(np.abs(numerical - exact))),
        "dx_m": float(dx),
        "dt_s": float(dt),
        "r": float(r),
    }


def make_system(
    environment_temperature_c: float,
    h_out_w_m2k: float,
    h_skin_w_m2k: float,
    d_ii_m: float = 0.006,
    d_iv_m: float = 0.005,
    target_dx_m: float = 1.0e-4,
) -> HeatSystem:
    return assemble_heat_system(
        build_grid(official_layers(d_ii_m, d_iv_m), target_dx_m),
        environment_temperature_c,
        h_out_w_m2k,
        h_skin_w_m2k,
    )
