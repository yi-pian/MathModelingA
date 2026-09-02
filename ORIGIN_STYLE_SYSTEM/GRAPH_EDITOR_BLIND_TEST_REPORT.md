# GRAPH EDITOR BLIND TEST REPORT

## Final verdict

`BLIND_TEST_PROBLEM = 2020 CUMCM A — Reflow Oven Temperature Profile (炉温曲线)`

**GRAPH EDITOR BLIND TEST — PASS**

The test remained isolated through the claim/evidence, candidate scoring, deletion, hierarchy, tool, template, caption, and storyboard decisions. External graph practices were consulted only after the blind plan and reverse audit were frozen. Five non-redundant MAIN figure units were produced in Origin; supporting and appendix candidates remained plans only.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Isolation valid | PASS | `BLIND_TEST_ISOLATION.md` records allowed/prohibited sources and the absence of a prior 2020A graph package in scope. |
| Independent graph plan | PASS | `BLIND_GRAPH_EDITOR_ANALYSIS.md` contains Q1–Q4 claims, evidence contracts, candidate scores, deletions, hierarchy, tools, templates, captions, and takeaways. |
| Storyboard frozen before plotting | PASS | `BLIND_FIGURE_STORYBOARD.md` fixes five MAIN units, one supporting plan, and one appendix plan. |
| Reverse audit | PASS | `BLIND_EDITOR_AUDIT.md` found no missing MAIN evidence, redundant MAIN unit, tool misuse, 3D/convergence inertia, identifiability overclaim, or global-optimum overclaim. |
| External cross-check | PASS | `EXTERNAL_GRAPH_CROSS_CHECK.md` found agreement with the dominant evidence chain and no major missing MAIN conclusion. |
| Numerical evidence integrity | PASS after correction | `BLIND_NUMERICAL_VERIFICATION.md` records a post-plan high-resolution feasibility audit and correction before plotting. Graph choices were unchanged. |
| Actual MAIN production | PASS | Five Origin figure units, each in PNG/PDF/SVG, plus the OPJU project are under `outputs/graph_editor_blind_test/`. |
| Frozen-template integrity | PASS | Frozen templates were instantiated/read only; no template was saved, overwritten, or added. |
| Hard-fail screen | PASS | No hard-fail condition occurred. |

## Final figure architecture

### MAIN-1 — Model calibration and residual structure

- **Claim served:** the effective thermal model reproduces the official experiment closely enough for bounded process prediction, but the fit does not prove parameter identifiability.
- **Tool / template:** Origin / `SCP_SCATTER_FIT_v20_FROZEN`, with a compact residual companion.
- **Why MAIN:** all later predictions depend on model–data agreement; residuals prevent a visually coincident fit from carrying more meaning than it can support.
- **Final caption:** Measured PCB-center temperature (gray markers) and the calibrated effective thermal model (navy line) for zone settings `175, 195, 235, 255°C` at `70 cm/min`; the lower panel reports predicted-minus-measured residuals relative to the zero reference. The fit has RMSE `1.484°C`, MAE `1.041°C`, and maximum absolute residual `4.814°C`. This supports calibration adequacy within the adopted model, not parameter identifiability.
- **TAKEAWAY:** the model captures the experiment with small, structured residuals and is adequate for conditional process calculations.

### MAIN-2 — Prescribed thermal response

- **Claim served:** PCB thermal inertia smooths and delays the local furnace-air forcing while producing the four required checkpoint temperatures.
- **Tool / template:** Origin / `SCP_MULTI_LINE_COMPARISON_v11_FROZEN`.
- **Why MAIN:** it connects the oven setting, physical lag, and the four numerical answers requested in Question 1 in one non-redundant graph.
- **Final caption:** Local furnace-air temperature (gray dashed) and predicted PCB-center temperature (navy) for settings `173, 198, 230, 257°C` at `78 cm/min`. Orange markers identify the requested temperatures at the zone-3 midpoint (`129.9°C`), zone-6 midpoint (`170.8°C`), zone-7 midpoint (`190.7°C`), and zone-8 end (`225.0°C`). The forcing profile is displayed as model input; it is not a second measured response.
- **TAKEAWAY:** thermal inertia explains the smoother, delayed PCB response and fixes all four prescribed-location predictions.

### MAIN-3 — Maximum-speed active constraint

