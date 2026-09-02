# MULTI-PANEL REFINEMENT REVIEW

## Status

**REFINEMENT COMPLETE — HUMAN APPROVAL PENDING**

Candidate template: `SCP_MULTIPANEL_2X2_v21_REFINED_CANDIDATE.otpu`

This work migrates Signature Scientific Style v1.1 into a compact 2×2 composition. It does not alter the frozen single-line, multi-line, sensitivity, contour, scatter-fit, heatmap, or convergence templates.

## What changed

| Review item | Refinement | Result |
|---|---|---|
| Horizontal/vertical gaps | Four layers repacked into a denser 2×2 cluster | More plotting area; panel relationships read as one figure |
| Outer whitespace | Left/right and top/bottom margins reduced while retaining label clearance | Higher information density without clipping |
| Typography | Introduced a composite-specific hierarchy rather than scaling a single-panel template mechanically | Axis titles, ticks, shared labels, legend, and panel tags remain balanced at insertion size |
| Panel tags | `(a)`–`(d)` enlarged and aligned to a common panel-relative offset | Faster navigation; no curve collision in standard or stress data |
| Shared legend | One borderless legend placed directly above the panel cluster | Legend belongs to the composition instead of floating at the page edge |
| Shared X title | Repeated X titles removed; one `Time (s)` title centered below the cluster | Less repetition and more usable vertical space |
| Repeated axes | Each panel retains only the variable-specific Y title/unit | Scientific meaning remains explicit without redundant titles |
| Hierarchy | Observed result remains Primary; model line remains lighter Secondary | Main evidence is visible first across all four panels |

## Composite typography contract

The multi-panel template has its own size hierarchy. Panel tags are intentionally more prominent than tick labels; shared legend and shared X title are sized for the full figure; per-panel axis titles are compact but remain legible. This is a composition-specific system and must not be derived by applying one global percentage reduction to a single-panel template.

## Insertion-size audit

| Width | Standard benchmark | Stress benchmark | Decision |
|---:|---|---|---|
| 15.5 cm | PASS | PASS | Publication-ready working size |
| 8.8 cm | PASS | PASS, with dense scientific ticks near the practical lower limit | Usable when the journal column and document rasterization preserve the exported resolution |

Audit criteria: label collision, visual hierarchy, whitespace, tick consistency, shared-object proximity, and cross-panel alignment. The 8.8 cm audit uses the actual reduced raster, not a zoomed full-size preview.

## Stress test

The stress composition deliberately combines:

- displacement near `10^-3`;
- velocity near `10^2`;
- power near `10^4`;
- absolute error spanning `10^-8`–`10^-3` on a true logarithmic Y axis;
- scientific notation and a localized high-power peak.

The logarithmic panel uses strictly positive absolute-error values; it is not a label-only simulation of a log axis. The stress result preserves the common legend and shared X title, while its left/right layer geometry is adapted to clear scientific-notation ticks.

## TEMPLATE_ADAPTATION_REQUIRED

The candidate is directly reusable only when panel roles and label lengths are comparable. Adaptation is required when real data introduce:

- longer variable names or units: adjust composite typography and outer margins;
- scientific notation wider than the stress benchmark: expand the affected layer's left allowance;
- log data containing zero or negative values: choose a scientifically justified transform or a non-log axis and disclose it;
- unequal X variables: restore panel-specific X titles instead of forcing a shared title;
- more than two series: reassess shared legend versus direct labels and do not overload the cluster;
- a dominant panel that carries the conclusion: enlarge that panel only if the evidence hierarchy justifies an asymmetric layout.

Template consistency must never override scientific readability.

## Final visual review

- Label collision: PASS
- Visual hierarchy: PASS
- Whitespace: PASS
- Tick consistency: PASS
- Shared legend balance: PASS
- Cross-panel consistency: PASS

The template remains a candidate until the next human aesthetic decision; it has not been marked FROZEN.

## Deliverables

- `outputs/phase2_refinement/P2_MULTIPANEL_2X2_REFINED.png/.pdf/.svg`
- `outputs/phase2_refinement/P2_MULTIPANEL_2X2_REFINED_STRESS.png/.pdf/.svg`
- `outputs/phase2_refinement/P2_MULTIPANEL_2X2_REFINED_155MM_AUDIT.png`
- `outputs/phase2_refinement/P2_MULTIPANEL_2X2_REFINED_088MM_AUDIT.png`
- stress equivalents of both insertion-size audits
- `benchmarks/phase2_multipanel_refinement_stress.csv`

