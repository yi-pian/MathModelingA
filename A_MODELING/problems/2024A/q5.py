"""Q5: maximum constant head speed under the 2 m/s handle-speed limit."""

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
from core.optimization import optimize_scalar
from core.plotting import COLORS, save_figure, use_paper_style
from core.roots import solve_bracketed
from core.validation import ValidationReport, check_finite

from common import (
    NODE_LABELS, N_HANDLES, TurnaroundPath, build_path_chain,
    link_error_statistics, velocity_constraint_residuals,
)
from deliverables import RESULT_DIR


class SpeedRatioEvaluator:
    def __init__(self, path):
        self.path = path
        self.cache: dict[float, tuple[float, int]] = {}
        self.call_seconds: list[float] = []

    def evaluate(self, head_s):
        key = round(float(head_s), 11)
        if key not in self.cache:
            start = perf_counter(); state = build_path_chain(self.path, key)
            self.call_seconds.append(perf_counter() - start)
            index = int(np.argmax(state.speeds))
            self.cache[key] = (float(state.speeds[index]), index)
        return self.cache[key]

    def ratio(self, head_s):
        return self.evaluate(head_s)[0]


def locate_tail_exit(path):
    function = lambda head_s: float(build_path_chain(path, head_s).coordinates[-1] - path.turn_length)
    return solve_bracketed(function, (350.0, 420.0), xtol=2e-10, rtol=2e-11)


def refine_local_maxima(evaluator, grid_s, grid_ratios, *, candidate_count=12):
    local_indices = [
        index for index in range(1, len(grid_s) - 1)
        if grid_ratios[index] >= grid_ratios[index - 1] and grid_ratios[index] >= grid_ratios[index + 1]
    ]
    local_indices.sort(key=lambda index: grid_ratios[index], reverse=True)
    records = []
    start = perf_counter()
    for index in local_indices[:candidate_count]:
        result = optimize_scalar(
            evaluator.ratio,
            bounds=(float(grid_s[index - 1]), float(grid_s[index + 1])),
            direction="maximize", options={"xatol": 2e-10},
        )
        ratio, node = evaluator.evaluate(result.x)
        records.append({
            "head_s_m": float(result.x), "ratio": ratio, "node_index": node,
            "success": bool(result.success), "nfev": result.nfev,
            "coarse_center_m": float(grid_s[index]),
        })
    records.sort(key=lambda item: item["ratio"], reverse=True)
    return records, perf_counter() - start


def local_grid_convergence(evaluator, center_s):
    records = []
    for step in (0.1, 0.05, 0.025, 0.0125):
        # Half-cell offset deliberately excludes the refined optimum.  Otherwise
        # all nested grids would report the same zero sampling error.
        values_s = np.arange(center_s - 0.6 + 0.5 * step, center_s + 0.6, step)
        ratios = np.array([evaluator.ratio(value) for value in values_s])
        index = int(np.argmax(ratios))
        records.append({"step_m": step, "head_s_m": float(values_s[index]), "ratio": float(ratios[index])})
    return records


def plot_speed_ratio(grid_s, grid_ratios, optimum_s, optimum_ratio, local_s, local_ratios, output):
    import matplotlib.pyplot as plt
    use_paper_style(); figure, axes = plt.subplots(1, 2, figsize=(10.0, 3.7))
    axes[0].plot(grid_s, grid_ratios, color=COLORS[0], linewidth=0.9)
    axes[0].scatter([optimum_s], [optimum_ratio], color=COLORS[1], s=24, zorder=3)
    axes[0].set(xlabel="Head path coordinate (m)", ylabel="Maximum speed ratio", title="Whole passage")
    axes[0].grid(True, color="#DDDDDD", linewidth=0.45)
    axes[1].plot(local_s, local_ratios, color=COLORS[0], linewidth=1.1)
    axes[1].scatter([optimum_s], [optimum_ratio], color=COLORS[1], s=24, zorder=3)
    axes[1].set(xlabel="Head path coordinate (m)", ylabel="Maximum speed ratio", title="Critical neighborhood")
    axes[1].grid(True, color="#DDDDDD", linewidth=0.45)
    figure.tight_layout(); save_figure(figure, output); plt.close(figure)