- **Claim served:** the maximum feasible speed occurs where peak temperature touches the `240°C` lower bound.
- **Tool / template:** Origin / `SCP_SINGLE_LINE_MAIN_v11_FROZEN`.
- **Why MAIN:** it exposes the active throughput-limiting mechanism more directly than a crowded plot of every constraint metric.
- **Final caption:** Predicted peak PCB temperature versus conveyor speed for fixed settings `182, 203, 237, 254°C`. Gray reference lines mark the accepted `240–250°C` peak interval; the orange point is the maximum feasible speed, `77.871 cm/min`, where the lower peak limit becomes active. Heating/cooling slopes and duration constraints were checked numerically but are omitted from the graph to avoid redundant series. The result is conditional on the calibrated model and one-dimensional speed search.
- **TAKEAWAY:** peak temperature, rather than another process metric, limits throughput at `77.871 cm/min`.

### MAIN-4 — Low-area process design

- **Claim served:** a strictly feasible bounded-search design reduces the pre-peak liquidus-excess area.
- **Tool / template:** Origin / `SCP_SINGLE_LINE_MAIN_v11_FROZEN`; the pale-orange fill is data-bound figure content and does not modify the template.
- **Why MAIN:** the curve simultaneously verifies the selected physical response, the `217°C` threshold, the peak, and the exact Q3 objective region.
- **Final caption:** Predicted PCB-center temperature for the selected Q3 setting `[172.118, 189.123, 229.005, 265.000]°C` at `88.918 cm/min`. The gray line is the `217°C` liquidus threshold; pale orange encodes the integral of temperature excess from the upward crossing to the peak, `419.599°C·s`; the orange marker identifies the peak (`240.004°C`). All adopted process inequalities pass at `dt = 0.05 s`. This is the best strictly verified design found in the adopted parameterized search, not a proof of global optimality.
- **TAKEAWAY:** the selected feasible profile attains a pre-peak excess area of `419.599°C·s` without hiding the threshold or peak constraint.

### MAIN-5 — Symmetry compromise

- **Claim served:** under a small area allowance, the Q4 design improves peak-centered symmetry while remaining close to the Q3 area minimum.
- **Tool / template:** Origin / frozen Multi-panel grammar; panel (a) uses frozen scatter/single-line semantics and panel (b) frozen restrained multi-line semantics. The two-panel composition is data content, not a template change.
- **Why MAIN:** panel (a) explains why the compromise is selected; panel (b) verifies what improved symmetry means in the physical time profile. Neither panel answers the full claim alone.
- **Final caption:** (a) Decision-relevant subset of `853` strictly verified feasible designs in pre-peak excess area–asymmetry space. The navy polyline connects the four nondominated sampled points and is not asserted to be a continuous or global Pareto frontier; the square marks the Q3 area-minimum selection and the orange circle the Q4 selection. (b) Heating (solid) and cooling (dashed) branches mirrored about each design's peak over their common above-`217°C` time span. Under the corrected area cap `440.579°C·s`, Q4 uses `422.621°C·s` and reduces the asymmetry metric from Q3's `1.725°C` to `1.604°C`. The comparison is conditional on the adopted metric, 105% cap, parameterized family, and deterministic search sample.
- **TAKEAWAY:** Q4 provides a modest, verified symmetry improvement for a small area cost; no global Pareto claim is made.

## Supporting and appendix discipline

- **Supporting S1, not rendered:** local `T8–9 × speed` Q3 contour with all other variables fixed. It could explain local boundary pressure but cannot prove global optimality.
- **Appendix A1, not rendered:** full limiting-speed Q2 time profile for a reproducibility audit of slopes and duration metrics.
- **Deleted:** optimizer convergence, 3D surface, settings bars, checkpoint bars, duplicated time/position profiles, dense constraint-spaghetti plot, and routine sensitivity panels. Their information was redundant, table-suited, or unable to support a distinct MAIN takeaway.
- **Interval decision:** `SECOND_INDEPENDENT_USE_CASE_FOUND = NO`. No event-interval/interval-union figure was manufactured.
- **Template decision:** `TEMPLATE_ADAPTATION_REQUIRED = NO` for the retained MAIN evidence. Data-dependent fills, thresholds, highlights, labels, and the two-panel composition are annotations/content rather than changes to frozen visual semantics.

## Post-plan numerical correction

The graph-preparation stress test correctly exposed that the initial heuristic Q3/Q4 selections were mildly dominated. A deterministic high-resolution audit retained `853` feasible candidates and promoted better selections before plotting:

| Metric | Initial | Final verified |
|---|---:|---:|
| Q3 area (°C·s) | 420.973 | 419.599 |
| Q4 area (°C·s) | 423.971 | 422.621 |
| Q4 asymmetry (°C) | 1.621 | 1.604 |

