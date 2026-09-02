# GRAPH EDITOR BLIND TEST — INDEPENDENT ANALYSIS

`BLIND_TEST_PROBLEM = 2020 CUMCM Problem A — Reflow Oven Temperature Profile (炉温曲线)`

Status: **INDEPENDENT GRAPH PLAN FROZEN BEFORE PLOTTING AND EXTERNAL CROSS-CHECK**  
No Origin session, plotting library, formal figure, external solution paper, or external figure was used to make these decisions.

## 0. Result-data contract

The blind-test result package uses a calibrated lumped thermal model:

`dT/dt = k(T,Ta)[Ta(x(t)) - T]`, with `x(t)=vt`.

The official 70 cm/min experiment calibrates a spatial furnace-air profile and asymmetric heating/cooling thermal inertia. Calibration quality is RMSE `1.484 °C`, MAE `1.041 °C`, and maximum absolute residual `4.814 °C`.

This agreement supports **calibration adequacy and model–data agreement only**. It does not establish parameter identifiability.

Optimization results are limited to the adopted model, official temperature/speed bounds, chosen Q4 lexicographic rule, and fixed numerical search. Global optimality is not proven.

---

# Q1 GRAPH PLAN

## CLAIM

在官方实验工况所校准的热惯性模型下，给定 `78 cm/min` 与温区设定 `173/198/230/257 °C` 时，焊接中心温度沿炉程呈平滑升温—峰值—冷却响应，并在小温区 3、6、7 中点和小温区 8 末端分别达到 `129.87/170.80/190.70/225.01 °C`；该预测受限于集总热模型的校准精度，且良好拟合不等于参数可辨识。

## Evidence Contract

### Question objective

建立能够描述焊接区域中心温度变化的模型，并给出指定新工况下的完整炉温曲线及四个位置温度。

### Core result

- calibration RMSE: `1.484 °C`;
- Q1 checkpoint temperatures: `129.87`, `170.80`, `190.70`, `225.01 °C`;
- full center-temperature sequence is available at high temporal resolution and can be sampled every `0.5 s`.

### Limitation

- lumped effective thermal inertia rather than a full three-dimensional conduction model;
- cooling-transition behavior is empirically calibrated from one experiment;
- fit quality demonstrates adequacy for this operating envelope, not unique identification of physical parameters;
- extrapolation beyond official setting/speed bounds is unsupported.

### Evidence needed

1. model–experiment agreement and residual scale;
2. predicted center-temperature evolution under the specified Q1 condition;
3. spatial/temporal locations of the four requested checkpoint values.

## Candidate generation and deletion test

| Candidate | What it proves | What it cannot prove | Redundancy test |
|---|---|---|---|
| A. Measured vs calibrated response with residual | agreement over heating, peak, and cooling; residual structure/scale | identifiability; universal validity | unique validation evidence |
| B. Q1 PCB-center and furnace-air profiles with checkpoint markers | thermal lag, predicted time evolution, requested locations | global physical correctness outside calibrated envelope | unique answer evidence |
| C. Temperature vs furnace position rather than time | physical zone correspondence | adds no new values because speed is constant | same data under a linear axis transform |
| D. Separate bar chart of four checkpoint temperatures | exact comparison among four values | full evolution and thermal lag | table is clearer and already required |
| E. Parameter confidence/sensitivity plot | possible calibration robustness | identifiability without designed excitation/profile likelihood | no reliable independent-identifiability evidence exists |
| F. Every `0.5 s` sample as a plotted marker | nothing beyond the continuous curve | — | visualizes output-file density, not science |

## Forced scoring

| Candidate | Information | Uniqueness | Conclusion support | Readability | Penalty | Total | Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| A. Calibration fit + residual | 10 | 9 | 10 | 9 | -1 | 37 | MAIN |
| B. Q1 predicted PCB/air profiles | 10 | 10 | 10 | 9 | 0 | 39 | MAIN |
| C. Position-axis duplicate | 6 | 3 | 5 | 8 | -7 | 15 | DO NOT PLOT |
| D. Four-value bar chart | 5 | 4 | 6 | 9 | -6 | 18 | DO NOT PLOT |
| E. Calibration parameter sensitivity | 6 | 6 | 4 | 7 | -4 | 19 | DO NOT PLOT |
| F. Dense sampled markers | 3 | 2 | 3 | 4 | -8 | 4 | DO NOT PLOT |

