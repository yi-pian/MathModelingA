"""Q4: continuous motion through the two-arc S-turn and official result4.xlsx."""

from __future__ import annotations

from pathlib import Path
import json
import sys
from time import perf_counter

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "core").is_dir())
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))

from core.export import export_origin_table, write_excel_checked
from core.plotting import COLORS, save_figure, use_paper_style
from core.validation import ValidationReport, check_finite, check_monotonic_time

from common import (
    NODE_LABELS, N_HANDLES, SELECTED_NODE_INDICES, TURN_RADIUS_M,
    TurnaroundPath, build_path_chain, link_error_statistics,
    minimum_bench_clearance, velocity_constraint_residuals,
)
from deliverables import OFFICIAL_DIR, RESULT_DIR, fill_time_series_template, selected_position_table, selected_speed_table


def solve_q4(path):
    times = np.arange(-100.0, 101.0, 1.0)
    positions = np.empty((len(times), N_HANDLES, 2))
    speeds = np.empty((len(times), N_HANDLES))
    coordinates = np.empty((len(times), N_HANDLES))
    link_errors = np.empty((len(times), N_HANDLES - 1))
    velocity_residual_max = np.empty(len(times))
    build_times = np.empty(len(times))
    start_total = perf_counter()
    for time_index, time_s in enumerate(times):
        start = perf_counter(); state = build_path_chain(path, time_s)
        build_times[time_index] = perf_counter() - start
        positions[time_index] = state.positions; speeds[time_index] = state.speeds
        coordinates[time_index] = state.coordinates
        link_errors[time_index] = link_error_statistics(state.positions).errors
        velocity_residual_max[time_index] = np.max(np.abs(velocity_constraint_residuals(state)))
    return {
        "times": times, "positions": positions, "speeds": speeds,
        "coordinates": coordinates, "link_errors": link_errors,
        "velocity_residual_max": velocity_residual_max,
        "build_times": build_times, "total_seconds": perf_counter() - start_total,
    }


def finite_difference_speed_check(path, check_times, step_s=1e-3):
    errors = []
    for time_s in check_times:
        minus = build_path_chain(path, time_s - step_s)
        center = build_path_chain(path, time_s)
        plus = build_path_chain(path, time_s + step_s)
        numerical = np.linalg.norm((plus.positions - minus.positions) / (2.0 * step_s), axis=1)
        errors.extend(np.abs(numerical - center.speeds).tolist())
    return {"step_s": step_s, "max_abs": float(max(errors)), "mean_abs": float(np.mean(errors))}


def junction_speed_convergence(path):
    """At C1-but-not-C2 joins, centered differences converge only first order."""
    steps = (1e-3, 5e-4, 2.5e-4)
    errors = []
    junctions = (0.0, path.length1, path.turn_length)
    for step_s in steps:
        check = finite_difference_speed_check(path, junctions, step_s=step_s)
        errors.append(check["max_abs"])
    return {
        "steps_s": list(steps), "max_errors_m_s": errors,
        "successive_ratios": [errors[index] / errors[index + 1] for index in range(len(errors) - 1)],
    }


def plot_path_shapes(path, positions, selected_times, output):
    import matplotlib.pyplot as plt
    if len(selected_times) != 2:
        raise ValueError("paper figure is limited to two subplots")
    use_paper_style(); figure, axes = plt.subplots(1, 2, figsize=(9.6, 4.4))
    path_s = np.linspace(-105.0, 105.0, 3000)
    curve = np.array([path.point(value) for value in path_s])
    for axis, time_s in zip(axes, selected_times):
        state_positions = positions[time_s + 100]
        axis.plot(curve[:, 0], curve[:, 1], color="#C7C7C7", linewidth=0.7, label="Prescribed path")
        circle = plt.Circle((0, 0), TURN_RADIUS_M, fill=False, color="#999999", linestyle="--", linewidth=0.8, label="Turn boundary")
        axis.add_patch(circle)
        axis.plot(state_positions[:, 0], state_positions[:, 1], color=COLORS[0], linewidth=1.0, label="Dragon handles")
        axis.scatter(state_positions[0, 0], state_positions[0, 1], color=COLORS[1], s=22, zorder=3, label="Head")
        axis.set(xlabel="x (m)", ylabel="y (m)", title=f"t = {time_s} s")
        axis.set_aspect("equal", adjustable="box"); axis.grid(True, color="#DDDDDD", linewidth=0.45)
    axes[0].legend(loc="best", fontsize=7); figure.tight_layout()
    save_figure(figure, output); plt.close(figure)


