"""Q2: first physical bench contact using coarse event bracketing and Brent refinement."""

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
from core.roots import solve_bracketed
from core.validation import ValidationReport, check_finite

from common import (
    NODE_LABELS, SELECTED_NODE_INDICES, build_bench_rectangles, build_spiral_chain,
    head_theta_at_time, link_error_statistics, minimum_bench_clearance,
    pair_clearance, velocity_constraint_residuals,
)
from deliverables import RESULT_DIR, fill_result2_template, selected_position_table, selected_speed_table


def state_and_collision(time_s):
    theta, arc_residual = head_theta_at_time(time_s)
    state = build_spiral_chain(theta)
    collision = minimum_bench_clearance(state.positions)
    return state, collision, arc_residual


def scan_first_collision(start_s, stop_s, step_s, cache=None):
    cache = {} if cache is None else cache
    start_clock = perf_counter()
    previous_time = float(start_s)
    if previous_time not in cache: cache[previous_time] = state_and_collision(previous_time)
    previous_collision = cache[previous_time][1]
    if previous_collision.clearance <= 0: raise ValueError("scan starts in collision")
    evaluations = 1
    times = np.arange(start_s + step_s, stop_s + 0.5 * step_s, step_s)
    for time_s in times:
        key = float(round(time_s, 12))
        if key not in cache: cache[key] = state_and_collision(key)
        evaluations += 1
        collision = cache[key][1]
        if collision.clearance <= 0:
            return (previous_time, key), collision.pair, {"seconds": perf_counter() - start_clock, "evaluations": evaluations, "step_s": step_s}, cache
        previous_time, previous_collision = key, collision
    raise RuntimeError("no collision found in scan interval")


def refine_pair_event(bracket, pair):
    def clearance(time_s):
        theta, _ = head_theta_at_time(time_s)
        state = build_spiral_chain(theta)
        return pair_clearance(state.positions, pair)
    start = perf_counter()
    result = solve_bracketed(clearance, bracket, xtol=2e-11, rtol=2e-13, maxiter=100)
    return result, perf_counter() - start


def plot_critical_state(state, pair, output):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    use_paper_style(); figure, axis = plt.subplots(figsize=(6.0, 5.4))
    rectangles = build_bench_rectangles(state.positions)
    for index, rectangle in enumerate(rectangles):
        highlighted = index in pair
        patch = Polygon(rectangle.vertices, closed=True, facecolor=COLORS[1] if highlighted else COLORS[0], edgecolor="#333333" if highlighted else "none", alpha=0.75 if highlighted else 0.13, linewidth=1.0)
        axis.add_patch(patch)
    axis.plot(state.positions[:, 0], state.positions[:, 1], color="#555555", linewidth=0.5)
    for index in pair:
        axis.text(rectangles[index].center[0], rectangles[index].center[1], f"Bench {index}", fontsize=8)
    focus = np.vstack([rectangles[index].vertices for index in pair])
    margin = 1.2
    axis.set_xlim(focus[:, 0].min() - margin, focus[:, 0].max() + margin); axis.set_ylim(focus[:, 1].min() - margin, focus[:, 1].max() + margin)
    axis.set(xlabel="x (m)", ylabel="y (m)"); axis.set_aspect("equal", adjustable="box"); axis.grid(True, color="#DDDDDD", linewidth=0.45)
    figure.tight_layout(); save_figure(figure, output); plt.close(figure)