The two MAIN candidates are not merged: A establishes model credibility under the official experiment; B answers the new prescribed operating condition. Combining them would force residuals, furnace air, checkpoints, and prediction into an overloaded multi-panel.

## MAIN FIGURE 1 — calibration agreement

**Purpose:** establish that the adopted effective model reproduces the official experiment across heating and cooling.

**Evidence:** measured and predicted center temperature; residuals on their own scale; RMSE/MAE in caption.

**Data:** time `(s)`, measured temperature `(°C)`, predicted temperature `(°C)`, residual `(°C)`.

**Tool:** Origin.

**Frozen Template:** `SCP_SCATTER_FIT_v20_FROZEN`, using its approved residual companion layout.

**Caption:** Model calibration at the official `70 cm/min` experiment with zone settings `175/195/235/255 °C`: measured and predicted PCB-center temperatures `(°C)` are shown against time `(s)`, with residuals plotted on their native scale. RMSE is `1.484 °C`, MAE is `1.041 °C`, and the maximum absolute residual is `4.814 °C`. The agreement supports calibration adequacy within the tested operating envelope; it does not establish parameter identifiability.

**TAKEAWAY:** The effective thermal model reproduces the official experiment closely enough for bounded process analysis, while retaining visible residual and scope limitations.

**Why main:** every later optimization depends on this calibrated response; without it the paper asks readers to trust an unvalidated thermal model.

## MAIN FIGURE 2 — prescribed-condition temperature evolution

**Purpose:** answer Q1 with the full predicted furnace response and connect it to the commanded air-temperature environment.

**Evidence:** PCB-center temperature as Primary, furnace-air profile as Neutral/Secondary, and four requested positions as Highlight markers on the PCB curve.

**Data:** time `(s)`, PCB-center temperature `(°C)`, modeled furnace-air temperature `(°C)`, four checkpoint times/temperatures.

**Tool:** Origin.

**Frozen Template:** `SCP_MULTI_LINE_COMPARISON_v11_FROZEN`; two directly labeled curves, with the PCB-center curve dominant.

**Caption:** Predicted reflow response at `78 cm/min` for zone settings `173/198/230/257 °C`. The Primary curve encodes PCB-center temperature `(°C)` and the Neutral curve encodes the modeled local furnace-air temperature `(°C)` versus time `(s)`; orange markers identify the midpoints of zones 3, 6, and 7 and the end of zone 8, where predicted center temperatures are `129.87`, `170.80`, `190.70`, and `225.01 °C`, respectively. Predictions are conditional on the calibrated lumped model.

**TAKEAWAY:** Thermal inertia smooths and delays the commanded furnace profile, producing the four required checkpoint temperatures along one continuous heating trajectory.

**Why main:** it is the direct requested result; the air profile supplies mechanism rather than a redundant second view.

## SUPPORTING

None. Exact checkpoint values and the `0.5 s` output belong in tables/data, not another figure.

## APPENDIX

None by default. A compact parameter table and residual statistics are sufficient.

## DO NOT PLOT

- position-axis duplicate of the time curve;
- bar chart of four checkpoint temperatures;
- all `0.5 s` samples as markers;
- generic parameter sensitivity presented as identifiability evidence;
- furnace geometry schematic recreated from the official statement.

---

# Q2 GRAPH PLAN

## CLAIM

在温区设定 `182/203/237/254 °C` 下，模型给出的最大可行传送带速度为 `77.871 cm/min`，因为继续增速会首先使峰值温度跌破 `240 °C`，而该速度下升降温斜率、`150–190 °C` 保温时间及高于 `217 °C` 的时间仍满足制程界限；该边界结论仅适用于校准模型与官方速度区间。

## Evidence Contract

### Question objective

在给定温区温度下确定满足全部制程界限的最大过炉速度。

### Core result