This correction did not alter any Claim → Evidence → Figure decision. The original blind-analysis files remain unchanged; `BLIND_NUMERICAL_VERIFICATION.md` is the explicit supersession record. Catching the issue before plotting is treated as scientific QA, not as a reason to hide or inflate the result.

## Actual-figure QA

| Check | Result | Notes |
|---|---|---|
| Scientific accuracy | PASS | plotted values were read from the final verified CSV package; Q3/Q4 corrections were propagated to curves, captions, and annotations |
| Style consistency | PASS | white background, navy Primary, orange Highlight, muted auxiliary colors, restrained direct labels, and no grid/shadow/rainbow/3D |
| Final insertion readability | PASS | all figures were re-rendered and inspected at a `1040 px` bounded preview; core values, units, panel tags, thresholds, and direct labels remain legible |
| Label collisions | PASS | Q1 checkpoints, Q2 limit/selection, Q3 area/threshold, and Q4 panel labels were individually repositioned after visual inspection |
| Units | PASS | seconds, °C, cm/min, and °C·s are explicit where encoded |
| Caption consistency | PASS | every number and condition matches `results/summary.csv` and the final graph data |
| Exaggeration | PASS | Q4 shows a sampled feasible cloud and four sampled nondominated points, not a falsely smoothed global frontier |
| Limitation visibility | PASS | calibration, bounded search, parameterized family, cap, and lack of global proof are stated in captions/takeaways |
| Frozen files | PASS | exports reside only in the blind-test output directory; no `.otpu` was created or overwritten |

## Output manifest

Directory: `outputs/graph_editor_blind_test/`

- `MAIN1_MODEL_CALIBRATION.{png,pdf,svg}`
- `MAIN2_Q1_THERMAL_RESPONSE.{png,pdf,svg}`
- `MAIN3_Q2_MAXIMUM_SPEED.{png,pdf,svg}`
- `MAIN4_Q3_LOW_AREA_DESIGN.{png,pdf,svg}`
- `MAIN5_Q4_SYMMETRY_COMPROMISE.{png,pdf,svg}`
- `ORIGIN_GRAPH_EDITOR_BLIND_TEST.opju`

All PNG headers, PDF headers, and SVG roots were verified. The Origin MCP execution log is `training_data/blind_test_mcp_execution.json`.

## Score

| Dimension | Score | Rationale |
|---|---:|---|
| Conclusion understanding | 19/20 | all four questions were reduced to exact claim sentences and active limitations; one point retained because the numerical result package required later correction |
| Evidence selection | 19/20 | each MAIN unit supplies distinct necessary evidence; broader robustness remains a defensible supporting extension |
| Redundancy control | 15/15 | routine convergence, 3D, duplicate curves, bars, and all-metric clutter were deleted |
| Main/support/appendix hierarchy | 10/10 | five MAIN units, one supporting plan, one appendix plan, with explicit zero-figure permission respected |
| Python–Origin decision | 10/10 | all retained evidence is analytical and was produced in Origin; Python was limited to numerical preparation/MCP orchestration |
| Template matching | 9/10 | frozen visual semantics matched every MAIN unit; one point retained for data-dependent two-panel assembly rather than a mechanically reusable one-shot template |
| Caption/Takeaway quality | 9/10 | captions encode conditions, quantities, units, references, and limits without overclaim; one point retained for the unavoidable density of the Q4 compound caption |
| Limitation honesty | 5/5 | fit is not identifiability; sampled frontier is not global; search/cap/model conditions remain explicit |
| **TOTAL** | **96/100** | **PASS threshold met** |

## Hard-fail screen

All ten hard-fail conditions are **false**:

1. no critical conclusion lacks necessary visual evidence;
2. no large set of meaningless figures entered the main text;
3. convergence is not used as global-optimum evidence;
4. no 3D surface replaces a clearer contour or analytical plot;
5. tool choice does not distort physical geometry;
6. scientific meaning was not altered for template reuse;
7. captions do not claim more than the figures show;
8. fit/residual is not used as identifiability proof;
9. conditional numerical results remain conditional;
10. no existing or external graph plan was read before the blind decisions were frozen.

## System status

`GRAPH_EDITOR_PLAYBOOK_STATUS = HUMAN REVIEW PASSED / BLIND TEST PASSED / CONTEST READY`

`ORIGIN_STYLE_SYSTEM_STATUS = CONTEST READY — STYLE + GRAPH EDITOR COMPLETE`

**GRAPH EDITOR BLIND TEST — PASS**
