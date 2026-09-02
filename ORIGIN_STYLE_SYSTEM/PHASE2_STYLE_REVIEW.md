# Phase 2 Style Review

**Status: PHASE 2 CANDIDATES — HUMAN AESTHETIC REVIEW PENDING**

本轮只将 **Signature Scientific Style v1.1** 迁移到五类新图，没有重设计视觉系统，也没有修改或覆盖任何 `v11_FROZEN` 模板。全部图形由 Origin MCP 在 Origin 2026 中创建、排版和导出；Python 仅用于确定性数据生成与 MCP 流程编排。

## 1. 继承情况

| 视觉语义 | Phase 2 落实方式 |
|---|---|
| Primary | 深海军蓝，用于拟合线、best objective、Observed 主结果和核心曲面语义 |
| Highlight | 暖橙，用于异常点、最终最优值和 3D 最优位置 |
| Secondary | 低饱和青，用于 population mean、Model 等次要结果 |
| Neutral | 灰蓝/中性灰，用于观测散点、零参考线和辅助信息 |
| 连续场 | 继承 Contour 的低饱和蓝—青绿—浅黄体系；禁止彩虹色 |
| 版式 | 纯白背景、轻量标记、克制字号、无网格/阴影/装饰、优先直接标注 |

## 2. 五类候选图审查

### 2.1 Scatter + Fit

交付图：`P2_SCATTER_FIT`、`P2_SCATTER_RESIDUAL`、`P2_SCATTER_STRESS`。

- 观测值使用小型、低权重灰蓝 marker；拟合线使用 Primary，避免散点淹没关系。
- 异常点仅用暖橙强调，不扩大成展示型 marker。
- 拟合图使用直接标签，无图例；残差图增加浅灰 `y=0` 参考线。
- 压力图含 601 个观测点、4 个异常点和长轴标题；以更小 marker、高透明度和局部轴标题缩小保持可读。

结论：拟合关系、异常点和残差结构具有清楚的视觉主次，与 v1.1 的线图语义一致。

### 2.2 Heatmap

交付图：`P2_HEATMAP`、`P2_HEATMAP_STRESS`。

- 连续场采用 19 级低饱和蓝—青绿—浅黄填色，不使用彩虹色。
- Colorbar 竖直放置、独立标注 `Temperature (C)`，刻度与边框降权。
- 标准图优先表现连续温度传播，不叠加无必要的密集等值线。
- 压力图含 21,901 个网格单元、长轴标题和靠近边界的局部热点；颜色范围保留高低值辨识度。

结论：与冻结 Contour 属于同一连续场设计系统，同时保留 Heatmap 的场分布阅读效率。

### 2.3 Optimization Convergence

交付图：`P2_CONVERGENCE`、`P2_CONVERGENCE_STRESS`。

- `Best objective` 为 Primary 粗实线；`Population mean` 为低饱和青色虚线。
- 最终最优值以小型暖橙点标记；两条曲线均采用直接标签，不使用图例。
- 标准图表达收敛速度与群体稳定性，而非单一下降轨迹。
- 压力图覆盖 2,000 次迭代和跨数量级目标值，使用预计算 `log10` 变换并在轴标题中明确披露。

结论：第一眼先读 best，再读 mean，最终值关系明确，主次层级通过。

### 2.4 Multi-panel（最高优先级）

交付图：`P2_MULTIPANEL_2X2`、`P2_MULTIPANEL_STRESS`。

- 采用 2×2 布局：(a) displacement、(b) velocity、(c) power、(d) error。
- 四个子图严格对齐；统一边框、字号和线型；仅保留一个页面级共享图例和一个共享 X 轴标题。
- `(a)(b)(c)(d)` 位置统一，子图间距兼顾双栏缩放后的可读性。
- 压力图同时处理小量级位移、大量级功率、长时域和 `log10 |error|`，允许各面板独立 Y 轴范围，不为形式一致牺牲科学可读性。

结论：跨子图层级、共享元素和留白稳定；作为本轮最高优先级图型，已具备候选模板质量。

### 2.5 3D Surface

交付图：`P2_SURFACE_3D`、`P2_SURFACE_3D_STRESS`。

- 使用与 Contour 同源的蓝—青绿连续色彩语义，关闭夸张曲面网格，仅保留克制等值结构。
- 采用 45° 的清晰分析视角，避免低角度遮挡最优位置，也不使用炫技透视。
- X/Y/Z 轴标题从矩阵维度标签在绘图前写入，解决 OpenGL 3D 默认标题问题。
- 暖橙最优点保持真实 X/Y 位置；为避免与曲面发生 z-fighting，仅对显示用 Z 坐标抬升目标范围的 5%，原始最优值仍保留在 CSV 和执行记录中。
- 压力图将最优点放在边界附近，检验视角、轴比例和色条的稳定性。