- maximum feasible speed: `77.871 cm/min`;
- peak: `240.000 °C` (active lower-bound constraint);
- max rise/min fall slope: `2.316/-1.790 °C/s`;
- `150–190 °C` rising duration: `83.195 s`;
- duration above `217 °C`: `73.332 s`.

### Limitation

- speed boundary derived from the calibrated model, not a production tolerance study;
- exact operational set point should retain a safety margin for sensor/model uncertainty;
- monotonic active-constraint behavior is established numerically within `65–100 cm/min` only.

### Evidence needed

1. the active peak-temperature constraint crossing at the limiting speed;
2. confirmation that all non-active constraints remain feasible, preferably in a table;
3. optional full temperature trajectory for process interpretation, not for locating the speed boundary.

## Candidate generation and deletion test

| Candidate | What it proves | What it cannot prove | Redundancy test |
|---|---|---|---|
| A. Peak temperature vs conveyor speed with 240–250 °C limits | why the upper speed is finite; which constraint is active | all other metrics unless caption/table reports them | unique boundary evidence |
| B. Five normalized constraint margins vs speed | simultaneous feasibility and active constraint | physical temperature evolution; robustness to model uncertainty | partly duplicates A and is harder to read |
| C. Full temperature profile at limiting speed | process trajectory and threshold durations | maximum-speed status without a speed sweep | supporting interpretation only |
| D. Feasible/infeasible speed heatmap | binary feasibility | which constraint causes failure | degrades a one-dimensional boundary into blocks |
| E. Bisection/optimizer convergence | algorithm termination | physical feasibility or globality | routine numerical trace |

## Forced scoring

| Candidate | Information | Uniqueness | Conclusion support | Readability | Penalty | Total | Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| A. Peak temperature vs speed | 10 | 9 | 10 | 9 | 0 | 38 | MAIN |
| B. Normalized margin bundle | 8 | 7 | 9 | 7 | -3 | 28 | SUPPORTING |
| C. Limiting-speed temperature profile | 8 | 7 | 8 | 9 | -2 | 30 | SUPPORTING |
| D. Binary feasibility heatmap | 5 | 4 | 6 | 7 | -5 | 17 | DO NOT PLOT |
| E. Search convergence | 3 | 3 | 3 | 7 | -7 | 9 | DO NOT PLOT |

Candidates B and C support the same feasibility message already closed by A plus a metrics table. Only C is retained as appendix material for readers who want the time-domain process; B is deleted despite scoring as supporting.

## MAIN FIGURE — active speed boundary

**Purpose:** show why `77.871 cm/min` is the maximum feasible speed.

**Evidence:** peak PCB-center temperature versus speed, the `240 °C` lower process limit, `250 °C` upper limit, and the accepted boundary point.

**Data:** conveyor speed `(cm/min)`, peak temperature `(°C)`, process-limit references.

**Tool:** Origin.

**Frozen Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN`.

**Caption:** Peak PCB-center temperature `(°C)` across conveyor speeds `65–100 cm/min` for fixed zone settings `182/203/237/254 °C`. Horizontal references denote the permitted `240–250 °C` peak range, and the orange point marks `77.871 cm/min`, where the peak equals `240.000 °C`. The remaining process metrics at this speed satisfy their limits; the boundary is conditional on the calibrated model and does not include a production uncertainty margin.

**TAKEAWAY:** Peak-temperature loss is the active mechanism that limits conveyor speed to `77.871 cm/min` in the adopted model.

**Why main:** it proves both the numerical boundary and its cause with one relationship.

## SUPPORTING

None retained after deletion review. A table of the four non-active process metrics is clearer than a normalized multi-line margin plot.

## APPENDIX — limiting-speed profile

**Purpose:** provide the full time-domain response for reproduction and threshold-duration checking.

**Evidence/Data:** time `(s)`, PCB-center temperature `(°C)`, `150/190/217/240 °C` references.

**Tool:** Origin.

**Frozen Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN`, with low-weight reference lines.

**Caption:** PCB-center temperature at the model-limited speed `77.871 cm/min`; reference temperatures define the soak, liquidus, and peak constraints. Exact interval durations are reported in the accompanying table.

