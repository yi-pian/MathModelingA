"""Q3: minimum spiral pitch that remains collision-free to the turn boundary."""

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

from core.export import export_origin_table
from core.optimization import coarse_to_fine
from core.plotting import COLORS, save_figure, use_paper_style
from core.roots import solve_bracketed
from core.validation import ValidationReport, check_finite

from common import (
    ArchimedeanSpiral, TURN_RADIUS_M, build_bench_rectangles,
    build_spiral_chain, link_error_statistics, minimum_bench_clearance,
    velocity_constraint_residuals,
)
from deliverables import RESULT_DIR


class ApproachClearance:
    """Cached nested minimization of physical-bench clearance for one pitch."""

    def __init__(self):
        self.state_cache: dict[tuple[float, float], tuple[float, tuple[int, int] | None]] = {}
        self.pitch_evaluations: list[dict] = []

    def clearance(self, pitch_m: float, theta_head: float):
        key = (round(float(pitch_m), 13), round(float(theta_head), 12))
        if key not in self.state_cache:
            state = build_spiral_chain(theta_head, pitch_m=pitch_m)
            collision = minimum_bench_clearance(state.positions)
            self.state_cache[key] = (collision.clearance, collision.pair)
        return self.state_cache[key]

    def minimum(self, pitch_m: float, *, grid_points=31):
        """Minimize over the innermost turn; an outer-interval audit is done separately."""
        spiral = ArchimedeanSpiral(pitch_m)
        theta_boundary = TURN_RADIUS_M / spiral.a

        def objective(theta_head):
            return self.clearance(pitch_m, theta_head)[0]

        start = perf_counter()
        optimized, detail = coarse_to_fine(
            objective,
            (theta_boundary, theta_boundary + 2.0 * np.pi),
            grid_points=grid_points,
            direction="minimize",
            xatol=2e-11,
        )
        clearance, pair = self.clearance(pitch_m, optimized.x)
        record = {
            "pitch_m": float(pitch_m), "clearance_m": float(clearance),
            "theta_head_rad": float(optimized.x), "head_radius_m": float(spiral.a * optimized.x),
            "pair": None if pair is None else list(pair), "grid_points": int(grid_points),
            "seconds": perf_counter() - start, "optimizer_success": bool(optimized.success),
            "optimizer_nfev": optimized.nfev,
        }
        self.pitch_evaluations.append(record)
        return record


def plot_pitch_clearance(data, critical_pitch, output):
    import matplotlib.pyplot as plt
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.6, 3.6))
    axis.plot(data["pitch_m"] * 100.0, data["minimum_clearance_m"] * 100.0, "o-", color=COLORS[0], markersize=3.5)
    axis.axhline(0.0, color=COLORS[1], linewidth=0.9)
    axis.axvline(critical_pitch * 100.0, color="#555555", linestyle="--", linewidth=0.8)
    axis.set(xlabel="Spiral pitch (cm)", ylabel="Minimum signed clearance (cm)")
    axis.grid(True, color="#DDDDDD", linewidth=0.45); figure.tight_layout()
    save_figure(figure, output); plt.close(figure)


def plot_critical_state(state, pair, output):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.8, 5.2))
    rectangles = build_bench_rectangles(state.positions)
    for index, rectangle in enumerate(rectangles):
        highlighted = index in pair
        axis.add_patch(Polygon(
            rectangle.vertices, closed=True,
            facecolor=COLORS[1] if highlighted else COLORS[0],
            edgecolor="#333333" if highlighted else "none",
            alpha=0.78 if highlighted else 0.12, linewidth=1.0,
        ))
    axis.plot(state.positions[:, 0], state.positions[:, 1], color="#555555", linewidth=0.45)
    focus = np.vstack([rectangles[index].vertices for index in pair])
    margin = 1.0
    axis.set_xlim(focus[:, 0].min() - margin, focus[:, 0].max() + margin)
    axis.set_ylim(focus[:, 1].min() - margin, focus[:, 1].max() + margin)
    axis.set(xlabel="x (m)", ylabel="y (m)"); axis.set_aspect("equal", adjustable="box")
    axis.grid(True, color="#DDDDDD", linewidth=0.45); figure.tight_layout()
    save_figure(figure, output); plt.close(figure)