结论：3D Surface 定义为辅助图。若 Contour 能更准确地表达最优位置和数值关系，应优先使用 Contour，3D 不推荐替代主图。

## 3. 视觉复查

| 检查项 | 结果 | 说明 |
|---|---|---|
| Label collision | PASS | 直标与曲线错位放置；压力图长标题采用局部字号适配 |
| Visual hierarchy | PASS | Primary 始终优先，Secondary/Neutral 降权，Highlight 只标结论点 |
| Whitespace | PASS | 单图绘图区充足；2×2 子图间距和页面边距均衡 |
| Tick consistency | PASS | 2D 图使用统一轻量刻度；3D/Colorbar 保持同级但按空间适配 |
| Colorbar balance | PASS | Heatmap 色条窄、带单位标签；3D 色条不压缩曲面主体 |
| Cross-figure consistency | PASS | 字体、纯白背景、配色语义、主次层级与 v1.1 一致 |

## 4. 真实数据压力测试与模板适配

`TEMPLATE_ADAPTATION_REQUIRED` 表示候选模板需要数据依赖的适配层，不表示模板失败。以下适配已经在压力图中实现，后续真实数据应再次检查。

| 图型 | 困难情况 | 状态 | 必须允许的适配 |
|---|---|---|---|
| Scatter + Fit | 601 点、重叠、长标签、4 个异常点 | `TEMPLATE_ADAPTATION_REQUIRED` | marker 0.42、66% 透明、异常点独立层、Y 标题 5.2 pt、轴范围重算 |
| Heatmap | 21,901 单元、长标签、靠边界热点 | `TEMPLATE_ADAPTATION_REQUIRED` | colorbar 范围/刻度、轴比例、连续色级、必要时少量等值线 |
| Convergence | 2,000 次迭代、目标值跨数量级 | `TEMPLATE_ADAPTATION_REQUIRED` | `log10` 数据变换、直接标签位置、Y 轴范围、最终点标注 |
| Multi-panel | 四面板量纲与范围悬殊 | `TEMPLATE_ADAPTATION_REQUIRED` | 各面板独立 Y 轴、共享图例/轴标题、误差变换、面板间距 |
| 3D Surface | 最优点靠边界、陡峭响应面 | `TEMPLATE_ADAPTATION_REQUIRED` | 视角、轴比例、色条范围、最优点可见性；必要时改用 Contour 主图 |

## 5. 候选模板

| 模板 | 状态 | 用途 |
|---|---|---|
| `SCP_SCATTER_FIT_v20_CANDIDATE.otpu` | human review pending | Scatter + Fit；Residual 共享其散点语义 |
| `SCP_HEATMAP_CONTINUOUS_v20_CANDIDATE.otpu` | human review pending | 连续场 Heatmap |
| `SCP_OPTIMIZATION_CONVERGENCE_v20_CANDIDATE.otpu` | human review pending | best / mean 收敛分析 |
| `SCP_MULTIPANEL_2X2_v20_CANDIDATE.otpu` | human review pending | 2×2 论文多面板 |
| `SCP_SURFACE_3D_AUXILIARY_v20_CANDIDATE.otpu` | human review pending | 3D 辅助曲面 |

五个模板均保存于 `C:\Users\YiPian\.origin-mcp\templates`，并带有 `phase2`、`candidate`、`human-review-pending` 标签。它们尚未冻结。

## 6. 冻结模板完整性

四个 `v11_FROZEN` 模板的 SHA-256 与 `FROZEN_MANIFEST_V1_1.json` 逐一一致：

- `SCP_SINGLE_LINE_MAIN_v11_FROZEN` — MATCH
- `SCP_MULTI_LINE_COMPARISON_v11_FROZEN` — MATCH
- `SCP_SENSITIVITY_ANALYTICAL_v11_FROZEN` — MATCH
- `SCP_CONTOUR_MAIN_v11_FROZEN` — MATCH

因此，本轮没有修改 Signature Scientific Style v1.1。

## 7. 交付完整性

- 11 组图（含 Residual 与每类压力图），共 33 个 Origin 导出文件。
- PNG：全部可解码；单图 2400×1702，多面板 3600×2552。
- PDF：11/11 具有有效 `%PDF` 文件头。
- SVG：11/11 含有效 `<svg>` 根元素。
- Origin 源工程：`outputs/phase2/ORIGIN_PHASE2_STYLE_TRAINING.opju`。
- 复现记录：`training_data/phase2_mcp_execution.json`、`phase2_graph_inspection.json`、`phase2_template_save.json`。

## 8. 人工审美验收入口

本轮不执行冻结。请重点审查：散点密度与异常点权重、Heatmap 色条比例、收敛图直标位置、2×2 缩放可读性、3D 视角与辅助图定位。

完成后停止，等待人工审美反馈。
