# BLIND FIGURE STORYBOARD — 2020A Reflow Oven Temperature Profile

Status: **FROZEN BEFORE PLOTTING AND EXTERNAL CROSS-CHECK**

The order follows the reader's evidence needs rather than mechanically repeating Q1–Q4.

## Figure 1 — Model credibility

- **Question source:** Q1 model establishment.
- **Role:** validation foundation.
- **Tool:** Origin.
- **Template:** `SCP_SCATTER_FIT_v20_FROZEN` with residual companion.
- **TAKEAWAY:** The effective thermal model reproduces the official experiment with RMSE `1.484 °C`, supporting bounded process prediction but not parameter identifiability.

## Figure 2 — Thermal mechanism and prescribed prediction

- **Question source:** Q1 specified operating condition.
- **Role:** primary physical response.
- **Tool:** Origin.
- **Template:** `SCP_MULTI_LINE_COMPARISON_v11_FROZEN`.
- **TAKEAWAY:** PCB thermal inertia smooths and delays the local furnace-air profile, producing the four required checkpoint temperatures.

## Figure 3 — Throughput boundary

- **Question source:** Q2.
- **Role:** active-constraint decision.
- **Tool:** Origin.
- **Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN`.
- **TAKEAWAY:** Peak temperature reaches its `240 °C` lower limit at `77.871 cm/min`, making it the active maximum-speed constraint in the model.

## Figure 4 — Low-area process design

- **Question source:** Q3.
- **Role:** optimized response and constraint verification.
- **Tool:** Origin.
- **Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN` with data-bound objective-region fill.
- **TAKEAWAY:** The selected bounded-search profile reduces the pre-peak liquidus excess to `420.973 °C·s` while satisfying all process limits.

## Figure 5 — Symmetry compromise

- **Question source:** Q3 + Q4.
- **Role:** final design trade-off and physical verification.
- **Tool:** Origin.
- **Template:** frozen Multi-panel.
- **TAKEAWAY:** Under a 105% Q3-area cap, Q4 modestly improves peak-centered symmetry with a small area cost; the result remains conditional on the compromise rule and search family.

## Supporting Figure S1 — Local Q3 boundary context

- **Question source:** Q3.
- **Role:** local landscape and limitation disclosure.
- **Tool:** Origin.
- **Template:** `SCP_CONTOUR_MAIN_v11_FROZEN`.
- **TAKEAWAY:** The accepted Q3 solution is locally driven toward the `T8–9` upper bound; the slice is explanatory and not global-optimum proof.

## Appendix Figure A1 — Limiting-speed time history

- **Question source:** Q2.
- **Role:** reproducibility/threshold audit.
- **Tool:** Origin.
- **Template:** `SCP_SINGLE_LINE_MAIN_v11_FROZEN`.
- **TAKEAWAY:** At the limiting speed, slope and duration metrics remain feasible while the peak just touches the lower bound.

## Count budget

- MAIN: **5 figure units**.
- Supporting: **1 planned, not required for blind-test rendering**.
- Appendix: **1 planned, not required for blind-test rendering**.

Five main units are justified because the paper needs five non-redundant links: model credibility, prescribed prediction, active throughput constraint, low-area design, and final symmetry trade-off. No question receives a figure merely to satisfy a quota.

