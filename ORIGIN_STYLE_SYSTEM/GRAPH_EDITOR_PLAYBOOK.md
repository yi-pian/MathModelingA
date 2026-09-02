# GRAPH EDITOR PLAYBOOK

Status: **HUMAN REVIEW PASSED / BLIND TEST PASSED / CONTEST READY**

This playbook governs graph selection before any Origin/Python production begins. It does not modify Signature Scientific Style v1.1 or any frozen template.

## 1. Start from the conclusion

Write one sentence in this form:

> Under **condition**, the model shows **result**, because **evidence**, with **limitation**.

If the intended figure cannot be mapped to one part of that sentence, it is probably decorative, redundant, or premature.

## 2. Build an evidence contract

For each question, record:

1. **Objective:** what the question asks, not what the solver computes.
2. **Core result:** the exact number, design, event, comparison, or mechanism.
3. **Evidence needed:** fit, threshold, trade-off, spatial structure, timing, robustness, or convergence.
4. **Candidate figures:** include “table only” and “do not plot” as real options.
5. **Final takeaway:** one sentence the reader should retain after five seconds.

## 3. Score before styling

Score every candidate:

| Dimension | Question |
|---|---|
| Information `/10` | How much decision-relevant content is visible? |
| Uniqueness `/10` | Is this evidence unavailable elsewhere? |
| Conclusion support `/10` | Does it directly support the stated result? |
| Readability `/10` | Can the relationship be read at publication size? |
| Redundancy penalty `-10…0` | How strongly does it duplicate another figure/table? |

`Total = four positive dimensions + penalty`

| Total | Action |
|---:|---|
| 32–40 | Main Figure |
| 26–31 | Supporting Figure |
| 20–25 | Appendix Figure |
| <20 | Do Not Plot |

The threshold is a filter, not a quota. If two high-scoring candidates support the same sentence, combine them or keep the stronger one.

## 4. Choose the scientific grammar

| Evidence question | Preferred grammar | Default tool/template |
|---|---|---|
| Does a model fit observations? | scatter + fit + residual | Origin / frozen Scatter + Fit |
| Where is a scalar optimum or threshold? | single line + one highlight/reference | Origin / frozen Single line |
| Which scenario dominates? | direct-labeled multi-line | Origin / frozen Multi-line |
| Which parameter matters? | signed sensitivity with zero reference | Origin / frozen Sensitivity |
| How do two parameters shape an objective? | contour | Origin / frozen Contour |
| How does a dense regular field vary? | heatmap, optional restrained contours | Origin / frozen Heatmap |
| Is an optimizer stable across runs/methods? | best/mean or comparative convergence | Origin / frozen Convergence |
| Do complementary panels close one claim? | compact multi-panel | Origin / frozen Multi-panel |
| Where are objects, paths, contacts, or occlusions? | equal-aspect geometry/projections | Python |
| Do curvature/multimodality/saddle/local basins require height? | 2.5D surface, auxiliary only | Origin / frozen 3D Surface Auxiliary |
| How do event windows overlap or form a union? | horizontal interval-union chart | `TEMPLATE_ADAPTATION_REQUIRED` |

## 5. Main-text hierarchy

### Main Figure

Use for the result, mechanism, feasibility boundary, or decisive comparison. A main figure must survive the question: “If this were removed, would a skeptical reader lose essential evidence?”

### Supporting Figure

Use for robustness, a secondary mechanism, local slices, or an assumption audit. It qualifies the conclusion without becoming the conclusion.

### Appendix Figure

Use for reproduction, dense diagnostics, specialist state-space views, selected numerical checks, or an alternative view that does not change the answer.

### Do Not Plot

Use when a table is clearer, the evidence duplicates another figure, the visual is algorithm-dependent, or it adds software spectacle rather than scientific information.

## 6. Mandatory deletion tests

Delete or demote a candidate when any of the following is true:

- It repeats the same curves in separate model/scenario figures.
- It is a 3D version of an already-readable contour.
- It shows a single optimizer’s routine convergence without stability/comparison evidence.
- It plots raw states when a derived signed margin or union interval is the sufficient statistic.
- It presents many adjacent geometry snapshots after the critical event is already identified.
- It repeats a coordinate system merely because a later question exists.
- Its caption can only say “results are shown” rather than a scientific conclusion.

## 7. Complementary-pair rule

Two visuals may coexist when they answer different parts of the evidence chain:

| Visual A | Visual B | Valid joint question |
|---|---|---|
| collision geometry | signed clearance vs time | who/where + when |
| design trade-off | final safety response | why selected + whether feasible |
| objective contour | component decomposition | where optimum + what mechanism dominates |
| spatial layout | efficiency map | where devices are + why performance varies |
| assignment matrix | interval union | who serves whom + what coverage results |

Combine them in a multi-panel only when they share one takeaway and remain readable at final insertion size.

## 8. Caption contract

A caption must contain:

1. the comparison or condition;
2. the encoded quantities and units;
3. the meaning of highlights/reference lines;
4. the conclusion or limitation.

Avoid “Plot of…”, “The figure above…”, unsupported superlatives, and claims of global optimality based only on convergence.

Caption test:

> Can a reader understand the result without searching the body text for what orange, zero, or the shaded interval means?

## 9. Tool boundary

Use **Python** for exact spatial geometry: equal aspect, polygons, collisions, occlusion volumes, trajectories, irregular layouts, and genuine 3D scenes.

Use **Origin** for analytical plots: lines, fits, residuals, sensitivity, contour, regular heatmaps, convergence comparisons, and conventional aligned panels.

Do not choose a tool to maximize template reuse. Choose it to preserve the scientific coordinate system and data grammar.

## 10. Template adaptation rule

Declare `TEMPLATE_ADAPTATION_REQUIRED` only when real data cannot be expressed truthfully by a frozen grammar. The adaptation request must state:

- missing semantic element;
- why annotation alone is insufficient;
- what remains frozen (font, palette, hierarchy, axes, whitespace);
- the smallest new behavior required;
- stress cases to test.

Phase 3 discovered one justified gap: **event interval / interval-union charts**. Required semantics are start/end, overlap/gap, union, row identity, and marginal contribution. This should become a separate training class; it must not silently mutate the frozen Single-line template.

## 11. Figure-count budget

For a typical five-question A-paper:

- target **5–7 main editorial figure units**;
- allow **3–6 supporting/appendix figures** when they add mechanism, robustness, or reproducibility;
- aim for **1 main figure per question on average**, not by rule;
- allow 2–3 only for geometry/event questions whose evidence modes are genuinely complementary;
- allow zero when a table answers the question better.

## 12. Final pre-production gate

Before drawing, confirm all answers are “yes”:

- Is the core conclusion numerically fixed?
- Does every planned main figure have a one-sentence takeaway?
- Have redundant candidates been scored and deleted?
- Are exact values assigned to tables rather than overloaded into the figure?
- Is the Python/Origin choice scientifically justified?
- Does the selected frozen template match the data grammar?
- Are limitations visible in the plan/caption?
- If adaptation is required, is it isolated from frozen templates?

Only after this gate should the plotting workflow begin.
