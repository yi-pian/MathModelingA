# Graph Decision Guide

## Required GRAPH INTENT

Before any drawing operation, write:

```text
GRAPH INTENT
Question:
Primary message:
Data structure:
Recommended plot:
Reason:
Highlight:
Suggested Origin template:
Scientific transformations/disclosures:
```

## Decision matrix

| Analytical question | Data structure | Primary plot | Secondary option | Avoid |
|---|---|---|---|---|
| How does one quantity evolve? | ordered x, one y | single line | line + sparse markers | bars for dense time points |
| Which method performs better over a common domain? | ordered x, 2–6 y series | multi-line | small multiples if crossings are dense | equal visual weight for all methods |
| Does a model explain observations? | paired x-y observations, fitted response | scatter + fit | residual panel | connecting observations as a time series |
| Which input matters most? | perturbation vs response | sensitivity curves | tornado/range plot for discrete scenarios | radar plot as the default |
| Where is a two-parameter optimum? | x-y grid with one scalar z | filled contour + labeled isolines | 3D surface as supplement | 3D-only evidence |
| How is a scalar field distributed? | matrix or regular grid | heatmap | contour overlay | rainbow color maps |
| How does an optimization progress? | iteration plus objective/gap | convergence curve, log y if justified | inset for late stage | smoothing away oscillation |
| How do three solutions compare across metrics? | methods × metrics | grouped dot/bar chart after normalization disclosure | small multiples in native units | polygon area/radar as sole evidence |
| Do panels jointly support one conclusion? | related heterogeneous tables | multi-panel | hero panel + subordinate checks | equal panels without evidence logic |

## MAIN / ANALYTICAL / COMPARISON

- MAIN: one conclusion, strongest hierarchy, at most one Highlight event, minimal legend burden.
- ANALYTICAL: diagnostic detail, neutral styling, uncertainty and residual structure visible, annotation sparse.
- COMPARISON: series redundancy through color + line + marker; baseline subordinate; proposed method Primary.

## Contour versus 3D surface

For two continuous parameters and one objective, the permanent default is:

`Contour > 3D Surface`

If a contour already communicates all of the following clearly, do **not** add a 3D surface:

- optimum location;
- gradient direction or steepness;
- feasible-domain boundary;
- multimodal structure.

3D Surface is an **AUXILIARY FIGURE**, never an automatic main figure. Add it only when curvature, multimodality, saddle structure, or a local basin is itself part of the scientific explanation. It must not be used merely to make a two-parameter response look more impressive.

When a 3D surface is justified, use a low-perspective 2.5D view, preserve the true Z scale, disclose any display-only lift applied to an optimum marker, and verify that no valid surface region is hidden by range, color-map, layer, or missing-data clipping.

## Escalation to Python

Use Python for complex geometric constructions, trajectories/schematics, or specialized computed graphics that Origin cannot express without distortion or brittle scripting. Record the reason and keep the same semantic palette and typography.
