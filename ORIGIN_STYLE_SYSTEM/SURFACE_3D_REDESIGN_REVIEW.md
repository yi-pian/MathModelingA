# SURFACE 3D REDESIGN REVIEW

## Status

**REDESIGN COMPLETE — AUXILIARY CANDIDATE — HUMAN APPROVAL PENDING**

Candidate template: `SCP_SURFACE_3D_AUXILIARY_v21_REDESIGN_CANDIDATE.otpu`

The read-only cause analysis is recorded in `SURFACE_3D_DIAGNOSTIC.md`. No missing data, Z-range clipping, color-map clipping, or layer clipping was found. The previous white region was a view/rendering ambiguity and the v20 candidate remains rejected and unfrozen.

## 2.5D scientific redesign

- Replaced the stronger perspective with a near-orthographic, higher viewing angle.
- Preserved the real Z range; the surface was not flattened to make it fit.
- Applied the same deep-blue → teal → muted-green → pale-yellow family as frozen Contour/Heatmap.
- Used a continuous 256-step Origin palette derived from the frozen 19-anchor field colors.
- Reduced surface isolines to six and kept them subordinate to the filled surface.
- Reduced 3D tick/axis emphasis and removed the collision-prone Z-axis title; the narrow labeled colorbar carries the objective quantity.
- Narrowed and deweighted the colorbar, reduced its tick count, and added the compact `Objective value` label.
- Retained the warm-orange optimum marker. Its display Z is lifted by 1.8% of the plotted Z span only to avoid Z-fighting; the underlying optimum value is unchanged.
- Used a calmer camera (`azimuth 135°`, `inclination 68°`) with minimum practical perspective.

## Completeness and stress audit

| Check | Standard | Stress | Result |
|---|---:|---:|---|
| Grid | 41×41 | 61×61 | Complete regular grids |
| Missing values | 0 | 0 | PASS |
| Values outside displayed Z | 0 | 0 | PASS |
| Boundary optimum | interior | near boundary | PASS |
| Strong asymmetry | moderate | intentional | PASS |
| Surface continuity | complete | complete | PASS |
| Label collision | none | none | PASS |
| Colorbar balance | pass | pass | PASS |

The remaining white regions are outside the rectangular surface domain in the 3D projection; no valid surface cells are missing.

## Scientific role

Permanent priority:

`Contour > 3D Surface`

Use this surface only when curvature, multimodality, saddle structure, or a local basin adds explanatory value. If a contour already shows optimum, gradient, feasible domain, and multimodality clearly, omit the surface.

## TEMPLATE_ADAPTATION_REQUIRED

Adapt the candidate when real data expose:

- boundary markers hidden by the frame: change camera orientation or marker annotation, not the optimum coordinates;
- extreme Z dynamic range: use a disclosed transform or revised axis range only when scientifically justified;
- irregular or sparse grids: do not imply a continuous surface without stating/interrogating interpolation;
- long axis titles: abbreviate with defined units or increase margins; never allow label overlap;
- multiple local optima: highlight only the scientifically selected optimum and explain the selection criterion.

## Deliverables

- `outputs/phase2_refinement/P2_SURFACE_3D_25D_REDESIGN.png/.pdf/.svg`
- `outputs/phase2_refinement/P2_SURFACE_3D_25D_REDESIGN_STRESS.png/.pdf/.svg`
- `themes/SignatureScientificField19.pal`

The template is not FROZEN pending human review.

