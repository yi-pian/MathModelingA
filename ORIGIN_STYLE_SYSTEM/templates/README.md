# Origin graph templates

Origin MCP stores reusable user templates in its verified user-template library rather than this repository directory:

`C:\Users\YiPian\.origin-mcp\templates`

Round-one candidate templates saved on 2026-08-30:

| Template | Purpose | Source graph | Intended structure | Score | Status |
|---|---|---|---|---:|---|
| `SCP_SINGLE_LINE_MAIN_v01.otpu` | MAIN | Graph1 | common X + one Y + optional highlighted point | 94 | candidate; human pending |
| `SCP_MULTI_LINE_COMPARISON_v01.otpu` | COMPARISON | Graph2 | common X + four comparable Y series | 92 | candidate; human pending |
| `SCP_SENSITIVITY_ANALYTICAL_v01.otpu` | ANALYTICAL | Graph3 | perturbation X + four response series | 92 | candidate; human pending |
| `SCP_CONTOUR_MAIN_v01.otpu` | MAIN | Graph4 | regular matrix Z + optimum XY overlay | 90 | candidate; human pending |

All four `.otpu` files, JSON metadata files, and PNG thumbnails were verified as non-empty. The templates are deliberately tagged `round1` and `candidate`; none is promoted to a final team standard before human aesthetic feedback.

Second-round templates saved on 2026-08-30:

| Template | Purpose | Signature v1 improvement | Status |
|---|---|---|---|
| `SCP_SINGLE_LINE_MAIN_v02.otpu` | MAIN | smaller typography, 0.45 pt axes, 3.3 pt highlight marker, larger plot rectangle | round-two candidate |
| `SCP_MULTI_LINE_COMPARISON_v02.otpu` | COMPARISON | direct line-end labels, no legend, stronger Primary/auxiliary hierarchy | round-two candidate |
| `SCP_SENSITIVITY_ANALYTICAL_v02.otpu` | ANALYTICAL | direct labels, explicit `y=0` rule, Unit cost as Primary | round-two candidate |
| `SCP_CONTOUR_MAIN_v02.otpu` | MAIN | custom low-saturation field palette, narrow labeled colorbar, smaller optimum marker | round-two candidate |

The v01 files are intentionally retained for auditability. The v02 multi-line and sensitivity templates store the label objects, but endpoint positions remain data-dependent; the reproducible `origin_round2.py` routine must reposition direct labels when new data ranges are substituted.

Frozen v1.1 templates saved on 2026-08-31:

| Template | Purpose | Frozen v1.1 refinement | Status |
|---|---|---|---|
| `SCP_SINGLE_LINE_MAIN_v11_FROZEN.otpu` | MAIN | 1.36 pt Primary curve and 3.05 pt optimum marker | FROZEN |
| `SCP_MULTI_LINE_COMPARISON_v11_FROZEN.otpu` | COMPARISON | collision-safe staggered direct labels and 5.5% right buffer | FROZEN |
| `SCP_SENSITIVITY_ANALYTICAL_v11_FROZEN.otpu` | ANALYTICAL | top headroom, negative-half collision-safe labels, retained `y=0` rule | FROZEN |
| `SCP_CONTOUR_MAIN_v11_FROZEN.otpu` | MAIN | lighter ticks, narrower colorbar, 19 fill levels / 7 contour lines | FROZEN |

These four templates are registered in `C:\Users\YiPian\.origin-mcp\templates` with the `frozen` tag. Do not overwrite or aesthetically iterate them unless real competition data exposes a new problem. Data-dependent direct labels must still be collision-checked when values or ranges change.

Phase 2 candidate templates saved on 2026-08-31:

| Template | Purpose | Stress-tested adaptation | Status |
|---|---|---|---|
| `SCP_SCATTER_FIT_v20_CANDIDATE.otpu` | Scatter + Fit | dense points, outliers, long labels | human review pending |
| `SCP_HEATMAP_CONTINUOUS_v20_CANDIDATE.otpu` | Heatmap | 21,901 cells, edge hotspot, long labels | human review pending |
| `SCP_OPTIMIZATION_CONVERGENCE_v20_CANDIDATE.otpu` | Optimization convergence | 2,000 iterations, log10 range | human review pending |
| `SCP_MULTIPANEL_2X2_v20_CANDIDATE.otpu` | 2×2 multi-panel | disparate units/ranges, shared legend/title | human review pending |
| `SCP_SURFACE_3D_AUXILIARY_v20_CANDIDATE.otpu` | Auxiliary 3D surface | boundary optimum, view/scale adaptation | human review pending |

These templates inherit v1.1 but are not frozen. Their data-dependent stress adaptations are documented in `../PHASE2_STYLE_REVIEW.md`.

Phase 2 human-review disposition and post-review candidates:

| Template | Decision | Current status |
|---|---|---|
| `SCP_SCATTER_FIT_v20_FROZEN.otpu` | PASS | FROZEN; modify only for scientific accuracy, readability, or real-data adaptation failure |
| `SCP_HEATMAP_CONTINUOUS_v20_FROZEN.otpu` | PASS | FROZEN under the same exception policy |
| `SCP_OPTIMIZATION_CONVERGENCE_v20_FROZEN.otpu` | PASS | FROZEN under the same exception policy |
| `SCP_MULTIPANEL_2X2_v21_REFINED_CANDIDATE.otpu` | REFINE | compact post-review candidate; human approval pending |
| `SCP_SURFACE_3D_AUXILIARY_v21_REDESIGN_CANDIDATE.otpu` | REDESIGN | 2.5D auxiliary candidate; human approval pending |

The older `SCP_MULTIPANEL_2X2_v20_CANDIDATE.otpu` and `SCP_SURFACE_3D_AUXILIARY_v20_CANDIDATE.otpu` remain audit artifacts and are not approved for publication use. The v21 files are intentionally tagged `candidate`, not `frozen`.

Do not place placeholder `.otp` or `.otpu` files here. Future records must include source graph, Origin version, creation date, score, intended data structure, and known limitations.