def main():
    output = RESULT_DIR; figures = output / "figures"; origin = output / "origin_data"
    figures.mkdir(parents=True, exist_ok=True); origin.mkdir(parents=True, exist_ok=True)
    total_start = perf_counter(); cache = {}
    # A 1 s coarse safety audit covers the whole pre-event interval; event-
    # convergence scans start at 300 s and are refined continuously.
    early_clearances = []
    for time_s in np.arange(0.0, 301.0, 1.0):
        state, collision, _ = state_and_collision(float(time_s)); early_clearances.append(collision.clearance)
    scans, refined = [], []
    for step_s in (1.0, 0.5, 0.25):
        bracket, pair, performance, cache = scan_first_collision(300.0, 430.0, step_s, cache)
        root, refine_seconds = refine_pair_event(bracket, pair)
        scans.append({"step_s": step_s, "bracket": list(bracket), "pair": list(pair), **performance, "refine_seconds": refine_seconds})
        refined.append(float(root.root))
    event_time = refined[-1]
    pair = tuple(scans[-1]["pair"])
    event_state, event_collision, arc_residual = state_and_collision(event_time)
    event_pair_clearance = pair_clearance(event_state.positions, pair)
    epsilon_s = 1e-4
    before_state, before_collision, _ = state_and_collision(event_time - epsilon_s)
    after_state, after_collision, _ = state_and_collision(event_time + epsilon_s)
    link_stats = link_error_statistics(event_state.positions)
    velocity_residual = float(np.max(np.abs(velocity_constraint_residuals(event_state))))
    excel = fill_result2_template(output / "result2.xlsx", event_state.positions, event_state.speeds)
    selected_positions = selected_position_table([event_time], event_state.positions[None, :, :])
    selected_speeds = selected_speed_table([event_time], event_state.speeds[None, :])
    write_excel_checked(output / "q2_selected_results.xlsx", {"Position": selected_positions, "Speed": selected_speeds}, decimals=6)
    node_data = pd.DataFrame({"node_index": np.arange(len(event_state.positions)), "x_m": event_state.positions[:, 0], "y_m": event_state.positions[:, 1], "speed_m_s": event_state.speeds})
    export_origin_table(origin / "q2_critical_state.xlsx", node_data, x_column="node_index", metadata={"event_time_s": f"{event_time:.12f}", "collision_pair": str(pair)})
    near_times = np.linspace(event_time - 0.5, event_time + 0.5, 101)
    near_clearances = []
    for time_s in near_times:
        theta, _ = head_theta_at_time(time_s); state = build_spiral_chain(theta); near_clearances.append(pair_clearance(state.positions, pair))
    clearance_data = pd.DataFrame({"time_s": near_times, "signed_clearance_m": near_clearances})
    export_origin_table(origin / "q2_collision_event.xlsx", clearance_data, x_column="time_s", metadata={"positive": "separated", "zero": "contact", "negative": "overlap"})
    plot_critical_state(event_state, pair, figures / "q2_critical_collision")
    import matplotlib.pyplot as plt
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.4, 3.4)); axis.plot(near_times, near_clearances, color=COLORS[0]); axis.axhline(0, color=COLORS[1], linewidth=0.9); axis.axvline(event_time, color="#555555", linestyle="--", linewidth=0.8); axis.set(xlabel="Time (s)", ylabel="Signed clearance (m)"); axis.grid(True, color="#DDDDDD", linewidth=0.45); figure.tight_layout(); save_figure(figure, figures / "q2_event_clearance"); plt.close(figure)
    total_seconds = perf_counter() - total_start
    event_convergence = float(np.max(np.abs(np.asarray(refined) - event_time)))
    metrics = {
        "status": "PASS", "event_time_s": event_time, "collision_pair_bench_indices": list(pair),
        "collision_pair_labels": [f"板凳{index}" for index in pair], "event_pair_clearance_m": event_pair_clearance,
        "global_clearance_before_m": before_collision.clearance, "global_clearance_at_m": event_collision.clearance,
        "global_clearance_after_m": after_collision.clearance, "epsilon_s": epsilon_s,
        "coarse_step_refined_times_s": dict(zip(("1.0", "0.5", "0.25"), refined)),
        "event_time_convergence_s": event_convergence, "early_min_clearance_m": float(min(early_clearances)),
        "arc_residual_m": arc_residual, "link_error_max_m": link_stats.maximum,
        "link_error_mean_m": link_stats.mean, "link_error_p95_m": link_stats.percentile95,
        "velocity_constraint_residual_max_m2_s": velocity_residual, "scans": scans,
        "single_collision_check_seconds": float(np.mean([item["seconds"] / item["evaluations"] for item in scans])),
        "q2_total_seconds": total_seconds, "excel": excel,
    }
    report = ValidationReport().add("Q1 interval collision-free", min(early_clearances) > 0, f"1 s audit min={min(early_clearances):.6e} m").add("Step convergence", event_convergence < 1e-8, f"spread={event_convergence:.3e} s").add("Event root residual", abs(event_pair_clearance) < 1e-9, f"clearance={event_pair_clearance:.3e} m").add("Before event separated", before_collision.clearance > 0, f"{before_collision.clearance:.3e} m").add("After event intersecting", after_collision.clearance < 0, f"{after_collision.clearance:.3e} m").add("Link constraints", link_stats.maximum < 5e-9).add("Velocity constraints", velocity_residual < 5e-9).add("Finite state", check_finite(event_state.positions) and check_finite(event_state.speeds)).add("Official result2.xlsx", excel["valid"])
    if not report.passed: metrics["status"] = "FAIL"
    (output / "q2_validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "q2_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = f"""# Q2 结果摘要\n\n- 状态：{metrics['status']}\n- 首次板凳接触时刻：**{event_time:.9f} s**。\n- 临界板凳对（0 基板凳编号）：{pair}。\n- 事件间隙残差：{event_pair_clearance:.3e} m。\n- 在 t*−{epsilon_s:g} s、t*、t*+{epsilon_s:g} s 的全局最小间隙分别为 {before_collision.clearance:.6e}、{event_collision.clearance:.6e}、{after_collision.clearance:.6e} m。\n- 1/0.5/0.25 s 粗扫描经 Brent 精化后的时刻差：{event_convergence:.3e} s。\n- 链长误差 maximum={link_stats.maximum:.3e} m，mean={link_stats.mean:.3e} m，P95={link_stats.percentile95:.3e} m。\n- Q2 总耗时：{total_seconds:.3f} s；单时刻碰撞检查（含整龙构造）平均 {metrics['single_collision_check_seconds']:.5f} s。\n- 官方结果：[result2.xlsx](result2.xlsx)。\n- 图：[临界碰撞](figures/q2_critical_collision.png)、[事件间隙](figures/q2_event_clearance.png)。\n"""
    (output / "q2_summary.md").write_text(summary, encoding="utf-8")
    print(report.render()); print(json.dumps({"event_time_s": event_time, "pair": pair, "q2_total_seconds": total_seconds}, ensure_ascii=False))
    if not report.passed: raise RuntimeError("Q2 validation failed")


if __name__ == "__main__": main()
