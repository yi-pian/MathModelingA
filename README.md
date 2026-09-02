# MathModeling

面向全国大学生数学建模竞赛（CUMCM）A 题的数值建模与计算项目。项目以 Python 为主要语言，提供可复用的数值计算核心库、历年 A 题实现、比赛模板、自动化测试、结果文件和论文图表数据。

## 项目特点

- 覆盖有限差分/有限体积、ODE、非线性方程、参数拟合、优化、几何计算和空间搜索等常见 A 题方法。
- 核心代码与题目专用代码分离，便于复用和审查。
- 统一处理单位、坐标系、数值稳定性、误差、灵敏度和结果验证。
- 支持导出 Excel、PNG、PDF、SVG 以及 Origin 可编辑数据。
- 历年题目结果、验证报告和图表按年份归档，方便复现。

## 目录结构

```text
MathModeling/
├─ A_MODELING/
│  ├─ core/                 通用数值计算与绘图模块
│  ├─ problems/             历年题目和各小问的实现
│  ├─ templates/            可复制的建模代码模板
│  ├─ knowledge/            A 题建模知识卡
│  ├─ tests/                核心模块测试
│  ├─ examples/             示例与 smoke test
│  ├─ data/                 题目原始材料（原则上只读）
│  ├─ results/              计算结果、图表和验证报告
│  └─ logs/                 实验记录与 AI 使用记录
├─ contest_backups/         比赛过程备份
├─ ORIGIN_STYLE_SYSTEM/     Origin 科研绘图样式与训练资料
└─ CONTEST_*.md             比赛模式、状态和交付检查文档
```

## 环境要求

- Windows
- Python 3.12（推荐使用 `A_MODELING/.venv`）
- NumPy、SciPy、pandas、Matplotlib、openpyxl、pytest
- 如需 Origin 图形工程，还需要本机安装 Origin 并配置 Origin MCP

## 快速开始

在项目根目录执行：

```powershell
cd A_MODELING
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

运行核心测试和基础示例：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples\smoke_test.py
```

运行某一年度题目时，先阅读对应目录的 README，再执行该年度的题目脚本。例如：

```powershell
.\.venv\Scripts\python.exe problems\2025A\q1.py
.\.venv\Scripts\python.exe problems\2025A\q2.py
.\.venv\Scripts\python.exe problems\2025A\q3.py
.\.venv\Scripts\python.exe problems\2025A\q4.py
.\.venv\Scripts\python.exe problems\2025A\q5.py
```

不同年份的完整运行顺序和交付脚本以对应的 `problems/<年份>/README.md` 为准。

## 通用模块

| 模块 | 用途 |
|---|---|
| `core.roots` | 一维求根、非线性方程组和多根搜索 |
| `core.ode` | 常微分方程、事件和容差收敛 |
| `core.integration` | 数值积分 |
| `core.fitting` | 曲线拟合和最小二乘参数标定 |
| `core.optimization` | 局部/全局优化 |
| `core.geometry` | 二维/三维几何、距离和碰撞判断 |
| `core.spatial` | 最近邻与半径候选搜索 |
| `core.sensitivity` | 参数灵敏度分析 |
| `core.validation` | 数值结果标准检查和验证报告 |
| `core.plotting` | 论文级图表输出 |
| `core.export` | Excel、CSV 等结果导出 |

所有核心角度接口使用弧度；核心物理量优先使用 SI 单位。详细接口说明见 [`A_MODELING/README.md`](A_MODELING/README.md) 和 [`A_MODELING/knowledge/index.md`](A_MODELING/knowledge/index.md)。

## 历年题目

| 年份 | 主题 | 代码 | 结果 |
|---|---|---|---|
| 2018 A | 高温作业专用服装设计 | [`problems/2018A`](A_MODELING/problems/2018A) | [`results/2018A`](A_MODELING/results/2018A) |
| 2022 A | 波浪能最大输出功率设计 | [`problems/2022A`](A_MODELING/problems/2022A) | [`results/2022A`](A_MODELING/results/2022A) |
| 2023 A | 定日镜场的优化设计 | [`problems/2023A`](A_MODELING/problems/2023A) | [`results/2023A`](A_MODELING/results/2023A) |
| 2024 A | 板凳龙运动与碰撞分析 | [`problems/2024A`](A_MODELING/problems/2024A) | [`results/2024A`](A_MODELING/results/2024A) |
| 2025 A | 烟幕干扰弹的投放策略 | [`problems/2025A`](A_MODELING/problems/2025A) | [`results/2025A`](A_MODELING/results/2025A) |

`problems/2026A` 和 `results/2026A` 用于当前比赛过程中的题目实现与正式结果。

## 推荐工作流

1. 在 `problems/<年份>/` 的 README 中明确问题理解、变量、单位、模型、目标、约束和验证方案。
2. 使用最接近的 `templates/` 模板建立题目脚本。
3. 先运行小规模算例和专项测试，再进行正式计算。
4. 检查残差、约束、NaN/Inf、量级、收敛性和灵敏度。
5. 将最终数值、验证报告、Excel、图表和可编辑数据写入 `results/<年份>/`。
6. 论文中的数字只从最终结果索引和对应验证文件中选取。

题目原始数据位于 `data/`，默认只读；官方 Excel 模板必须复制到结果目录后再填写，不能直接覆盖原件。

## 当前状态

最近一次赛前检查已通过，详见 [`PRE_FLIGHT_CHECK.md`](PRE_FLIGHT_CHECK.md)。当前比赛状态和最终结果登记分别见：

- [`CONTEST_STATUS.md`](CONTEST_STATUS.md)
- [`FINAL_RESULTS_INDEX.md`](FINAL_RESULTS_INDEX.md)
- [`FINAL_FIGURE_INDEX.md`](FINAL_FIGURE_INDEX.md)

## 项目规范

详细的代码、单位、数值方法、测试、Excel 和交付规范见 [`A_MODELING/AGENTS.md`](A_MODELING/AGENTS.md)。

## 说明

自动化测试只能验证代码接口、解析基准和数值一致性，不能替代对题意、模型假设、单位、坐标系和物理合理性的人工复核。正式结果应以验证报告和人工审查共同确认。
