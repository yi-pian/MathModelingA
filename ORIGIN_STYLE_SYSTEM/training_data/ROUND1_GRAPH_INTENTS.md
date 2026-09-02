# Round 1 — Graph Intents

## B01 Single line — MAIN

**Question:** When does the modeled response reach its maximum over a 24 h horizon?

**Primary message:** The response rises smoothly, peaks near 7 h, then decays without a secondary peak.

**Data structure:** One ordered time variable and one deterministic response.

**Recommended plot:** Single line with one vertical peak reference.

**Reason:** Continuity and peak timing are the evidence; bars or markers at every sample would add clutter.

**Highlight:** Peak near 7 h.

**Suggested Origin template:** `SCP_SINGLE_LINE_MAIN_v01`.

**Scientific transformations/disclosures:** None; raw deterministic benchmark values are plotted.

## B02 Multi-line — COMPARISON

**Question:** How do four strategies differ in transient speed and final response?

**Primary message:** The proposed strategy combines a strong early response with the highest late-stage level; the baseline remains contextual.

**Data structure:** One common time variable and four comparable response series.

**Recommended plot:** Multi-line comparison with semantic hierarchy and redundant line styles.

**Reason:** Crossovers and transient behavior must be read over a common domain.

**Highlight:** Proposed strategy; baseline is Neutral.

**Suggested Origin template:** `SCP_MULTI_LINE_COMPARISON_v01`.

**Scientific transformations/disclosures:** None.

## B03 Sensitivity — ANALYTICAL

**Question:** Which parameter causes the largest relative output change around the baseline?

**Primary message:** Unit cost is the most influential tested parameter, while efficiency has the weakest response.

**Data structure:** Symmetric parameter perturbations from −20% to +20% and four nonlinear response curves.

**Recommended plot:** Sensitivity curves with x=0 and y=0 reference lines.

**Reason:** The curves reveal magnitude, sign, asymmetry, and nonlinearity simultaneously.

**Highlight:** Unit-cost curve.

**Suggested Origin template:** `SCP_SENSITIVITY_ANALYTICAL_v01`.

**Scientific transformations/disclosures:** Responses are benchmark-defined relative changes in percent; no post-plot normalization or smoothing.

## B04 Contour — MAIN

**Question:** Where is the low-objective region in a two-parameter decision space?

**Primary message:** The objective has one dominant basin near x≈0.9, y≈−0.6 with mild local periodic structure.

**Data structure:** Regular 41 × 41 XYZ grid plus the grid-search minimum as a one-row overlay.

**Recommended plot:** Filled contour with an optimum marker.

**Reason:** Contour preserves quantitative location and gradient reading without perspective distortion.

**Highlight:** Grid-search minimum in Highlight amber.

**Suggested Origin template:** `SCP_CONTOUR_MAIN_v01`.

**Scientific transformations/disclosures:** No interpolation beyond Origin's regular-grid contour construction; the marked optimum is the minimum among sampled grid points.