**TAKEAWAY:** The limiting-speed trajectory remains feasible for slope and duration constraints while touching the lower peak-temperature bound.

## DO NOT PLOT

- normalized five-margin bundle in the final paper;
- binary speed-feasibility heatmap;
- bisection or optimizer convergence;
- a separate marker plot for each process metric.

---

# Q3 GRAPH PLAN

## CLAIM

在官方温度与速度边界构成的参数化搜索域内，模型得到一条满足全部制程界限的低面积炉温曲线，设定为 `169.94/188.12/226.82/264.98 °C`、速度 `87.378 cm/min`，其从首次超过 `217 °C` 到峰值的面积为 `420.973 °C·s`；该解位于高温区上边界附近，是限定搜索域内的高质量可行解而非已证明的全局最优。

## Evidence Contract

### Question objective

在全部制程界限内，使上升阶段超过 `217 °C` 到峰值之间的面积最小，并给出对应温区设置、速度和炉温曲线。

### Core result

- settings: `169.943/188.124/226.823/264.975 °C`;
- speed: `87.378 cm/min`;
- objective area: `420.973 °C·s`;
- peak: `240.005 °C`;
- above-217 duration: `56.971 s`;
- soak duration: `61.723 s`;
- max rise/min fall slope: `2.156/-1.855 °C/s`.

### Limitation

- high-temperature set point approaches its `265 °C` search bound;
- solution is conditional on a five-variable parameterized family and numerical search;
- a contour/local slice cannot prove global optimality;
- manufacturing tolerance and model uncertainty are not optimized.

### Evidence needed

1. selected temperature curve, `217 °C` threshold, peak, and objective-area region;
2. all process metrics/limits, preferably table-based;
3. local landscape/boundary context showing why the accepted solution should not be narrated as an unconstrained global optimum.

## Candidate generation and deletion test

| Candidate | What it proves | What it cannot prove | Redundancy test |
|---|---|---|---|
| A. Optimal temperature curve with objective-area fill | exact process response, objective definition, threshold/peak feasibility | global optimality | indispensable direct answer |
| B. `T8–9 × speed` local area contour with other variables fixed | boundary direction, local curvature, accepted point | full five-dimensional/global optimum | unique limitation/context evidence |
| C. All five one-factor slices | local sensitivity | parameter interaction and globality | too many panels; overlaps contour/table |
| D. Optimization convergence | numerical search progress | global optimum | routine and algorithm-dependent |
| E. 3D surface of the same local slice | perspective height | more than contour | redundant and less quantitative |
| F. Bar chart of selected settings | exact settings | objective or feasibility | table is clearer |

## Forced scoring

| Candidate | Information | Uniqueness | Conclusion support | Readability | Penalty | Total | Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| A. Selected curve + area | 10 | 10 | 10 | 9 | 0 | 39 | MAIN |
| B. Local area contour | 9 | 8 | 8 | 9 | -2 | 32 | MAIN by score, demoted to SUPPORTING after redundancy/scope test |
| C. Five local slices | 7 | 5 | 6 | 6 | -6 | 18 | DO NOT PLOT |
| D. Optimization convergence | 4 | 4 | 3 | 7 | -6 | 12 | DO NOT PLOT |
| E. 3D duplicate surface | 6 | 3 | 5 | 6 | -7 | 13 | DO NOT PLOT |
| F. Setting bars | 5 | 4 | 6 | 8 | -6 | 17 | DO NOT PLOT |

Candidate B exceeds 32 but does not enter the main narrative: it is a two-dimensional conditional slice of a five-variable problem and cannot carry the main optimality claim. This is an explicit non-mechanical override.

## MAIN FIGURE — selected low-area profile

**Purpose:** encode the objective itself and verify the accepted thermal trajectory.

**Evidence:** temperature curve; `217 °C` reference; upward crossing, peak, and shaded integral region; `240 °C` lower peak reference; key process metrics in caption/table.

**Data:** time `(s)`, PCB-center temperature `(°C)`, threshold-crossing time, peak time/temperature, objective area `(°C·s)`.

**Tool:** Origin.

