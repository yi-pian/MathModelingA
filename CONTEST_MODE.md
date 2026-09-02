# CONTEST MODE

比赛拿到 A 题后：

1. **STEP 1｜题面入库**：保存官方题面、附件和 Excel 模板，原始文件只读。
2. **STEP 2｜建模手交接**：接收目标、变量、单位、公式、初边值、目标与约束。
3. **STEP 3｜MODEL CONFIRMATION**：消除会改变数学含义的歧义；未确认不得实现。
4. **STEP 4｜实现**：优先调用 Frozen Core，再用稳定模板，最后写 `problems/2026A/` 题目专用代码。
5. **STEP 5｜验证**：检查单位、初边值、物理量级、约束、残差、精度稳定性和关键值独立复算。
6. **STEP 6｜STANDARD RUN**：形成可验证的标准精度结果，供分析与优化使用。
7. **STEP 7｜FINAL RUN**：停止探索，以最终模型、参数、搜索空间和精度高精度复算。
8. **STEP 8｜GRAPH EDITOR**：先定结论与证据，再决定正文图、Supporting、Appendix 和删图。
9. **STEP 9｜ORIGIN / PYTHON 正式图**：只读取 FINAL DATA；按科学坐标结构选择工具。
10. **STEP 10｜Excel / results / paper handoff**：统一数字来源，生成结果表和极简论文手交接。
11. **STEP 11｜SUBMISSION FREEZE**：冻结模型、数字和图；只允许纠错、一致性修复和排版整理。

> 唯一现场入口：本文件。禁止跳过 **MODEL CONFIRMATION**，禁止看到公式后直接编写完整程序。

## 当前最高状态

- `A_MODELING`: `CORE = FROZEN`; `HISTORICAL BENCHMARK = COMPLETE`; `2025 BLIND BENCHMARK = CONDITIONAL PASS`; `2026A_CONTEST_PLAYBOOK = ACTIVE`
- `ORIGIN_STYLE_SYSTEM`: `SIGNATURE STYLE = FROZEN`; `GRAPH EDITOR = HUMAN REVIEW PASSED`; `BLIND TEST = PASSED`; `STATUS = CONTEST READY — STYLE + GRAPH EDITOR COMPLETE`
- 比赛期间以正确性、完整性、验证和 FINAL 结果为先，不继续开发框架、训练风格或重跑历史 benchmark。

## 六个短口令

| 口令 | 自动进入的流程 | 必须输出/边界 |
|---|---|---|
| `开始A题 Q1` | 读取题面与建模手材料，检查目标、变量、单位、公式、约束、初边值和待确认项 | `Q1_IMPLEMENTATION_PRECHECK.md`；禁止正式求解 |
| `确认模型，开始实现` | 最小正确实现 → 验证 → STANDARD RUN | 仅在所有 `MODEL_CONFIRMATION_REQUIRED` 已回答后执行 |
| `做 FINAL` | 固定模型、参数、搜索空间和精度，高精度独立复算 | `FINAL_RESULT`、`FINAL_VALIDATION`、`FINAL_TABLE_DATA`；旧 STANDARD 数值退出论文链路 |
| `做图` | 结论 → 证据 → 选图 → 删图 → 层级 → 工具 → 模板 → 绘图 | 先过 Graph Editor Gate；正式图只读 FINAL DATA |
| `交论文手` | 压缩为模型、公式、假设、最终结果、验证、图、Caption、TAKEAWAY、局限 | `PAPER_HANDOFF.md`；不交调试日志 |
| `最终检查` | 执行 Submission Freeze Check | 数字、图、表、单位、假设和声明全部一致 |

## MODEL CONFIRMATION Gate

建模手交接必须覆盖：`QUESTION GOAL / KNOWN DATA / VARIABLES / UNITS / FORMULAS / INITIAL CONDITIONS / BOUNDARY CONDITIONS / DECISION VARIABLES / SEARCH RANGE / OBJECTIVE / CONSTRAINTS / EXPECTED OUTPUT / MODEL ASSUMPTIONS`。

缺失内容若会改变数学含义，立即输出：

```text
MODEL_CONFIRMATION_REQUIRED
- Question:
- Missing/ambiguous definition:
- Why it changes the model:
- Who must confirm: 建模手
```

确认前只允许拆解和预检，不允许正式求解或擅自决定参考轴、遮挡定义、边界条件、搜索空间、有效区间、积分范围或初始状态。

## 固定结果链

`EXPLORATORY → STANDARD → FINAL`

只有 **FINAL** 可以进入论文正文、最终 Excel、正式图片、摘要和结论。默认路径：

- 题目代码：`A_MODELING/problems/2026A/`
- 结果：`A_MODELING/results/2026A/`
- 每问建议：`qX/solve.py`, `config.py`, `validate.py`, `export.py`
- 正式数字唯一索引：[FINAL_RESULTS_INDEX.md](FINAL_RESULTS_INDEX.md)
- 正式图片唯一索引：[FINAL_FIGURE_INDEX.md](FINAL_FIGURE_INDEX.md)
- 赛场状态：[CONTEST_STATUS.md](CONTEST_STATUS.md)
- 当前阻塞：[CONTEST_BLOCKERS.md](CONTEST_BLOCKERS.md)
- 快速健康检查：[PRE_FLIGHT_CHECK.md](PRE_FLIGHT_CHECK.md)

## 详细规则入口

- 数值实现、FINAL、Excel 与论文交接：[2026A_CONTEST_PLAYBOOK.md](A_MODELING/2026A_CONTEST_PLAYBOOK.md)
- 结论—证据—选图、删图与工具边界：[GRAPH_EDITOR_PLAYBOOK.md](ORIGIN_STYLE_SYSTEM/GRAPH_EDITOR_PLAYBOOK.md)
- Origin 冻结状态：[CONTEST_READY_STATUS.md](ORIGIN_STYLE_SYSTEM/CONTEST_READY_STATUS.md)

Frozen Core 与 Frozen Origin Templates 只能调用，不能覆盖。真实数据允许调整轴范围、ticks、标注位置、图例、marker 密度、contour levels、colorbar、panel spacing 和 camera angle；不得改变 Signature palette、字体体系、Highlight 语义、白底和总体 publication style。

## SUBMISSION FREEZE CHECK

- 所有正文数字均能在 `FINAL_RESULTS_INDEX.md` 定位到 FINAL 源文件和验证文件。
- 图表数字与 Excel 数字逐项一致，单位与模型假设一致。
- Excel 回读无 `NaN/Inf`，工作表、列序和关键单元格正确。
- 每张正式图均登记 FINAL 数据源、工具、模板、Caption 和 TAKEAWAY。
- 未把 `best verified solution found` 夸大为未经证明的 `global optimum`。
- FINAL 数字如有任何变化，同步复核论文、Excel、图、摘要和结论。

进入 Submission Freeze 后禁止改模型定义、换优化方法或换图形风格；只允许修正明确错误、数字一致性、图注、排版与文件整理。
