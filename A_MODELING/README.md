# A_MODELING：高教杯 A 题数值计算集成库

这是面向 CUMCM A 题工程机理建模的轻量 Python 工具箱。它把常见比赛流程压缩为：明确模型和单位 → 解析/小规模验证 → 正式计算 → 稳定性与灵敏度 → 论文图 → 官方 Excel/Origin 数据。核心库不包含历年题参数，也不替代建模手决策。

2026 正式比赛按 [`2026A_CONTEST_PLAYBOOK.md`](2026A_CONTEST_PLAYBOOK.md) 执行。当前状态为 `FREEZE CORE BEFORE CONTEST`；除可复现的通用 BUG 外，不修改 `core/`、`templates/` 或 `knowledge/`。

## 5 分钟开始

```powershell
cd A_MODELING
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples\smoke_test.py
```

比赛时复制最接近的 `templates/` 文件到 `problems/qX/`，先填文件顶部的变量、单位、模型、约束和验证基准，再改计算部分。不要直接改 `core/` 以适配某一题。

## 核心入口

| 任务 | 推荐入口 |
|---|---|
| 有变号区间求根 | `core.roots.solve_bracketed` |
| 非线性方程组 | `core.roots.solve_system` |
| 2D/3D 几何与碰撞 | `core.geometry` 中的向量函数 |
| ODE 与事件 | `core.ode.solve_ode` |
| 大规模最近邻/半径候选 | `core.spatial.nearest_neighbors` / `pairs_within_radius` |
| 容差收敛 | `core.ode.tolerance_convergence` |
| 参数标定 | `core.fitting.fit_curve` / `fit_least_squares` |
| 连续优化 | `core.optimization.optimize_local` / `optimize_global` |
| 灵敏度 | `core.sensitivity.multi_parameter_sensitivity` |
| 自动数值检查 | `core.validation.standard_report` |
| 论文图与导出 | `core.plotting`、`core.export` |

全部角度接口接受 rad；核心物理量应在调用前转换成 SI。优化方向用字符串显式声明。几何函数将零向量、无效 AABB、负半径等作为输入错误，不静默猜测。

## 目录

```text
A_MODELING/
├─ AGENTS.md              项目内协作与验收规则
├─ core/                  可复用、已测试的核心函数
├─ templates/             可直接复制修改的比赛模板
├─ knowledge/             15 张 A 题实用知识卡
├─ tests/                 解析解和边界测试
├─ examples/              热传导与统一 smoke test
├─ problems/q1..q5/       当届题目代码
├─ data/                  题目原始输入，只读
├─ results/               正式结果与 Origin 数据
└─ logs/                  实验与 AI 使用记录
```

## 推荐工作流

每一问先在 `problems/qX/README.md` 写问题理解、变量表、数学模型、目标函数、约束、初值、边界、数值方法和验证方案。运行后把验证报告、结果、图和 Origin 表放入 `results/qX/`。`core.export.write_excel_checked` 用于自建官方结果簿；有官方模板时用 `fill_excel_template` 复制后填写，禁止覆盖原件。

## 近年 A 题能力映射

| 年份 | 本库能力 |
|---|---|
| 2018 A | `examples/validation_examples/heat_1d.py`、有限差分知识卡、网格/步长稳定性 |
| 2020 A | ODE、参数标定、残差诊断、连续优化与灵敏度 |
| 2022 A | 多状态 ODE、事件、功率/能量积分、阻尼参数优化 |
| 2023 A | 三维旋转、线/面/球、空间距离、遮挡、AABB、向量化 |
| 2024 A | 区间求根、多根扫描、链式几何约束、碰撞、粗到细搜索、Excel |
| 2025 A | 三维运动、球体遮挡、布尔时间区间、连续优化、轨迹输出 |

映射只说明基础能力，不代表历年原题已硬编码或一键求解。

## 验证边界

自动测试能证明解析例、接口约束和数值一致性；它不能证明新题模型正确或结果物理合理。每个结果仍需人工复核公式、单位、坐标系、量级、约束方向、状态顺序和题意对应关系。验证报告中的 `MANUAL CHECK REQUIRED` 是诚实边界，不是失败。