**Frozen Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN`; the objective region is a data-bound low-opacity fill under the same graph without modifying the template.

**Caption:** Selected low-area furnace profile within the official setting and speed bounds. PCB-center temperature `(°C)` is plotted against time `(s)` for settings `169.94/188.12/226.82/264.98 °C` and speed `87.378 cm/min`; the gray reference marks `217 °C`, the orange point marks the `240.005 °C` peak, and the lightly filled region from the upward `217 °C` crossing to the peak equals `420.973 °C·s`. All process limits are satisfied in the adopted model. The result is a high-quality feasible solution within the parameterized search space; global optimality is not proven.

**TAKEAWAY:** The accepted bounded-search solution minimizes the targeted pre-peak liquidus excess while operating close to the minimum peak and soak constraints.

**Why main:** it shows exactly what was minimized and whether the selected curve remains physically/process feasible.

## SUPPORTING — local boundary landscape

**Purpose:** disclose local curvature and the upper-bound tendency of `T8–9`.

**Evidence/Data:** local grid of `T8–9 (°C)`, speed `(cm/min)`, feasible objective area `(°C·s)`, infeasible cells masked/outlined, accepted point.

**Tool:** Origin.

**Frozen Template:** `SCP_CONTOUR_MAIN_v11_FROZEN`.

**Caption:** Local `T8–9 × speed` slice of the Q3 objective with the other three settings fixed at the accepted values. Color encodes the pre-peak excess area `(°C·s)` only where all process limits are satisfied; the orange point marks the accepted design near the upper `T8–9` bound. This conditional slice characterizes local behavior and does not prove a five-dimensional global optimum.

**TAKEAWAY:** The accepted solution is locally driven toward the high-temperature setting boundary, reinforcing the need for bounded-search language.

## APPENDIX

Numerical search repeatability across several fixed seeds may be tabulated. A figure is warranted only if materially different basins appear.

## DO NOT PLOT

- routine best-value convergence;
- 3D version of the local contour;
- five one-factor sensitivity panels;
- bar chart of the optimized settings;
- every feasible candidate as an unstructured scatter cloud.

---

# Q4 GRAPH PLAN

## CLAIM

在保持 Q3 面积不超过 `105%` 且满足全部制程界限的条件下，`167.10/185.37/225.14/264.90 °C` 与 `85.426 cm/min` 的方案把峰值两侧不对称指标从 Q3 的 `1.674 °C` 降至 `1.621 °C`，面积仅由 `420.973` 增至 `423.971 °C·s`；该方案是所定义折中规则和参数化搜索域内的高质量可行解，权重/面积上限改变时选择可能变化。

## Evidence Contract

### Question objective

结合 Q3 的低面积要求，使峰值两侧超过 `217 °C` 的曲线尽量对称，并给出方案、曲线和指标。

### Core result

- settings: `167.098/185.374/225.140/264.901 °C`;
- speed: `85.426 cm/min`;
- area: `423.971 °C·s`, below cap `442.021 °C·s`;
- asymmetry: `1.621 °C`, versus Q3 `1.674 °C`;
- peak: `240.021 °C`; all process constraints feasible.

### Limitation

- Q4 requires an explicit compromise definition; here asymmetry is minimized under an area cap of 105% of the Q3 minimum;
- improvement is modest and model-dependent;
- the selected point is not a proven global optimum;
- different compromise rules can yield different designs.

### Evidence needed

1. the feasible area–asymmetry trade-off and accepted Q3/Q4 positions;
2. direct comparison of left/right above-217 branches around the peak;
3. table of selected settings and process metrics.

## Candidate generation and deletion test

| Candidate | What it proves | What it cannot prove | Redundancy test |
|---|---|---|---|
| A. Feasible area–asymmetry frontier | compromise structure and accepted Q4 position | global optimum outside sampled/optimized family | unique decision evidence |
| B. Peak-centered mirrored branches for Q3 and Q4 | actual symmetry change in curve shape | why the area cap was chosen | unique physical evidence |
| C. Q3/Q4 full time curves | overall similarity | symmetry as directly as mirrored branches | weaker view of the same data |
| D. Parameter bars for Q3/Q4 | setting differences | thermal consequence | table clearer |
| E. Q4 convergence | algorithm progress | global optimum or trade-off validity | routine trace |
| F. 3D area–asymmetry–speed display | an extra dimension | more defensible compromise evidence | occlusion/perspective and unnecessary |

## Forced scoring

| Candidate | Information | Uniqueness | Conclusion support | Readability | Penalty | Total | Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| A. Area–asymmetry frontier | 10 | 10 | 10 | 9 | 0 | 39 | MAIN |
| B. Mirrored branch comparison | 9 | 9 | 10 | 9 | -1 | 36 | MAIN |
| C. Full Q3/Q4 time curves | 7 | 5 | 7 | 9 | -5 | 23 | APPENDIX by score, then DO NOT PLOT as duplicate |
| D. Setting bars | 5 | 4 | 5 | 8 | -6 | 16 | DO NOT PLOT |
| E. Convergence | 4 | 4 | 3 | 7 | -6 | 12 | DO NOT PLOT |
| F. 3D trade-off | 6 | 5 | 6 | 5 | -7 | 15 | DO NOT PLOT |

A and B are combined into one two-panel MAIN figure because they jointly answer one conclusion: **why the compromise was selected and whether the resulting curve is more symmetric**. Neither panel is retained merely because Multi-panel exists.

## MAIN FIGURE — symmetry/area compromise

**Purpose:** connect the decision trade-off to the actual thermal-shape improvement.

**Evidence:** panel (a) feasible Pareto envelope of objective area and asymmetry, with Q3/Q4 points and 105% area cap; panel (b) mirrored rising/falling branches above `217 °C`, centered at the peak, comparing Q3 and Q4.

**Data:** feasible design area `(°C·s)`, asymmetry `(°C)`, Q3/Q4 points; relative time from peak `(s)`, mirrored branch temperature `(°C)`.

**Tool:** Origin.

**Frozen Template:** frozen Multi-panel; panel (a) uses Single-line/scatter semantics for the ordered Pareto envelope, panel (b) uses restrained Multi-line direct labels. No template change.

**Caption:** Area–symmetry compromise within the adopted five-variable search space. (a) Feasible pre-peak excess area `(°C·s)` versus above-217 asymmetry `(°C)`; the Q3 point minimizes area, the vertical reference is the `105%` area cap (`442.021 °C·s`), and the orange Q4 point minimizes the adopted asymmetry metric under that cap. (b) Heating and cooling branches above `217 °C`, mirrored about each profile's peak time, for Q3 and Q4. Q4 reduces asymmetry from `1.674` to `1.621 °C` while area increases from `420.973` to `423.971 °C·s`. These are high-quality feasible solutions under the stated compromise rule; global optimality is not proven.

**TAKEAWAY:** A small sacrifice in Q3 area produces a measurable but modest improvement in peak-centered symmetry under the explicit 105% area rule.

**Why main:** the trade-off panel alone is abstract, while the mirrored-profile panel alone cannot justify the selection rule; together they close one decision claim.

## SUPPORTING

None. The main two-panel figure and metric table contain the required evidence.

## APPENDIX

Alternative area-cap choices may be tabulated if decision sensitivity is discussed. No default figure.

## DO NOT PLOT

- full unaligned Q3/Q4 time curves;
- parameter-setting bars;
- routine convergence;
- 3D trade-off surface;
- a four-panel dashboard of unrelated Q4 metrics.

---

# Cross-question deletion summary

The independent plan keeps **five MAIN figure units**:

1. calibration fit + residual;
2. Q1 prescribed-condition thermal response;
3. Q2 active speed boundary;
4. Q3 selected curve and objective area;
5. Q4 area–symmetry compromise.

It retains **one supporting figure plan** (Q3 local contour) and **one appendix figure plan** (Q2 limiting-speed profile). Exact settings, checkpoint temperatures, constraint metrics, and search-repeat values remain tables.

No event/work interval or interval-union grammar is naturally required. Therefore:

`SECOND_INDEPENDENT_USE_CASE_FOUND = NO`

No `TEMPLATE_ADAPTATION_REQUIRED` condition is present in the frozen main plan. The Q3 data-bound objective fill and Q4 panel combination are figure content, not changes to a frozen template.

