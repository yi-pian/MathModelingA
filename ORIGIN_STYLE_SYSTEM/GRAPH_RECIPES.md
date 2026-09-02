# Graph Recipes v0.1

## R01 — Single Line / MAIN

**Data:** ordered numeric x, one numeric y; optional event/optimum point.

**Template:** `SCP_SINGLE_LINE_MAIN`.

**Color semantics:** curve = Primary; optimum = Highlight; optional reference = Neutral.

**Steps:** import table → designate X/Y → plot line → apply 120 × 80 mm page → format axes/ticks/font → add one factual annotation → export PNG/PDF/SVG → score.

**Do not use:** unordered categories, discontinuous events that would be falsely connected, or observations where a scatter representation is more honest.

## R02 — Multi-Line / COMPARISON

**Data:** common ordered x and 2–6 comparable y series.

**Template:** `SCP_MULTI_LINE_COMPARISON`.

**Color semantics:** proposed = Primary; baseline = Neutral; alternatives = Secondary plus approved comparison colors. Reinforce with dash and marker differences.

**Steps:** import wide table → preserve a common x scale → plot all y columns → reorder legend baseline/alternatives/proposed as rhetorically appropriate → reduce marker frequency → label only decisive endpoint/crossover → export and score.

**Do not use:** curves with incompatible units or scales; use panels or a carefully justified dual-y chart instead.

## R03 — Scatter + Fit / ANALYTICAL

**Data:** paired observations, fitted values, optional confidence interval and residuals.

**Template:** `SCP_SCATTER_FIT_ANALYTICAL` after human-approved training.

**Color semantics:** observations = Neutral outline; fit = Primary; confidence band = Secondary at low opacity; excluded/failed observations = Warning only with disclosure.

**Steps:** diagnose data → scatter raw observations → run documented fit → show fit equation/metric only if it supports the claim → never connect observation order → preserve outliers → score scientific accuracy heavily.

**Do not use:** fit line without raw observations or a model selected only for visual smoothness.

## R04 — Sensitivity / ANALYTICAL

**Data:** controlled perturbation around a baseline and one response per parameter.

**Template:** `SCP_SENSITIVITY_ANALYTICAL`.

**Color semantics:** most influential parameter = Primary; other parameters = Secondary/approved comparison colors; zero response and baseline perturbation = Neutral.

**Steps:** express perturbation in percent → plot relative response change → add x=0 and y=0 references → preserve nonlinear/asymmetric response → direct-label curves if feasible → export and score.

**Do not use:** mixing absolute and relative responses without explicit normalization.

## R05 — Contour / MAIN

**Data:** regular x-y grid with scalar objective z; optional feasible mask and optimum.

**Template:** `SCP_CONTOUR_MAIN`.

**Color semantics:** ordered low-to-high field map; optimum = Highlight; constraints = Warning outline; contour labels = near-black.

**Steps:** import XYZ → convert to matrix/grid when required → use 10–14 filled levels → overlay 5–7 labeled isolines → mark optimum → include color bar with units → keep equal geometric scaling when x and y units are comparable → export and score.

**Do not use:** irregular samples without a disclosed interpolation method or a rainbow map.

## R06 — Heatmap / ANALYTICAL

**Data:** matrix or regular grid, one scalar field.

**Template:** pending golden-example training.

**Do not use:** interpolated appearance that implies unmeasured resolution.

## R07 — 3D Surface / ANALYTICAL supplement

**Data:** regular x-y-z surface.

**Template:** pending golden-example training.

**Do not use:** as the only evidence for numerical differences or optimum location.

## R08 — Optimization Convergence / ANALYTICAL

**Data:** iteration/time and objective, gap, or residual for one or more algorithms.

**Template:** pending golden-example training.

**Do not use:** smoothed trajectories that hide oscillation or instability. A log axis must be disclosed.

## R09 — Multi-Panel / MAIN

**Data:** several panels that each contribute unique evidence to one conclusion.

**Template:** pending golden-example training.

**Do not use:** a grid of redundant panels. Define a hero panel and align plot rectangles.

