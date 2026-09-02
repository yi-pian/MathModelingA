# Signature Scientific Style v1.1 — Micro-refinement Review

**Final status: SIGNATURE SCIENTIFIC STYLE V1.1 — FROZEN**

本轮仅执行微观修订，没有改变主配色、字体体系、版式语言或直接标注策略。四张图均由 Origin MCP 重新生成，并完成 PNG、PDF、SVG 与 `.opju` 导出。

## 逐图修订

### 图1：MAIN SINGLE LINE

- 主曲线由 1.45 pt 降至 1.36 pt，约降低 6.2%。
- Optimum marker 由 3.30 pt 降至 3.05 pt，约降低 7.6%。
- 复核结果：曲线仍保持第一视觉层级，峰值点可见但不突兀；修改相较 v1 没有造成视觉下降。

### 图2：MULTI-LINE COMPARISON

- 保留直接标注，不恢复图例。
- x 轴右界由 27.5 扩至 29，增加约 5.5% 的标签缓冲区。
- Proposed、Conservative、Aggressive、Baseline 使用不同 x/y 位置；Aggressive 移入曲线间空域，避免与自身曲线和 Baseline 虚线穿插。
- 复核结果：四个标签均可独立识别，Proposed 仍保持第一视觉层级。

### 图3：SENSITIVITY ANALYTICAL

- 保留浅灰 `y=0` 参考线。
- y 轴上界扩至 27，为 Unit cost 增加 headroom。
- Unit cost / Demand 与 Capacity / Efficiency 分别采用错位直标；负坐标标签使用安全坐标变量，避免 Origin 将负值误判为命令开关。
- 复核结果：顶部、底部标签均无碰撞，主线与参考线层级清楚。

### 图4：CONTOUR MAIN

- 保留蓝青—绿—浅黄连续色彩体系。
- 坐标主刻度长度与粗细分别设为 1.2 pt、0.28 pt，较 v1 分别降低约 40% 与 38%；次刻度同步降权。
- Colorbar 宽度参数由 125 降至 102，约降低 18.4%；标签字号降至 5.1 pt，标题降至 4.3 pt。
- 连续响应面采用 19 级填色，仅保留 7 条等高线；Colorbar 同步只显示 7 个主刻度。
- Optimum 文字移至橙色点右侧邻近位置，点与注记形成明确关系。
- 复核结果：填色连续、等高线克制、Colorbar 不再压过主体。

## 最终视觉审查

| 检查项 | 结论 | 证据 |
|---|---|---|
| Label collision | 通过 | 图2四标签错位布置；图3上下两组标签分离；图4 Optimum 与点相邻且不遮挡 |
| Visual hierarchy | 通过 | Primary 深蓝保持最高权重；辅助曲线与参考线降权；Highlight 仅用于最优点 |
| Whitespace | 通过 | 图2增加右侧缓冲；图3增加顶部 headroom；其余绘图区比例保持 v1 |
| Tick consistency | 通过 | 图1–3保持冻结轴体系；图4刻度长度/粗细降低并与其余图的轻量语言一致 |
| Colorbar balance | 通过 | 宽度缩小、字号降低、主刻度减至 7 个，标题与色带比例协调 |
| Cross-figure consistency | 通过 | 字体、配色、背景、线型语义、绘图区和导出规格保持同一设计系统 |

## 冻结决定

四类模板正式冻结：

- `SCP_SINGLE_LINE_MAIN_v11_FROZEN`
- `SCP_MULTI_LINE_COMPARISON_v11_FROZEN`
- `SCP_SENSITIVITY_ANALYTICAL_v11_FROZEN`
- `SCP_CONTOUR_MAIN_v11_FROZEN`

后续不再对这四类图进行纯审美迭代。只有真实比赛数据暴露出新的可读性、科学准确性或版面适配问题时，才允许创建新版本；不得静默覆盖 v1.1。