def main():
    output = RESULT_DIR; figures = output / "figures"; origin = output / "origin_data"
    figures.mkdir(parents=True, exist_ok=True); origin.mkdir(parents=True, exist_ok=True)
    total_start = perf_counter(); path = TurnaroundPath(); evaluator = SpeedRatioEvaluator(path)
    tail_exit = locate_tail_exit(path); active_end = float(tail_exit.root)

    scan_start = perf_counter()
    grid_s = np.arange(0.0, active_end, 1.0)
    if grid_s[-1] < active_end: grid_s = np.r_[grid_s, active_end]
    grid_ratios = np.array([evaluator.ratio(value) for value in grid_s])
    scan_seconds = perf_counter() - scan_start
    refined, optimization_seconds = refine_local_maxima(evaluator, grid_s, grid_ratios)
    if not refined:
        raise RuntimeError("no local speed-ratio maximum found")
    optimum = refined[0]
    optimum_s, maximum_ratio = optimum["head_s_m"], optimum["ratio"]
    maximum_head_speed = 2.0 / maximum_ratio

    convergence = local_grid_convergence(evaluator, optimum_s)
    convergence_error = [maximum_ratio - item["ratio"] for item in convergence]
    local_s = np.linspace(optimum_s - 1.0, optimum_s + 1.0, 201)
    local_ratios = np.array([evaluator.ratio(value) for value in local_s])

    unit_state = build_path_chain(path, optimum_s)
    limit_state = build_path_chain(path, optimum_s, head_speed_m_s=maximum_head_speed)
    maximum_handle_speed = float(np.max(limit_state.speeds))
    limiting_nodes = np.flatnonzero(maximum_handle_speed - limit_state.speeds <= 1e-10).astype(int)
    limiting_node = int(limiting_nodes[0])
    speed_residual = float(np.max(limit_state.speeds) - 2.0)
    velocity_residual = float(np.max(np.abs(velocity_constraint_residuals(limit_state))))
    link_stats = link_error_statistics(limit_state.positions)
    speed_epsilon = 1e-6
    below_max = maximum_ratio * (maximum_head_speed - speed_epsilon)
    above_max = maximum_ratio * (maximum_head_speed + speed_epsilon)

    # Outside the active interval all handles lie on one spiral branch. Audit both
    # tails of the infinite-time motion and verify the post-turn envelope decreases.
    before_s = np.arange(-100.0, 0.1, 5.0)
    before_ratios = np.array([evaluator.ratio(value) for value in before_s])
    after_s = active_end + np.arange(0.0, 501.0, 20.0)
    after_ratios = np.array([evaluator.ratio(value) for value in after_s])

    scan_data = pd.DataFrame({"head_s_m": grid_s, "maximum_speed_ratio": grid_ratios})
    export_origin_table(origin / "q5_speed_ratio_scan.xlsx", scan_data, x_column="head_s_m", metadata={"tail_exit_head_s_m": active_end, "unit_head_speed": "1 m/s"})
    local_data = pd.DataFrame({"head_s_m": local_s, "maximum_speed_ratio": local_ratios})
    export_origin_table(origin / "q5_speed_ratio_critical.xlsx", local_data, x_column="head_s_m", metadata={"critical_head_s_m": optimum_s, "critical_ratio": maximum_ratio})
    profile = pd.DataFrame({
        "node_index": np.arange(N_HANDLES), "node_label": NODE_LABELS,
        "unit_head_speed_ratio": unit_state.speeds,
        "speed_at_limit_m_s": limit_state.speeds,
        "path_coordinate_m": limit_state.coordinates,
    })
    export_origin_table(origin / "q5_limiting_speed_profile.xlsx", profile, x_column="node_index", metadata={"head_speed_limit_m_s": maximum_head_speed, "limiting_nodes": ",".join(map(str, limiting_nodes))})
    write_excel_checked(output / "q5_speed_limit.xlsx", {"Summary": pd.DataFrame({
        "quantity": ["maximum head speed", "maximum unit-speed ratio", "critical head path coordinate", "limiting handle indices"],
        "value": [maximum_head_speed, maximum_ratio, optimum_s, ",".join(map(str, limiting_nodes))],
        "unit": ["m/s", "-", "m", "0-based"],
    }), "Critical speed profile": profile}, decimals=9)
    plot_speed_ratio(grid_s, grid_ratios, optimum_s, maximum_ratio, local_s, local_ratios, figures / "q5_speed_limit")

    total_seconds = perf_counter() - total_start
    metrics = {
        "status": "PASS", "maximum_head_speed_m_s": maximum_head_speed,
        "maximum_unit_head_speed_ratio": maximum_ratio,
        "critical_head_path_coordinate_m": optimum_s,
        "limiting_handle_indices": limiting_nodes.tolist(),
        "limiting_handle_labels": [NODE_LABELS[index] for index in limiting_nodes],
        "tail_exit_head_path_coordinate_m": active_end,
        "tail_exit_root_residual_m": tail_exit.residual,
        "coarse_step_m": 1.0, "coarse_points": len(grid_s),
        "refined_candidate_count": len(refined), "refined_candidates": refined,
        "local_grid_convergence": convergence,
        "local_grid_errors_from_refined": convergence_error,
        "speed_limit_residual_m_s": speed_residual,
        "max_speed_below_limit_m_s": below_max,
        "max_speed_above_limit_m_s": above_max,
        "speed_epsilon_m_s": speed_epsilon,
        "pre_turn_audit_max_ratio": float(np.max(before_ratios)),
        "post_turn_audit_max_ratio": float(np.max(after_ratios)),
        "post_turn_audit_last_ratio": float(after_ratios[-1]),
        "post_turn_audit_monotone": bool(np.all(np.diff(after_ratios) <= 1e-10)),
        "link_error_max_m": link_stats.maximum, "link_error_mean_m": link_stats.mean,
        "link_error_p95_m": link_stats.percentile95,
        "velocity_constraint_residual_max_m2_s": velocity_residual,
        "single_chain_mean_seconds": float(np.mean(evaluator.call_seconds)),
        "full_coarse_scan_seconds": scan_seconds,
        "optimization_seconds": optimization_seconds,
        "q5_total_seconds": total_seconds,
    }
    report = ValidationReport().add("Tail-exit root residual", tail_exit.residual < 1e-8, f"{tail_exit.residual:.3e} m").add("All coarse candidates refined", all(item["success"] for item in refined)).add("Local-grid convergence", np.all(np.diff(convergence_error) < 0) and convergence_error[-1] < 1e-4, str(convergence_error)).add("Speed limit active", abs(speed_residual) < 1e-10, f"{speed_residual:.3e} m/s").add("Smaller head speed feasible", below_max < 2.0, f"max={below_max:.9f} m/s").add("Larger head speed infeasible", above_max > 2.0, f"max={above_max:.9f} m/s").add("Pre-turn envelope bounded", np.max(before_ratios) <= maximum_ratio).add("Post-turn envelope bounded", np.max(after_ratios) <= maximum_ratio).add("Post-turn envelope decreases", np.all(np.diff(after_ratios) <= 1e-10), f"last={after_ratios[-1]:.9f}").add("Link constraints", link_stats.maximum < 5e-9).add("Velocity constraints", velocity_residual < 5e-9).add("Finite limiting state", check_finite(limit_state.positions) and check_finite(limit_state.speeds))
    if not report.passed: metrics["status"] = "FAIL"
    (output / "q5_validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "q5_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = f"""# Q5 结果摘要

- 状态：{metrics['status']}
- 龙头最大恒定速度：**{maximum_head_speed:.9f} m/s**。
- 单位龙头速度下的全程最大速度放大系数：{maximum_ratio:.12f}，出现于龙头路径坐标 {optimum_s:.9f} m；同时达到上限的把手索引为 {limiting_nodes.tolist()}，对应 {[NODE_LABELS[index] for index in limiting_nodes]}。
- 极限速度回代后的最大把手速度残差：{speed_residual:.3e} m/s；龙头速度 ±{speed_epsilon:.0e} m/s 后分别满足/违反 2 m/s 上限。
- 龙头从进入调头曲线到龙尾后把手离开调头曲线的路径坐标区间为 [0, {active_end:.9f}] m；采用 1 m 粗扫描识别局部峰，再用显式 maximize 的有界优化精化 {len(refined)} 个候选。
- 相邻把手距离误差：maximum={link_stats.maximum:.3e} m，mean={link_stats.mean:.3e} m，P95={link_stats.percentile95:.3e} m。
- 粗扫描耗时：{scan_seconds:.3f} s；候选优化耗时：{optimization_seconds:.3f} s；Q5 总耗时：{total_seconds:.3f} s。
- 数据：[q5_speed_limit.xlsx](q5_speed_limit.xlsx)；图：[速度上限搜索](figures/q5_speed_limit.png)。
"""
    (output / "q5_summary.md").write_text(summary, encoding="utf-8")
    print(report.render()); print(json.dumps({"maximum_head_speed_m_s": maximum_head_speed, "maximum_ratio": maximum_ratio, "limiting_nodes": limiting_nodes.tolist(), "q5_total_seconds": total_seconds}, ensure_ascii=False))
    if not report.passed: raise RuntimeError("Q5 validation failed")


if __name__ == "__main__": main()