def plot_speeds(times, speeds, output):
    import matplotlib.pyplot as plt
    use_paper_style(); figure, axes = plt.subplots(1, 2, figsize=(10.0, 3.7))
    for color_index, node in enumerate(SELECTED_NODE_INDICES):
        axes[0].plot(times, speeds[:, node], color=COLORS[color_index % len(COLORS)], label=NODE_LABELS[node])
    axes[0].set(xlabel="Time (s)", ylabel="Speed (m/s)"); axes[0].grid(True, color="#DDDDDD", linewidth=0.45)
    axes[0].legend(ncol=2, fontsize=6.5)
    nodes = np.arange(N_HANDLES)
    for color_index, time_s in enumerate((-100, -50, 0, 50, 100)):
        axes[1].plot(nodes, speeds[time_s + 100], color=COLORS[color_index % len(COLORS)], label=f"t={time_s} s")
    axes[1].set(xlabel="Handle index", ylabel="Speed (m/s)"); axes[1].grid(True, color="#DDDDDD", linewidth=0.45); axes[1].legend(fontsize=7)
    figure.tight_layout(); save_figure(figure, output); plt.close(figure)


def main():
    output = RESULT_DIR; figures = output / "figures"; origin = output / "origin_data"; raw = output / "raw"
    for directory in (figures, origin, raw): directory.mkdir(parents=True, exist_ok=True)
    path = TurnaroundPath(); result = solve_q4(path)
    times, positions, speeds = result["times"], result["positions"], result["speeds"]
    fd = finite_difference_speed_check(path, [-100, -50, 2, 5, 7, 11, 20, 50, 100])
    junction_fd = junction_speed_convergence(path)
    continuity = path.continuity_residuals(); max_turn_radius = path.max_turn_radius(samples=4001)

    excel = fill_time_series_template(OFFICIAL_DIR / "result4.xlsx", output / "result4.xlsx", times, positions, speeds)
    selected_times = np.array([-100, -50, 0, 50, 100], dtype=float)
    selected_indices = (selected_times + 100).astype(int)
    selected_positions = selected_position_table(selected_times, positions[selected_indices])
    selected_speeds = selected_speed_table(selected_times, speeds[selected_indices])
    write_excel_checked(output / "q4_selected_results.xlsx", {"Position": selected_positions, "Speed": selected_speeds}, decimals=6)

    path_s = np.linspace(-105.0, 105.0, 2101)
    path_points = np.array([path.point(value) for value in path_s])
    path_data = pd.DataFrame({"path_s_m": path_s, "x_m": path_points[:, 0], "y_m": path_points[:, 1], "segment": [path.segment_name(value) for value in path_s]})
    export_origin_table(origin / "q4_turnaround_path.xlsx", path_data, x_column="path_s_m", metadata={"radius_large_m": path.radius1, "radius_small_m": path.radius2, "turn_length_m": path.turn_length})
    speed_time = pd.DataFrame({"time_s": times})
    for node in SELECTED_NODE_INDICES: speed_time[f"speed_{NODE_LABELS[node]}_m_s"] = speeds[:, node]
    export_origin_table(origin / "q4_selected_speeds_time.xlsx", speed_time, x_column="time_s", metadata={"purpose": "Q4 selected handle speeds versus time"})
    speed_nodes = pd.DataFrame({"node_index": np.arange(N_HANDLES)})
    for time_s, time_index in zip(selected_times.astype(int), selected_indices): speed_nodes[f"speed_{time_s}s_m_s"] = speeds[time_index]
    export_origin_table(origin / "q4_speed_profiles.xlsx", speed_nodes, x_column="node_index", metadata={"purpose": "Q4 speed versus handle index"})
    shape_data = pd.DataFrame({"node_index": np.arange(N_HANDLES)})
    for time_s in (-100, 0, 14, 100):
        shape_data[f"x_{time_s}s_m"] = positions[time_s + 100, :, 0]
        shape_data[f"y_{time_s}s_m"] = positions[time_s + 100, :, 1]
    export_origin_table(origin / "q4_key_shapes.xlsx", shape_data, x_column="node_index", metadata={"purpose": "Q4 key-time dragon shapes"})
    plot_path_shapes(path, positions, (-100, 0), figures / "q4_path_shapes_inbound")
    plot_path_shapes(path, positions, (14, 100), figures / "q4_path_shapes_outbound")
    plot_speeds(times, speeds, figures / "q4_speeds")
    np.savez_compressed(raw / "q4.npz", **{key: value for key, value in result.items() if isinstance(value, np.ndarray)})

    # Collision checks are intentionally sparse outside the turn and dense while
    # the head/tail can occupy the compact S-curve.
    collision_times = np.unique(np.r_[np.arange(-100, 101, 5), np.arange(-5, 31, 0.5)])
    collision_clearances = []
    collision_start = perf_counter()
    for time_s in collision_times:
        state = build_path_chain(path, float(time_s)); collision_clearances.append(minimum_bench_clearance(state.positions).clearance)
    collision_seconds = perf_counter() - collision_start

    all_link_errors = result["link_errors"].ravel()
    metrics = {
        "status": "PASS", "pitch_m": 1.7, "turn_radius_m": TURN_RADIUS_M,
        "theta_boundary_rad": path.theta_boundary,
        "large_arc_radius_m": path.radius1, "small_arc_radius_m": path.radius2,
        "radius_ratio": path.radius1 / path.radius2,
        "large_arc_length_m": path.length1, "small_arc_length_m": path.length2,
        "turn_length_m": path.turn_length, "max_turn_path_radius_m": max_turn_radius,
        "continuity_position_sample_residual_max_m": max(continuity["position"]),
        "continuity_tangent_sample_residual_max": max(continuity["tangent"]),
        "link_error_max_m": float(np.max(all_link_errors)),
        "link_error_mean_m": float(np.mean(all_link_errors)),
        "link_error_p95_m": float(np.percentile(all_link_errors, 95)),
        "velocity_constraint_residual_max_m2_s": float(np.max(result["velocity_residual_max"])),
        "finite_difference_speed_smooth_segments": fd,
        "finite_difference_speed_junction_convergence": junction_fd,
        "minimum_audited_bench_clearance_m": float(np.min(collision_clearances)),
        "single_chain_mean_seconds": float(np.mean(result["build_times"])),
        "single_chain_max_seconds": float(np.max(result["build_times"])),
        "collision_audit_seconds": collision_seconds,
        "q4_total_seconds": float(result["total_seconds"]), "excel": excel,
    }
    report = ValidationReport().add("Finite positions/speeds", check_finite(positions) and check_finite(speeds)).add("Monotonic time", check_monotonic_time(times)).add("Radius ratio R1/R2=2", abs(metrics["radius_ratio"] - 2.0) < 1e-12).add("Turn path inside boundary", max_turn_radius <= TURN_RADIUS_M + 1e-10, f"max r={max_turn_radius:.12f} m").add("Position continuity", max(continuity["position"]) < 3e-7).add("Tangent continuity", max(continuity["tangent"]) < 3e-7).add("Head speed equals 1 m/s", np.max(np.abs(speeds[:, 0] - 1.0)) < 1e-12).add("Link constraints", metrics["link_error_max_m"] < 5e-9, f"max={metrics['link_error_max_m']:.3e} m").add("Velocity constraints", metrics["velocity_constraint_residual_max_m2_s"] < 5e-9).add("Smooth-segment FD speed", fd["max_abs"] < 5e-5, f"max={fd['max_abs']:.3e} m/s").add("Junction FD convergence", min(junction_fd["successive_ratios"]) > 1.9, f"ratios={junction_fd['successive_ratios']}").add("No audited bench collision", min(collision_clearances) > 0, f"min={min(collision_clearances):.3e} m").add("Official result4.xlsx", excel["valid"])
    if not report.passed: metrics["status"] = "FAIL"
    (output / "q4_validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "q4_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = f"""# Q4 结果摘要

- 状态：{metrics['status']}
- 调头曲线：半径 {path.radius1:.9f} m 与 {path.radius2:.9f} m 的两段相切圆弧，半径比严格为 2；总弧长 {path.turn_length:.9f} m。
- 调头路径最大原点距离：{max_turn_radius:.12f} m，不越出半径 4.5 m 的调头区域。
- 相邻把手距离误差：maximum={metrics['link_error_max_m']:.3e} m，mean={metrics['link_error_mean_m']:.3e} m，P95={metrics['link_error_p95_m']:.3e} m。
- 光滑段中心差分速度最大误差：{fd['max_abs']:.3e} m/s；在三个曲率跳变连接点，h/h/2/h/4 的最大误差为 {junction_fd['max_errors_m_s']} m/s，呈一阶收敛；抽检最小板凳间隙：{min(collision_clearances):.3e} m。
- 单时刻整龙平均构造耗时：{metrics['single_chain_mean_seconds']:.5f} s；201 个正式时刻总计算耗时：{metrics['q4_total_seconds']:.3f} s。
- 官方结果：[result4.xlsx](result4.xlsx)；指定时刻表：[q4_selected_results.xlsx](q4_selected_results.xlsx)。
- 图：[盘入至入弯形态](figures/q4_path_shapes_inbound.png)、[出弯至盘出形态](figures/q4_path_shapes_outbound.png)、[速度变化](figures/q4_speeds.png)。
"""
    (output / "q4_summary.md").write_text(summary, encoding="utf-8")
    print(report.render()); print(json.dumps({"turn_length_m": path.turn_length, "link_error_max_m": metrics["link_error_max_m"], "q4_total_seconds": metrics["q4_total_seconds"]}, ensure_ascii=False))
    if not report.passed: raise RuntimeError("Q4 validation failed")


if __name__ == "__main__": main()