def main():
    output = RESULT_DIR; figures = output / "figures"; origin = output / "origin_data"
    figures.mkdir(parents=True, exist_ok=True); origin.mkdir(parents=True, exist_ok=True)
    total_start = perf_counter(); evaluator = ApproachClearance()

    coarse_pitches = np.arange(0.35, 0.601, 0.025)
    coarse_records = [evaluator.minimum(float(pitch), grid_points=25) for pitch in coarse_pitches]
    brackets = []
    for left, right in zip(coarse_records[:-1], coarse_records[1:]):
        if np.signbit(left["clearance_m"]) != np.signbit(right["clearance_m"]):
            brackets.append((left["pitch_m"], right["pitch_m"]))
    if len(brackets) != 1:
        raise RuntimeError(f"expected one critical-pitch bracket, got {brackets}")

    root = solve_bracketed(
        lambda pitch: evaluator.minimum(pitch, grid_points=31)["clearance_m"],
        brackets[0], xtol=2e-11, rtol=2e-11, maxiter=60,
    )
    critical_pitch = float(root.root)
    critical = evaluator.minimum(critical_pitch, grid_points=81)
    critical_state = build_spiral_chain(critical["theta_head_rad"], pitch_m=critical_pitch)
    critical_collision = minimum_bench_clearance(critical_state.positions)
    pair = critical_collision.pair
    if pair is None:
        raise RuntimeError("critical collision pair is missing")

    # Nested-grid convergence and one-sided feasibility checks.
    grid_records = [evaluator.minimum(critical_pitch, grid_points=points) for points in (21, 41, 81)]
    theta_convergence = max(abs(item["theta_head_rad"] - grid_records[-1]["theta_head_rad"]) for item in grid_records)
    clearance_convergence = max(abs(item["clearance_m"] - grid_records[-1]["clearance_m"]) for item in grid_records)
    pitch_epsilon = 1e-5
    below = evaluator.minimum(critical_pitch - pitch_epsilon, grid_points=61)
    above = evaluator.minimum(critical_pitch + pitch_epsilon, grid_points=61)

    # Audit the entire approach from the 16th turn to the boundary; the refined
    # minimum is inserted explicitly so the sampling grid cannot hide tangency.
    spiral = ArchimedeanSpiral(critical_pitch)
    theta_boundary = TURN_RADIUS_M / spiral.a
    outer_thetas = np.arange(theta_boundary, 32.0 * np.pi + 0.125, 0.125)
    outer_clearances = np.array([evaluator.clearance(critical_pitch, theta)[0] for theta in outer_thetas])
    outside_inner_turn = outer_thetas >= theta_boundary + 2.0 * np.pi
    outer_min = float(np.min(outer_clearances[outside_inner_turn]))

    link_stats = link_error_statistics(critical_state.positions)
    velocity_residual = float(np.max(np.abs(velocity_constraint_residuals(critical_state))))
    sensitivity_pitches = np.linspace(critical_pitch - 0.025, critical_pitch + 0.025, 21)
    sensitivity_records = [evaluator.minimum(float(pitch), grid_points=31) for pitch in sensitivity_pitches]
    sensitivity = pd.DataFrame({
        "pitch_m": sensitivity_pitches,
        "minimum_clearance_m": [item["clearance_m"] for item in sensitivity_records],
        "critical_head_radius_m": [item["head_radius_m"] for item in sensitivity_records],
    })
    export_origin_table(origin / "q3_pitch_sensitivity.xlsx", sensitivity, x_column="pitch_m", metadata={"purpose": "Q3 pitch criticality", "clearance_sign": "positive separated; negative overlap"})
    critical_nodes = pd.DataFrame({
        "node_index": np.arange(len(critical_state.positions)),
        "x_m": critical_state.positions[:, 0], "y_m": critical_state.positions[:, 1],
        "speed_m_s": critical_state.speeds,
    })
    export_origin_table(origin / "q3_critical_state.xlsx", critical_nodes, x_column="node_index", metadata={"critical_pitch_m": f"{critical_pitch:.12f}", "critical_pair": str(pair)})
    plot_pitch_clearance(sensitivity, critical_pitch, figures / "q3_pitch_clearance")
    plot_critical_state(critical_state, pair, figures / "q3_critical_contact")

    total_seconds = perf_counter() - total_start
    metrics = {
        "status": "PASS", "critical_pitch_m": critical_pitch,
        "critical_pitch_cm": 100.0 * critical_pitch,
        "critical_clearance_m": critical_collision.clearance,
        "root_reported_residual_m": root.residual,
        "critical_theta_head_rad": critical["theta_head_rad"],
        "critical_head_radius_m": critical["head_radius_m"],
        "critical_pair_bench_indices": list(pair),
        "pitch_bracket_m": list(brackets[0]), "pitch_epsilon_m": pitch_epsilon,
        "clearance_below_m": below["clearance_m"], "clearance_above_m": above["clearance_m"],
        "nested_theta_convergence_rad": theta_convergence,
        "nested_clearance_convergence_m": clearance_convergence,
        "outer_approach_min_clearance_m": outer_min,
        "outer_approach_samples": int(np.sum(outside_inner_turn)),
        "link_error_max_m": link_stats.maximum, "link_error_mean_m": link_stats.mean,
        "link_error_p95_m": link_stats.percentile95,
        "velocity_constraint_residual_max_m2_s": velocity_residual,
        "state_evaluations": len(evaluator.state_cache),
        "mean_nested_evaluation_seconds": float(np.mean([item["seconds"] for item in evaluator.pitch_evaluations])),
        "q3_total_seconds": total_seconds,
    }
    report = ValidationReport().add("Single coarse sign change", len(brackets) == 1, str(brackets)).add("Critical root residual", abs(critical_collision.clearance) < 1e-8, f"{critical_collision.clearance:.3e} m").add("Smaller pitch collides", below["clearance_m"] < 0, f"{below['clearance_m']:.3e} m").add("Larger pitch separates", above["clearance_m"] > 0, f"{above['clearance_m']:.3e} m").add("Nested-grid convergence", theta_convergence < 1e-6 and clearance_convergence < 1e-8, f"dtheta={theta_convergence:.3e}, dc={clearance_convergence:.3e}").add("Outer approach collision-free", outer_min > 0, f"min={outer_min:.3e} m").add("Link constraints", link_stats.maximum < 5e-9).add("Velocity constraints", velocity_residual < 5e-9).add("Finite critical state", check_finite(critical_state.positions) and check_finite(critical_state.speeds))
    if not report.passed: metrics["status"] = "FAIL"
    (output / "q3_validation_report.txt").write_text(report.render(), encoding="utf-8")
    (output / "q3_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = f"""# Q3 结果摘要

- 状态：{metrics['status']}
- 最小螺距：**{critical_pitch * 100.0:.6f} cm**（未提前按题面展示精度截断）。
- 临界接触发生在龙头半径 {critical['head_radius_m']:.6f} m、板凳对 {pair}，不是在 4.5 m 边界瞬间；因此模型对整个进入过程取最小间隙，而非只检查边界状态。
- 临界间隙残差：{critical_collision.clearance:.3e} m；螺距 ±{pitch_epsilon * 100:.3f} cm 时最小间隙分别为 {below['clearance_m']:.3e}、{above['clearance_m']:.3e} m。
- 对第 16 圈至调头边界的外层区间抽检最小间隙：{outer_min:.3e} m。
- 嵌套角度优化 21/41/81 点收敛差：{theta_convergence:.3e} rad；间隙差：{clearance_convergence:.3e} m。
- 链长误差 maximum={link_stats.maximum:.3e} m，mean={link_stats.mean:.3e} m，P95={link_stats.percentile95:.3e} m。
- Q3 总耗时：{total_seconds:.3f} s。
- 图：[螺距敏感性](figures/q3_pitch_clearance.png)、[临界接触](figures/q3_critical_contact.png)。
"""
    (output / "q3_summary.md").write_text(summary, encoding="utf-8")
    print(report.render()); print(json.dumps({"critical_pitch_cm": metrics["critical_pitch_cm"], "pair": pair, "q3_total_seconds": total_seconds}, ensure_ascii=False))
    if not report.passed: raise RuntimeError("Q3 validation failed")


if __name__ == "__main__": main()
