"""Q1: 0–300 s spiral-in positions, speeds, validation, figures and result1.xlsx."""

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
    ArchimedeanSpiral, NODE_LABELS, N_HANDLES, SELECTED_NODE_INDICES,
    build_spiral_chain, head_theta_at_time, link_error_statistics,
    velocity_constraint_residuals,
)
from deliverables import OFFICIAL_DIR, RESULT_DIR, fill_time_series_template, selected_position_table, selected_speed_table


def solve_q1():
    times = np.arange(0.0, 301.0, 1.0)
    positions = np.empty((len(times), N_HANDLES, 2))
    speeds = np.empty((len(times), N_HANDLES))
    parameters = np.empty((len(times), N_HANDLES))
    root_residuals = np.empty(len(times))
    link_errors = np.empty((len(times), N_HANDLES - 1))
    velocity_residual_max = np.empty(len(times))
    build_times = np.empty(len(times))
    start_total = perf_counter()
    for time_index, time_s in enumerate(times):
        theta_head, root_residuals[time_index] = head_theta_at_time(time_s)
        start = perf_counter()
        state = build_spiral_chain(theta_head)
        build_times[time_index] = perf_counter() - start
        positions[time_index] = state.positions
        speeds[time_index] = state.speeds
        parameters[time_index] = state.coordinates
        link_errors[time_index] = link_error_statistics(state.positions).errors
        velocity_residual_max[time_index] = np.max(np.abs(velocity_constraint_residuals(state)))
    total_seconds = perf_counter() - start_total
    return {
        "times": times, "positions": positions, "speeds": speeds, "parameters": parameters,
        "root_residuals": root_residuals, "link_errors": link_errors,
        "velocity_residual_max": velocity_residual_max, "build_times": build_times,
        "total_seconds": total_seconds,
    }


def finite_difference_speed_check(check_times, step_s=1e-3):
    absolute_errors = []
    relative_errors = []
    for time_s in check_times:
        minus = build_spiral_chain(head_theta_at_time(time_s - step_s)[0])
        center = build_spiral_chain(head_theta_at_time(time_s)[0])
        plus = build_spiral_chain(head_theta_at_time(time_s + step_s)[0])
        numerical = np.linalg.norm((plus.positions - minus.positions) / (2.0 * step_s), axis=1)
        error = np.abs(numerical - center.speeds)
        absolute_errors.extend(error.tolist())
        relative_errors.extend((error / np.maximum(center.speeds, 1e-15)).tolist())
    return {"step_s": step_s, "max_abs": float(max(absolute_errors)), "max_rel": float(max(relative_errors)), "mean_abs": float(np.mean(absolute_errors))}


def plot_q1_shapes(times, positions, output):
    import matplotlib.pyplot as plt
    use_paper_style()
    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.4))
    spiral = ArchimedeanSpiral(0.55)
    theta_values = np.linspace(45, 118, 5000)
    curve = np.array([spiral.point(theta) for theta in theta_values])
    for axis, time_s in zip(axes, (0, 300)):
        time_index = int(time_s)
        axis.plot(curve[:, 0], curve[:, 1], color="#C7C7C7", linewidth=0.65, label="Spiral")
        axis.plot(positions[time_index, :, 0], positions[time_index, :, 1], color=COLORS[0], linewidth=1.0, label="Dragon handles")
        axis.scatter(positions[time_index, 0, 0], positions[time_index, 0, 1], color=COLORS[1], s=25, zorder=3, label="Head")
        axis.set(xlabel="x (m)", ylabel="y (m)", title=f"t = {time_s} s")
        axis.set_aspect("equal", adjustable="box"); axis.grid(True, color="#DDDDDD", linewidth=0.45)
    axes[0].legend(loc="best")
    figure.tight_layout(); save_figure(figure, output); plt.close(figure)


def plot_q1_speeds(times, speeds, output):
    import matplotlib.pyplot as plt
    use_paper_style(); figure, axis = plt.subplots(figsize=(6.0, 3.7))
    for color_index, node in enumerate(SELECTED_NODE_INDICES):
        axis.plot(times, speeds[:, node], color=COLORS[color_index % len(COLORS)], label=NODE_LABELS[node])
    axis.set(xlabel="Time (s)", ylabel="Speed (m/s)"); axis.grid(True, color="#DDDDDD", linewidth=0.45); axis.legend(ncol=2, fontsize=7)
    figure.tight_layout(); save_figure(figure, output); plt.close(figure)


