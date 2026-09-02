# BLIND EDITOR REVERSE AUDIT

Problem: `2020 CUMCM A — Reflow Oven Temperature Profile`  
Audit timing: after the independent Graph Plan and Storyboard were frozen; before external cross-check and before plotting.

## 1. Missing-evidence audit

| Claim | Required visual evidence | Present? | Verdict |
|---|---|---:|---|
| calibrated model is adequate for bounded prediction | measured/predicted agreement and residual scale | yes, Figure 1 | PASS |
| Q1 specified response and checkpoints | continuous PCB profile, furnace forcing, checkpoint locations | yes, Figure 2 | PASS |
| Q2 maximum speed is set by peak lower bound | peak-vs-speed boundary with 240 °C reference | yes, Figure 3 | PASS |
| Q3 accepted design minimizes the stated area within the search | curve, threshold, filled objective region, feasible metrics | yes, Figure 4 + table | PASS with bounded-search limitation |
| Q4 improves symmetry under an area cap | area–asymmetry trade-off and mirrored branch comparison | yes, Figure 5 | PASS with compromise-rule limitation |

No critical conclusion is left without necessary visual evidence.

## 2. Redundancy audit

### Potential duplication: calibration curve vs Q1 predicted curve

They use the same response variable but answer different reviewer questions:

- Figure 1: “Does the model reproduce the official experiment?”
- Figure 2: “What does the model predict under the requested new condition, and why does it lag the furnace air?”

Covering either figure weakens a different evidence link. **Retain both.**

### Potential duplication: Q2 peak-speed curve vs limiting-speed temperature profile

The peak-speed curve establishes the decision boundary; the temperature profile only reproduces process timing. The latter is therefore correctly demoted to appendix. **No duplication in the main text.**

### Potential duplication: Q3 curve vs Q3 local contour

The curve defines and verifies the objective; the contour reveals local boundary behavior. Because the contour is a conditional two-dimensional slice of a five-variable search, its main-text score was overridden and it remains supporting. **Hierarchy is correct.**

### Potential duplication: Q4 Pareto panel vs mirrored branches

The Pareto panel answers “why this compromise”; the mirrored branches answer “what symmetry improvement occurs.” They share one claim and justify a single multi-panel unit. **Combination is valid.**

## 3. Table-better-than-figure audit

Correctly assigned to tables:

- four Q1 checkpoint temperatures;
- all Q2 non-active process metrics;
- Q3/Q4 exact zone settings and speed;
- Q3/Q4 complete process-limit checklist;
- seed/repeat summaries unless materially different basins emerge.

Correctly rejected as figures:

- parameter-setting bars;
- checkpoint bars;
- dense `0.5 s` marker plot;
- binary feasibility heatmap.

## 4. Multi-panel audit

- No multi-panel is used merely because variables are numerous.
- Q4 is the only substantive multi-panel decision; both panels jointly support one conclusion.
- Calibration fit/residual uses the approved residual companion because residual scale is inseparable from model-agreement assessment.
- Three otherwise deletable plots have not been hidden inside a multi-panel.

Verdict: **PASS**.

## 5. 3D audit

No 3D Surface or spatial 3D figure is selected. All available relationships are one-dimensional or two-dimensional analytical responses, and contour/line representations are more accurate.

Verdict: **PASS**.

## 6. Convergence audit

No routine convergence trace enters MAIN, SUPPORTING, or default APPENDIX. Search-repeat information is table-only unless it exposes multiple basins or instability.

Verdict: **PASS**.

## 7. Fit versus identifiability audit

The calibration caption and takeaway say only:

- model–data agreement;
- calibration adequacy within the tested envelope.

They explicitly state that fit/residual/RMSE do not establish parameter identifiability. No confidence or sensitivity figure is used as a substitute for identifiability analysis.

Verdict: **PASS**.

## 8. Global-optimum audit

- Q3 is called a high-quality feasible solution within the adopted model/search space.
- The local contour is explicitly prohibited from proving five-dimensional global optimality.
- Q4 is conditional on a 105% Q3-area cap and the adopted asymmetry metric.
- No convergence, contour, slice, or Pareto sample is described as proof of global optimality.

Verdict: **PASS**.

## 9. Python/Origin audit

All retained figures are analytical curves, residuals, a regular contour, or an analytical multi-panel. Origin is therefore appropriate. No exact spatial geometry, collision, irregular layout, or real three-dimensional relation exists that would require Python.

Python is used only for text/CSV numerical computation, not figure production.

Verdict: **PASS**.

## 10. Frozen-template audit

- Scatter + Fit: calibration agreement/residual.
- Multi-line: Q1 furnace-air vs PCB response.
- Single line: Q2 boundary and Q3 profile.
- Contour: Q3 conditional local landscape.
- Multi-panel: Q4 complementary trade-off/shape evidence.

No scientific meaning is altered to fit a template. Data-bound reference lines, markers, and Q3 objective fill are content annotations within existing grammar. No frozen asset is edited.

Verdict: **PASS**.

## 11. Caption audit

Each main caption includes:

- operating condition/comparison;
- encoded quantities and units;
- highlight/reference meaning;
- numerical result;
- limitation where needed.

No caption uses fit as identifiability evidence or claims a global optimum.

Verdict: **PASS**.

## 12. Hard-fail pre-check

| Hard-fail condition | Present? |
|---|---:|
| critical conclusion lacks evidence | no |
| meaningless main figures | no |
| routine convergence used as global proof | no |
| 3D replaces clearer contour | no |
| tool choice distorts geometry | no |
| template changes scientific meaning | no |
| caption overclaims evidence | no |
| fit treated as identifiability | no |
| conditional result presented as unconditional global result | no |
| prohibited material viewed before plan freeze | no |

## 13. Audit adjustments

No change is made to the frozen independent Graph Plan. One production risk is recorded:

- Figure 5 requires a sufficiently sampled feasible area–asymmetry envelope. If the computed envelope is too sparse or unstable, the panel must be marked `DATA_EVIDENCE_INSUFFICIENT` rather than cosmetically connected into a false smooth frontier. This is a data-integrity gate, not a selection change.

## 14. Reverse-audit verdict

`INDEPENDENT EDITOR AUDIT = PASS`

The plan is ready for external cross-check without reopening its original decisions.

