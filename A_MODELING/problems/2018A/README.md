# 2018 A 题：高温作业专用服装设计

本目录只放 2018 A 的分层传热、参数标定和厚度设计逻辑。求解器先作为题目专用实现接受实战检验；只有在整题完成后确认接口可跨题复用，才考虑抽象到 `core`。

## 官方材料与数据口径

- 官方页面：全国大学生数学建模竞赛组委会“2018 年高教社杯全国大学生数学建模竞赛赛题”。
- 官方压缩包：`data/2018A/official/CUMCM2018Problems.rar`。
- SHA-256：`DC2DB8A836D6D3DA519DF0D9DB9D68F6989ADBC91F25CDC471BFA0C8F415865E`。
- A 题原文：`data/2018A/official/extracted/2018-A-Chinese/CUMCM-2018-Problem-A-Chinese.docx`。
- A 题附件：`data/2018A/official/extracted/2018-A-Chinese/CUMCM-2018-Problem-A-Chinese-Appendix.xlsx`。
- 附件 2 含 0--5400 s 共 5401 条皮肤外侧温度记录，采样间隔 1 s；时间严格递增，无 NaN/Inf。

## 四层结构与材料参数

坐标 `x` 从高温环境指向假人皮肤，所有内部计算统一使用 SI 单位。

| 层 | 物理含义 | 密度 kg/m³ | 比热 J/(kg·K) | 导热率 W/(m·K) | 厚度 |
|---|---|---:|---:|---:|---:|
| I | 外层织物 | 300 | 1377 | 0.082 | 0.6 mm = 0.0006 m |
| II | 隔热织物，设计层 | 862 | 2100 | 0.37 | 0.6--25 mm |
| III | 内层织物 | 74.2 | 1726 | 0.045 | 3.6 mm = 0.0036 m |
| IV | III 层与皮肤之间空气隙，设计层 | 1.18 | 1005 | 0.028 | 0.6--6.4 mm |

温差用 K 或 °C 数值等价；温度输出为 °C。毫米只在输入/展示边界出现，进入模型立即调用 `core.units.mm_to_m`。

## 初值、边界条件与界面条件

每层满足一维瞬态导热方程

`rho_j c_j ∂T_j/∂t = ∂/∂x(k_j ∂T_j/∂x)`。

初始时服装、空气隙和假人皮肤均取 `37 °C`。外表面与环境、内表面与恒温 `37 °C` 假人之间采用 Robin 边界：

- 外侧：进入服装的热流 `q = h_out (T_env - T_surface,out)`；
- 内侧：离开服装进入假人的热流 `q = h_skin (T_surface,skin - 37)`。

`h_out`、`h_skin` 是有效换热系数，允许把实验装置中的对流及未单独建模的辐射等效作用吸收进去。二者通过问题 1 实验数据标定，不把它们误当材料常数。

每个相邻层界面同时满足：

- 温度连续：`T_j(x_interface,t) = T_(j+1)(x_interface,t)`；
- 热流连续：`k_j ∂T_j/∂x = k_(j+1) ∂T_(j+1)/∂x`。

## 待标定参数、决策变量和安全约束

| 类别 | 变量 | 单位 | 范围/定义 |
|---|---|---|---|
| parameter | `h_out` | W/(m²·K) | 标定边界 1--500 |
| parameter | `h_skin` | W/(m²·K) | 标定边界 1--100 |
| decision | `d_II` | m | 0.0006--0.025 |
| decision | `d_IV` | m | 0.0006--0.0064 |
| output | `T_skin(t)` | °C | IV 层靠皮肤一侧的表面温度 |
| output | `duration_above_44` | s | `T_skin > 44 °C` 的时间测度 |

安全约束统一写成非负裕量：

- `g_47 = 47 - max_t(T_skin(t)) >= 0`；
- `g_44 = 300 - duration(T_skin(t) > 44) >= 0`。

问题 2 在 `T_env=65 °C`、`d_IV=5.5 mm`、`0--3600 s` 下最小化 `d_II`。问题 3 在 `T_env=80 °C`、`0--1800 s` 下最小化总设计厚度 `d_II+d_IV`；若总厚度在数值容差内相同，以较小 `d_II` 为确定性次级准则。该目标是对题目“最优厚度”的显式最小用料解释，报告中会说明其建模假设。

## 数值方法与精度策略

- 主求解器：守恒型非均匀有限体积空间离散 + Crank--Nicolson 时间推进。
- 层间面导热系数由两侧半单元热阻串联得到，自然保证单一界面温度和热流连续。
- 空间网格：按目标 `dx` 为每层独立取整单元数，层厚精确命中；厚度优化时固定目标 `dx`，而不是固定单元数。
- 主时间步：与 1 s 实验采样对齐；最终结果另做 `dt/2`、`dt/4` 与空间加密。
- 显式交叉验证：实现 Forward Euler，并检查由半离散矩阵得到的稳定步长；只在可承受的短时/验证算例上运行，不用极小步长暴力完成正式 90 min 计算。
- 解析基准：均匀单层、恒温 Dirichlet 两端的正弦模态衰减。
- 事件时间：在相邻时间层线性插值确定首次越过 44 °C 的时刻；温升单调性会另行验证。
- 临界厚度：先少量粗点确定可行/不可行区间，再用 `core.roots.solve_bracketed` 收缩；候选点必须用 FINAL 网格和时间步复算。

## 标定与验证计划

1. 用 `core.fitting.fit_least_squares` 标定两个有效换热系数，报告 RMSE、MAE、R² 和残差时序。
2. 多个起点重复标定，检查是否收敛到同一参数盆地；报告雅可比奇异值/条件数和参数相关性。
3. 单层解析解检查 CN 与显式格式。
4. 两层人工算例检查界面温度与热流残差。
5. 检查有限值、最大值原理、时间单调、能量平衡残差。
6. 对 Q1、Q2、Q3 分别做三档空间/时间收敛。
7. 对临界设计点检查邻域：略减厚应违反至少一个约束，略增厚应保持可行。

## 计划文件结构

```text
problems/2018A/
  common.py          # 材料、网格、PDE、界面与事件等题目共用逻辑
  calibration.py     # Q1 参数标定与可辨识性
  q1.py
  q2.py
  q3.py
  deliverables.py    # Excel、Origin、图表与写后验收
  validation_2018a.py
  audit_2018a.py
  tests/
```

## 运行顺序

```powershell
& '.venv/Scripts/python.exe' 'problems/2018A/q1.py'
& '.venv/Scripts/python.exe' 'problems/2018A/q2.py'
& '.venv/Scripts/python.exe' 'problems/2018A/q3.py'
& '.venv/Scripts/python.exe' 'problems/2018A/deliverables.py'
& '.venv/Scripts/python.exe' 'problems/2018A/audit_2018a.py'
& '.venv/Scripts/python.exe' -m pytest -q
```

`deliverables.py` 会重新执行标定、三档收敛与 FINAL 优化，因此是完整但较慢的正式入口；单问脚本用于比赛中快速定位问题。