def main():
    output = RESULT_DIR; figures = output / "figures"; origin = output / "origin_data"; raw = output / "raw"
    for directory in (figures, origin, raw): directory.mkdir(parents=True, exist_ok=True)
    result = solve_q1()
    times, positions, speeds = result["times"], result["positions"], result["speeds"]
    fd = finite_difference_speed_check([0, 60, 120, 180, 240, 300])
    excel = fill_time_series_template(OFFICIAL_DIR / "result1.xlsx", output / "result1.xlsx", times, positions, speeds)
    selected_times = np.array([0, 60, 120, 180, 240, 300], dtype=float)
    selected_indices = selected_times.astype(int)
    position_table = selected_position_table(selected_times, positions[selected_indices])
    speed_table = selected_speed_table(selected_times, speeds[selected_indices])
    write_excel_checked(output / "q1_selected_results.xlsx", {"Position": position_table, "Speed": speed_table}, decimals=6)
    shape_data = pd.DataFrame({"node_index": np.arange(N_HANDLES)})
    for time_s in (0, 300):
        shape_data[f"x_{time_s}s_m"] = positions[time_s, :, 0]
        shape_data[f"y_{time_s}s_m"] = positions[time_s, :, 1]
    export_origin_table(origin / "q1_dragon_shapes.xlsx", shape_data, x_column="node_index", metadata={"purpose": "Q1 dragon shapes at 0 s and 300 s", "unit": "position in m"})
    speed_data = pd.DataFrame({"time_s": times})
    for node in SELECTED_NODE_INDICES: speed_data[f"speed_{NODE_LABELS[node]}_m_s"] = speeds[:, node]
    export_origin_table(origin / "q1_selected_speeds.xlsx", speed_data, x_column="time_s", metadata={"purpose": "Q1 selected handle speeds"})
    plot_q1_shapes(times, positions, figures / "q1_shapes")
    plot_q1_speeds(times, speeds, figures / "q1_speeds")
    np.savez_compressed(raw / "q1.npz", **{key: value for key, value in result.items() if isinstance(value, np.ndarray)})
    aggregate_errors = result["link_errors"].ravel()
    metrics = {
        "status": "PASS",
        "root_residual_max_m": float(np.max(result["root_residuals"])),
        "link_error_max_m": float(np.max(aggregate_errors)),
        "link_error_mean_m": float(np.mean(aggregate_errors)),
        "link_error_p95_m": float(np.percentile(aggregate_errors, 95)),
        "velocity_constraint_residual_max_m2_s": float(np.max(result["velocity_residual_max"])),
        "finite_difference_speed": fd,
        "single_chain_mean_seconds": float(np.mean(result["build_times"])),
        "single_chain_max_seconds": float(np.max(result["build_times"])),
        "q1_total_seconds": float(result["total_seconds"]),
        "excel": excel,
    }
    report = ValidationReport().add("Finite positions/speeds", check_finite(positions) and check_finite(speeds)).add("Monotonic time", check_monotonic_time(times)).add("Head speed equals 1 m/s", np.max(np.abs(speeds[:, 0] - 1.0)) < 1e-12).add("Arc inversion residual", metrics["root_residual_max_m"] < 1e-9, f"max={metrics['root_residual_max_m']:.3e} m").add("Link constraints", metrics["link_error_max_m"] < 5e-9, f"max={metrics['link_error_max_m']:.3e} m").add("Velocity constraints", metrics["velocity_constraint_residual_max_m2_s"] < 5e-9).add("Finite-difference speed", fd["max_abs"] < 5e-5, f"max abs={fd['max_abs']:.3e} m/s").add("Official result1.xlsx", excel["valid"])
    if not report.passed: metrics["status"] = "FAIL"
    (output / "q1_validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "q1_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = f"""# Q1 结果摘要\n\n- 状态：{metrics['status']}\n- 模型：阿基米德螺线弧长反解 + 逐节弦长 Brent 求根 + 刚性杆速度传播。\n- 时间：0–300 s，步长 1 s，共 301 个状态、224 个把手。\n- 弧长求根最大残差：{metrics['root_residual_max_m']:.3e} m。\n- 相邻把手距离误差：maximum={metrics['link_error_max_m']:.3e} m，mean={metrics['link_error_mean_m']:.3e} m，P95={metrics['link_error_p95_m']:.3e} m。\n- 中心差分速度最大误差：{fd['max_abs']:.3e} m/s。\n- 单时刻整龙平均构造耗时：{metrics['single_chain_mean_seconds']:.6f} s；Q1 总计算耗时：{metrics['q1_total_seconds']:.3f} s。\n- 官方结果：[result1.xlsx](result1.xlsx)；指定节点表：[q1_selected_results.xlsx](q1_selected_results.xlsx)。\n- 图：[q1_shapes.png](figures/q1_shapes.png)、[q1_speeds.png](figures/q1_speeds.png)。\n"""
    (output / "q1_summary.md").write_text(summary, encoding="utf-8")
    print(report.render()); print(json.dumps({key: metrics[key] for key in ("status", "link_error_max_m", "q1_total_seconds")}, ensure_ascii=False))
    if not report.passed: raise RuntimeError("Q1 validation failed")


if __name__ == "__main__": main()
