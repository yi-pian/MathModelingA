# PHASE 3 — GRAPH EDITOR REVIEW

Status: **GRAPH SELECTION TRAINING COMPLETE — HUMAN REVIEW PENDING**  
Scope: 2018A, 2022A, 2023A, 2024A, 2025A completed-result audit.  
Constraint: no new graph was drawn; no frozen template, palette, font system, or layout asset was modified.

## 0. Editorial contract

This phase asks a different question from the style phases: **which result deserves a figure, where should it appear, and what single conclusion must it carry?** Existing images were treated as evidence, not as mandatory deliverables.

Scoring rule:

`Total = Information + Uniqueness + Conclusion support + Readability + Redundancy penalty`

| Total | Editorial tier |
|---:|---|
| 32–40 | Main Figure |
| 26–31 | Supporting Figure |
| 20–25 | Appendix Figure |
| <20 | Do Not Plot |

Template references are functional names. For Multi-panel and 3D Surface Auxiliary, the Phase 3 instruction is treated as the governing freeze decision even though older local review records still carry `v21 ... CANDIDATE` filenames. This report does not rename or edit those files.

Tool boundary:

- **Python**: geometry, trajectories, collision/contact, occlusion, irregular spatial layouts, real three-dimensional spatial relations.
- **Origin**: lines, comparisons, fits/residuals, sensitivity, contour, heatmap, convergence, and conventional multi-panel analysis.
- **3D Surface Auxiliary**: only when curvature, multimodality, saddle structure, or a local basin cannot be read adequately from a contour.

---

# 1. 2018A — Heat transfer and protective-clothing design

## 1.1 Q1 GRAPH EDITOR ANALYSIS — parameter calibration

- **Question objective:** identify external and skin-side heat-transfer coefficients from the experiment.
- **Core result:** `h_out = 120.284467`, `h_skin = 8.364568`; RMSE `0.002972 °C`, `R² = 0.99999731`.
- **Evidence needed:** measured-vs-fitted agreement plus residual scale; the parameter table supplies exact values.
- **Candidate plots:** fit with residual; `x–t` temperature field; selected through-thickness profiles; mesh/time-step convergence.
- **High-value plot:** fit + residual, because it establishes identifiability/fit quality before later optimization.
- **Final selection:** one main fit-residual figure; temperature field as supporting mechanism evidence; profiles in appendix; convergence deleted from the narrative.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Measured–fitted temperature + residual | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| Temperature `x × t` heatmap | 8 | 8 | 7 | 9 | -2 | 30 | Supporting |
| Selected multilayer temperature profiles | 7 | 6 | 6 | 8 | -3 | 24 | Appendix |
| Mesh/time-step convergence | 5 | 5 | 4 | 7 | -5 | 16 | Do Not Plot |

### Q1 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | validate calibration and expose structured residuals | experiment time, measured skin temperature, fitted temperature, residual | Scatter + Fit with residual / Origin / `SCP_SCATTER_FIT_v20_FROZEN` | one figure supplies both agreement and error scale |
| Supporting Figure | explain heat penetration across depth and time | layer coordinate, time, temperature matrix | Heatmap / Origin / `SCP_HEATMAP_CONTINUOUS_v20_FROZEN` | spatial-temporal mechanism is not available from fit metrics |
| Appendix Figure | show representative thermal gradients | depth and temperature at 4–5 meaningful times | Multi-line / Origin / `SCP_MULTI_LINE_COMPARISON_v11_FROZEN` | useful for reproduction, secondary to calibration |
| Do Not Plot | demonstrate numerical stability | mesh and time-step sweep | table only | differences are tiny and the plot does not change the scientific conclusion |

**Caption draft:** Measured and fitted skin-side temperatures used to calibrate the boundary heat-transfer coefficients; the residual panel shows the remaining model–experiment discrepancy on its true scale.  
**TAKEAWAY:** The calibrated model reproduces the experiment essentially within measurement resolution and is adequate for the subsequent thickness search.

## 1.2 Q2 GRAPH EDITOR ANALYSIS — minimum layer-II thickness

- **Question objective:** find the minimum layer-II thickness satisfying the temperature and exposure-time constraints.
- **Core result:** critical `d_II = 17.572773 mm`, reported conservatively as `17.6 mm`; time above `44 °C = 288.7395 s`.
- **Evidence needed:** the final skin-temperature trajectory relative to both regulatory thresholds; exact thickness belongs in text/table.
- **Candidate plots:** final design safety trajectory; candidate-thickness comparison; full temperature field; convergence.
- **High-value plot:** final safety trajectory with `44 °C` and `47 °C` references.
- **Final selection:** one main safety figure; no generic convergence plot.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Final skin temperature with safety thresholds | 10 | 8 | 10 | 9 | 0 | 37 | Main |
| Near-critical thickness comparison | 8 | 7 | 9 | 8 | -2 | 30 | Supporting |
| Repeated full-field heatmap | 6 | 5 | 5 | 8 | -4 | 20 | Appendix |
| Solver/grid convergence | 4 | 4 | 4 | 7 | -5 | 14 | Do Not Plot |

### Q2 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | prove constraint satisfaction at the reported thickness | time, skin temperature, threshold lines, exceedance interval | Single line / Origin / `SCP_SINGLE_LINE_MAIN_v11_FROZEN` | directly answers feasibility and safety margin |
| Supporting Figure | show why rounding to `17.6 mm` is conservative | time responses at critical, lower, and reported thicknesses | Multi-line / Origin / `SCP_MULTI_LINE_COMPARISON_v11_FROZEN` | reveals the local threshold crossing without repeating the entire search |
| Appendix Figure | retain full-field audit trail | `x × t` matrix for the reported design | Heatmap / Origin / frozen heatmap | useful only for thermal-mechanism readers |
| Do Not Plot | optimization iterations or discretization sweep | iteration/error logs | table/checksum | numerical validity is better reported compactly |

**Caption draft:** Skin-side temperature of the reported `17.6 mm` layer-II design, with the allowable peak and cumulative-exposure thresholds indicated.  
**TAKEAWAY:** The rounded design is the thinnest reported configuration that remains on the safe side of both constraints.

## 1.3 Q3 GRAPH EDITOR ANALYSIS — joint layer-II/layer-IV design

- **Question objective:** minimize total insulation thickness under the same thermal constraints with `d_IV = 6.4 mm` allowed.
- **Core result:** critical `d_II = 19.242145 mm`, reported `19.3 mm`; time above `44 °C = 292.3948 s`.
- **Evidence needed:** trade-off curve locating the boundary optimum, final safety response, and robustness warning.
- **Candidate plots:** total-thickness trade-off; final safety response; parameter sensitivity; repeated heatmap.
- **High-value plot:** a compact two-panel main figure combining design trade-off and safety verification.
- **Final selection:** one main two-panel figure; sensitivity supporting because the nominal optimum is fragile to ±5% environment/material perturbations.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Layer-II/layer-IV thickness trade-off | 10 | 9 | 10 | 9 | 0 | 38 | Main |
| Final Q3 safety response | 9 | 7 | 9 | 9 | -1 | 33 | Main |
| Parameter sensitivity of safety margins | 9 | 8 | 8 | 8 | -2 | 31 | Supporting |
| Repeated temperature heatmap | 7 | 6 | 6 | 8 | -4 | 23 | Appendix |

### Q3 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | connect the boundary optimum to physical feasibility | panel (a): `d_IV`, critical `d_II`, total thickness; panel (b): time and final skin temperature | Multi-panel / Origin / frozen Multi-panel, using Single-line semantics inside panels | one editorial unit answers both “why this design” and “is it safe” |
| Supporting Figure | disclose robustness limits | ±5% perturbations and peak/exposure safety margins | Sensitivity / Origin / `SCP_SENSITIVITY_ANALYTICAL_v11_FROZEN` | prevents the nominal optimum from being overstated |
| Appendix Figure | archive full thermal field | final design `x × t` matrix | Heatmap / Origin / frozen heatmap | mechanism detail, not a new conclusion |
| Do Not Plot | every thickness-search iteration | candidate history | none | iteration order is algorithm-dependent and less informative than the trade-off envelope |

**Caption draft:** Joint insulation design: (a) minimum feasible layer-II thickness and total thickness as layer IV varies; (b) skin-temperature verification for the selected rounded design.  
**TAKEAWAY:** The selected pair lies on the minimum-thickness feasibility boundary, but its safety margin is sufficiently narrow that robustness must be reported separately.

## 1.4 2018A figure storyboard

1. **Model credibility:** calibration fit + residual.
2. **Physical mechanism (support):** `x–t` heat propagation.
3. **Single-variable design conclusion:** Q2 safety trajectory.
4. **Joint design conclusion:** Q3 trade-off + safety verification.
5. **Robustness disclosure (support):** parameter sensitivity.

Recommended body count: **3 main + 2 supporting**. Profiles and numerical-convergence evidence move to the appendix/table.

---

# 2. 2022A — Wave-energy converter dynamics and damping optimization

## 2.1 Q1 GRAPH EDITOR ANALYSIS — linear/nonlinear transient response

- **Question objective:** compute and compare displacement/velocity responses under the two damping descriptions.
- **Core result:** the two completed-response families are visually almost identical over most of the transient.
- **Evidence needed:** one aligned comparison that reveals whether the nonlinear law materially changes amplitude or phase.
- **Candidate plots:** two separate response figures; one comparative multi-panel; phase portraits; solver residuals.
- **High-value plot:** comparative multi-panel; separate near-duplicate figures are rejected.
- **Final selection:** one main comparison; phase portrait appendix only if nonlinear dynamics are discussed explicitly.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Linear vs nonlinear displacement/velocity comparison | 10 | 8 | 9 | 9 | -1 | 35 | Main |
| Separate linear response figure | 6 | 3 | 5 | 8 | -7 | 15 | Do Not Plot |
| Separate nonlinear response figure | 6 | 3 | 5 | 8 | -7 | 15 | Do Not Plot |
| Phase portraits | 6 | 6 | 5 | 7 | -3 | 21 | Appendix |

### Q1 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | test whether damping-law complexity changes the response | common time, two displacements, two velocities, difference inset or residual | Multi-panel / Origin / frozen Multi-panel | alignment makes amplitude/phase differences legible and removes duplication |
| Supporting Figure | none by default | — | — | the main comparison already closes the question |
| Appendix Figure | expose nonlinear state-space structure if discussed | displacement and velocity pairs | Multi-line or scatter / Origin | optional diagnostic, not required to answer Q1 |
| Do Not Plot | standalone linear and nonlinear panels | duplicated time histories | none | near-duplicate evidence should not occupy two figure numbers |

**Caption draft:** Linear and nonlinear damping models compared on common displacement and velocity axes over the evaluated transient.  
**TAKEAWAY:** The adopted nonlinear description produces only limited visible response change in this operating case; later optimization, rather than duplicated transients, is the informative comparison.

## 2.2 Q2 GRAPH EDITOR ANALYSIS — power-optimal damping

- **Question objective:** maximize mean captured power for constant and nonlinear speed-dependent damping.
- **Core result:** constant optimum `c = 37193.813485`, `P = 229.33394 W`; nonlinear optimum `λ = 100000`, `p = 0.415763073`, `P = 229.994292 W`.
- **Evidence needed:** unimodal constant-damping response and the two-parameter nonlinear objective landscape.
- **Candidate plots:** power curve; nonlinear contour; 3D surface; optimizer convergence.
- **High-value plots:** power curve and contour; 3D adds no reliable information beyond contour.
- **Final selection:** two main figures, ordered one-parameter then two-parameter.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Constant-damping power curve + optimum | 10 | 8 | 10 | 9 | 0 | 37 | Main |
| Nonlinear `λ × p` power contour | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| 3D power surface | 6 | 4 | 5 | 6 | -6 | 15 | Do Not Plot |
| Generic optimization convergence | 5 | 5 | 4 | 7 | -5 | 16 | Do Not Plot |

### Q2 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | show optimum uniqueness and local curvature | `c`, mean power, optimum | Single line / Origin / `SCP_SINGLE_LINE_MAIN_v11_FROZEN` | direct answer for the scalar design variable |
| Main Figure 2 | show the nonlinear optimum, boundary proximity, and parameter coupling | regular grid of `λ`, `p`, mean power, accepted optimum | Contour / Origin / `SCP_CONTOUR_MAIN_v11_FROZEN` | contour reads the basin and boundary more accurately than perspective 3D |
| Appendix Figure | none unless multiple algorithms are compared | — | — | a single optimizer trace is not scientific evidence of global optimality |
| Do Not Plot | 3D surface and routine convergence | same objective grid / iteration log | none | redundant with contour or method-dependent |

**Caption draft:** Mean captured power under (a) constant damping and (b) nonlinear speed-dependent damping; orange markers identify the accepted optima.  
**TAKEAWAY:** Nonlinear damping yields only a small power increase, and the optimum must be interpreted with its visible parameter-boundary context.

## 2.3 Q3 GRAPH EDITOR ANALYSIS — coupled heave/pitch dynamics

- **Question objective:** solve the coupled translational and rotational response.
- **Core result:** heave and pitch time histories are available, but the conclusion is conditional on inertia/reference-axis assumptions.
- **Evidence needed:** aligned coupled responses and a focused assumption/sensitivity check.
- **Candidate plots:** heave/pitch response; inertia sensitivity; phase portrait; duplicated component charts.
- **High-value plot:** coupled response multi-panel.
- **Final selection:** one main dynamics figure; sensitivity supporting because it qualifies interpretation.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Coupled heave/pitch response | 10 | 9 | 9 | 9 | 0 | 37 | Main |
| Inertia/reference-axis sensitivity | 8 | 7 | 8 | 8 | -1 | 30 | Supporting |
| Coupled phase portrait | 6 | 6 | 5 | 7 | -3 | 21 | Appendix |
| Separate component figures | 5 | 3 | 4 | 7 | -6 | 13 | Do Not Plot |

### Q3 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | display coupled modes on aligned time axes | time, heave displacement/velocity, pitch angle/angular velocity | Multi-panel / Origin / frozen Multi-panel | preserves unit differences while making phase relation visible |
| Supporting Figure | test the modeling assumption that controls interpretation | inertia/reference-axis variants and response/power metric | Sensitivity / Origin / frozen sensitivity | converts a caveat into quantified evidence |
| Appendix Figure | inspect state-space loops | heave/pitch state pairs | scatter/line / Origin | specialist diagnostic only |
| Do Not Plot | four standalone component charts | same response data | none | multi-panel already contains the information |

**Caption draft:** Coupled heave and pitch response under the adopted inertia and reference-axis convention.  
**TAKEAWAY:** The two modes are dynamically coupled, while the reported magnitude remains conditional on the mechanical-reference assumptions quantified separately.

## 2.4 Q4 GRAPH EDITOR ANALYSIS — joint translational/rotational damping

- **Question objective:** maximize total power over linear and rotational damping coefficients.
- **Core result:** `c_linear = 59120.86943`, `c_rot = 100000`, total `318.2068049 W`; rotational contribution is only `0.011053 W`.
- **Evidence needed:** objective landscape and power decomposition; the near-zero rotational contribution is a major interpretive result.
- **Candidate plots:** two-parameter contour; log-scale power split; 3D surface; convergence.
- **High-value plot:** compact contour + power-split multi-panel.
- **Final selection:** one main two-panel figure; no 3D.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Joint damping contour | 10 | 9 | 10 | 9 | 0 | 38 | Main |
| Translational vs rotational power split | 9 | 10 | 10 | 9 | 0 | 38 | Main |
| 3D objective surface | 6 | 4 | 5 | 6 | -7 | 14 | Do Not Plot |
| Optimizer history | 5 | 4 | 4 | 7 | -5 | 15 | Do Not Plot |

### Q4 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | show where the optimum lies and why the rotational channel is negligible | panel (a): damping grid and total power; panel (b): component powers on justified log scale | Multi-panel / Origin / frozen Multi-panel; contour semantics in (a) | the decomposition turns an optimum into a physical conclusion |
| Supporting Figure | none by default | — | — | main figure carries both numerical and mechanistic evidence |
| Appendix Figure | local one-dimensional slices only if boundary sensitivity is questioned | optimum-centered damping slices | Multi-line / Origin | conditional diagnostic |
| Do Not Plot | 3D and convergence | repeated grid/history | none | neither adds evidence of performance or robustness |

**Caption draft:** Joint damping optimization: (a) total mean power over translational and rotational damping; (b) decomposition of the accepted optimum into power channels.  
**TAKEAWAY:** Nearly all captured power is supplied by the translational channel, so the rotational optimum should not be mistaken for an equally important mechanism.

## 2.5 2022A figure storyboard

1. **Dynamics comparison:** one linear/nonlinear response multi-panel.
2. **Scalar optimization:** constant-damping power curve.
3. **Nonlinear optimization:** `λ × p` contour.
4. **Coupled mechanism:** heave/pitch response.
5. **Assumption audit (support):** inertia/reference-axis sensitivity.
6. **Final design interpretation:** joint contour + power split.

Recommended body count: **5 main + 1 supporting**. Separate response duplicates, routine convergence, and both 3D surfaces are deleted.

---

# 3. 2023A — Heliostat-field evaluation and design

## 3.1 Q1 GRAPH EDITOR ANALYSIS — prescribed-field performance

- **Question objective:** evaluate the prescribed 1745-heliostat field.
- **Core result:** annual optical efficiency `0.578629`, annual average power `35.374778 MW`, power density `0.563113 kW/m²`.
- **Evidence needed:** actual field geometry, spatial efficiency mechanism, and seasonal aggregate performance.
- **Candidate plots:** field layout; spatial efficiency distribution; monthly efficiency/power; 3D field rendering.
- **High-value plots:** layout and spatial efficiency; the geometry is part of the model, not decoration.
- **Final selection:** two main Python spatial figures; the cross-design monthly figure is reserved for the final comparison after Q3.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Heliostat field layout | 10 | 10 | 9 | 9 | 0 | 38 | Main |
| Spatial efficiency distribution | 9 | 9 | 9 | 9 | -1 | 35 | Main |
| Q1-only monthly efficiency/power | 8 | 7 | 8 | 9 | -2 | 30 | Supporting |
| Perspective 3D field rendering | 5 | 4 | 4 | 5 | -7 | 11 | Do Not Plot |

### Q1 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | establish geometric coverage and tower relation | heliostat centers/footprints, tower, site boundary, exclusion region | Plan-view geometry / Python / no Origin template | irregular spatial layout requires exact geometry and equal aspect |
| Main Figure 2 | reveal blocking/cosine/attenuation spatial structure | heliostat coordinates and annual optical efficiency | spatial map / Python / Signature palette transferred semantically | links aggregate efficiency to location |
| Supporting Figure | show seasonal variation only if discussed before optimization | month, efficiency components, power | Multi-panel / Origin / frozen Multi-panel | otherwise defer to the Q3 cross-design comparison |
| Do Not Plot | decorative 3D heliostat field | repeated coordinates | none | perspective occlusion reduces quantitative readability |

**Caption draft:** Prescribed heliostat field: (a) plan-view layout relative to the receiver tower and site constraints; (b) annual optical-efficiency distribution across the field.  
**TAKEAWAY:** The aggregate performance is spatially structured, so layout geometry is necessary evidence for interpreting the annual efficiency.

## 3.2 Q2 GRAPH EDITOR ANALYSIS — uniform-layout optimization

- **Question objective:** optimize tower position, mirror count/size, and mounting height in a uniform design family.
- **Core result:** tower `(0, 50)`, 3054 mirrors, `6.5 × 6.5 m`, height `3.3 m`; annual power `60.895838 MW`, power density `0.471946 kW/m²`.
- **Evidence needed:** optimized layout and a design-variable slice that shows the area/power trade-off.
- **Candidate plots:** optimized layout; mirror-size slice; optimization convergence; 3D field.
- **High-value plot:** optimized plan view; size slice is supporting, not proof of global optimality.
- **Final selection:** one main geometry figure plus one supporting Origin slice.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Optimized uniform-field layout | 10 | 9 | 9 | 9 | -1 | 36 | Main |
| Mirror-size objective slice | 8 | 8 | 8 | 9 | -2 | 31 | Supporting |
| Optimizer convergence | 5 | 5 | 4 | 7 | -5 | 16 | Do Not Plot |
| 3D layout rendering | 5 | 4 | 4 | 5 | -7 | 11 | Do Not Plot |

### Q2 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | show the optimized placement and constraint use | optimized coordinates, tower, site boundary, count/size annotation | plan-view geometry / Python | final design is inherently spatial |
| Supporting Figure | show local design trade-off around accepted mirror size | mirror side length, mirror count/area, power or power density | Single/Multi-line / Origin / frozen line template | explains why the chosen size is accepted without claiming exhaustive global proof |
| Appendix Figure | none by default | — | — | exact design parameters belong in a table |
| Do Not Plot | generic convergence and 3D rendering | search history / coordinates | none | neither establishes global optimality |

**Caption draft:** Optimized uniform heliostat-field layout under the site and receiver constraints; the companion slice shows the local performance response to mirror size.  
**TAKEAWAY:** Optimization increases annual power mainly by reorganizing usable field area and mirror population, not by a visually dramatic three-dimensional structure.

## 3.3 Q3 GRAPH EDITOR ANALYSIS — zoned variable-size design

- **Question objective:** test whether zoned mirror size and height improve the Q2 design.
- **Core result:** four zones use side lengths `6.54/6.48/6.42/6.36 m` and heights `3.32/3.29/3.26/3.23 m`; annual power `60.656296 MW`, power density `0.477354 kW/m²`.
- **Evidence needed:** Q2-vs-Q3 spatial change and annual/seasonal performance comparison; exact zone parameters are better in a table.
- **Candidate plots:** Q2/Q3 layout comparison; monthly efficiency and power; zonal parameter profile; convergence.
- **High-value plots:** layout comparison and seasonal performance multi-panel.
- **Final selection:** two main figures; zonal profile supporting only if spatial zoning is discussed mechanistically.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Q2 vs Q3 layout comparison | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| Monthly efficiency and power, Q1–Q3 | 10 | 9 | 10 | 9 | 0 | 38 | Main |
| Zone-wise size/height profile | 7 | 7 | 7 | 8 | -3 | 26 | Supporting |
| Optimization convergence | 5 | 4 | 4 | 7 | -5 | 15 | Do Not Plot |

### Q3 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | make the design change spatially explicit | Q2/Q3 mirror coordinates, zone boundaries, tower/site | comparative plan view / Python | readers can see what “zoned” changes |
| Main Figure 2 | compare annual designs across seasonal conditions | month, efficiencies, mean power for Q1/Q2/Q3 | Multi-panel / Origin / frozen Multi-panel | closes the complete problem with a common temporal comparison |
| Supporting Figure | show monotone zone adaptation if it is interpreted | zone radius/index, mirror side length, mounting height | Multi-line / Origin / frozen multi-line | useful mechanism, but exact values remain clearer in a table |
| Do Not Plot | convergence or 3D field | optimization history / repeated geometry | none | global optimality is conditional on the parameterized layout family |

**Caption draft:** Zoned-field redesign: (a) spatial comparison with the uniform Q2 solution; (b) monthly optical efficiency and mean power for the prescribed, uniform-optimized, and zoned designs.  
**TAKEAWAY:** Zoning slightly raises power density but does not surpass the uniform design in annual power, so the trade-off—not visual complexity—is the conclusion.

## 3.4 2023A figure storyboard

1. **Baseline geometry:** prescribed Q1 layout.
2. **Baseline mechanism:** spatial efficiency distribution.
3. **Optimized geometry:** Q2 layout.
4. **Local design evidence (support):** mirror-size slice.
5. **Design evolution:** Q2/Q3 spatial comparison.
6. **Final cross-design result:** monthly efficiency and power.

Recommended body count: **5 main + 1 supporting**. Use one plan-view language throughout; never introduce a decorative 3D field.

---

# 4. 2024A — Bench-dragon kinematics, collision, turnaround, and speed limit

## 4.1 Q1 GRAPH EDITOR ANALYSIS — spiral motion

- **Question objective:** determine positions and velocities of all 224 handles from `0–300 s` on the Archimedean spiral.
- **Core result:** the reconstructed chain satisfies very small arc-length, handle-distance, and speed errors.
- **Evidence needed:** representative configurations and only enough speed evidence to confirm propagation along the chain.
- **Candidate plots:** initial/final shapes; seven handle-speed curves; coordinate histories; numerical errors.
- **High-value plot:** equal-aspect geometry at `t=0` and `t=300 s`.
- **Final selection:** one main geometry figure; speed chart relegated to appendix because variations are very small and table values answer the question.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Chain shapes at `t=0` and `300 s` | 10 | 10 | 9 | 9 | 0 | 38 | Main |
| Selected handle-speed histories | 7 | 6 | 6 | 7 | -5 | 21 | Appendix |
| Separate x/y coordinate histories | 6 | 4 | 5 | 7 | -6 | 16 | Do Not Plot |
| Error/convergence curves | 5 | 4 | 4 | 7 | -5 | 15 | Do Not Plot |

### Q1 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | establish geometric evolution on the spiral | spiral, handle centers/benches, head, two representative times | 2-panel equal-aspect geometry / Python | exact geometry is the substance of the problem |
| Appendix Figure | verify small speed variation at representative handles | time and selected handle speeds | Multi-line / Origin / frozen multi-line | useful audit, weak main-text conclusion |
| Do Not Plot | separate coordinates and solver errors | repeated kinematic outputs | none | tables and residual maxima are more efficient |

**Caption draft:** Bench-dragon configurations at the start and at `300 s` along the prescribed Archimedean spiral.  
**TAKEAWAY:** The linked chain follows the prescribed spiral while preserving handle spacing; speed differences along the chain remain secondary at this stage.

## 4.2 Q2 GRAPH EDITOR ANALYSIS — first collision event

- **Question objective:** identify the first self-collision time and contact pair.
- **Core result:** `t* = 412.473837682 s`, contact between benches `0` and `8`; signed clearance changes sign at the event.
- **Evidence needed:** physical contact geometry and a root-crossing curve proving event localization.
- **Candidate plots:** critical configuration; signed clearance vs time; many pre/post snapshots; minimum-clearance heatmap.
- **High-value plots:** critical geometry and clearance crossing are complementary, not redundant.
- **Final selection:** two main figures or a single two-panel composite if page economy requires.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Critical collision geometry | 10 | 10 | 10 | 8 | 0 | 38 | Main |
| Signed clearance root crossing | 10 | 9 | 10 | 9 | 0 | 38 | Main |
| Sequence of dense chain snapshots | 6 | 5 | 5 | 6 | -5 | 17 | Do Not Plot |
| Pairwise-clearance heatmap | 7 | 7 | 6 | 7 | -4 | 23 | Appendix |

### Q2 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | identify the physical pair and contact location | bench polygons/centerlines at `t*`, highlighted benches 0 and 8 | collision geometry / Python | only geometry can establish which bodies touch |
| Main Figure 2 | establish first-event timing numerically | time near `t*`, minimum signed clearance, zero reference, root | Single line / Origin / frozen single-line | root crossing proves the event rather than merely illustrating it |
| Appendix Figure | audit all candidate pairs if challenged | pair index × time clearance matrix | Heatmap / Origin / frozen heatmap | broad diagnostic, not needed after the critical pair is identified |
| Do Not Plot | multiple nearly identical snapshots | full-chain states around `t*` | none | contact geometry plus root crossing is sufficient |

**Caption draft:** First collision event: (a) critical bench geometry identifying benches 0 and 8; (b) signed minimum clearance crossing zero at `t* = 412.473837682 s`.  
**TAKEAWAY:** The first collision is both geometrically identified and numerically localized by a clean zero crossing.

## 4.3 Q3 GRAPH EDITOR ANALYSIS — minimum feasible spiral pitch

- **Question objective:** determine the minimum pitch that avoids self-contact while entering the turn region.
- **Core result:** minimum pitch `45.033739 cm`, critical pair `(0, 19)`, critical radius `4.572603 m`; a `±0.001 cm` pitch change shifts clearance by about `±9.981×10⁻⁶ m`.
- **Evidence needed:** pitch–clearance threshold and critical contact geometry.
- **Candidate plots:** pitch-clearance curve; critical contact; dense feasibility sweep; chain snapshots.
- **High-value plots:** threshold curve and contact geometry.
- **Final selection:** two main figures, ordered analytical threshold then geometry.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Pitch vs minimum signed clearance | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| Critical contact geometry | 10 | 9 | 9 | 9 | -1 | 36 | Main |
| Dense pitch/radius feasibility map | 6 | 6 | 5 | 7 | -4 | 20 | Appendix |
| Repeated full-chain snapshots | 5 | 4 | 4 | 6 | -5 | 14 | Do Not Plot |

### Q3 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | locate the feasibility boundary and expose local sensitivity | pitch, minimum signed clearance, zero line, accepted pitch | Single line / Origin / frozen single-line | direct numerical answer with a physically meaningful zero |
| Main Figure 2 | identify the limiting contact mode | bench geometry at critical radius, highlighted pair 0/19 | contact geometry / Python | explains what sets the minimum pitch |
| Appendix Figure | audit two-dimensional feasibility only if a second variable is analyzed | pitch, radius/time, clearance | Contour/heatmap / Origin | otherwise it invents a dimension not needed by Q3 |
| Do Not Plot | more snapshots | repeated configurations | none | no additional limiting mechanism |

**Caption draft:** Minimum-pitch condition: (a) signed clearance as a function of spiral pitch; (b) limiting contact between benches 0 and 19 at the accepted boundary.  
**TAKEAWAY:** The reported pitch is a sharply localized geometric feasibility boundary, not a broad optimum.

## 4.4 Q4 GRAPH EDITOR ANALYSIS — turnaround path

- **Question objective:** construct the shortest feasible two-arc turnaround and propagate the chain through it.
- **Core result:** tangent-arc radii `3.0054 m` and `1.5027 m` (ratio `2:1`), total arc length `13.6212 m`, within the `4.5 m` turn region.
- **Evidence needed:** prescribed path and representative inbound/turn/outbound configurations; speed response is secondary.
- **Candidate plots:** separate inbound/outbound shape figures; one combined path storyboard; speed multi-panel.
- **High-value plot:** a consolidated four-state geometry storyboard.
- **Final selection:** one main Python geometry figure; one supporting speed figure.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Consolidated turnaround path storyboard | 10 | 10 | 10 | 9 | 0 | 39 | Main |
| Speed response through transition | 8 | 7 | 7 | 8 | -2 | 28 | Supporting |
| Separate inbound-only figure | 7 | 4 | 6 | 8 | -6 | 19 | Do Not Plot |
| Separate outbound-only figure | 7 | 4 | 6 | 8 | -6 | 19 | Do Not Plot |

### Q4 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | communicate path construction and chain passage in one sequence | spiral legs, two tangent arcs, turn boundary, chain states at four key times | 2×2 geometry storyboard / Python | avoids two redundant figure numbers and preserves equal-aspect geometry |
| Supporting Figure | reveal transient speed amplification caused by curvature transition | time and selected handle speeds; speed vs handle index at key times | Multi-panel / Origin / frozen Multi-panel | supports dynamic feasibility after geometry is understood |
| Appendix Figure | exact tangent construction detail if derivation is long | tangent points, centers, radii | Python geometry | derivation aid only |
| Do Not Plot | separate inbound/outbound publications | same geometry halves | none | merge into the storyboard |

**Caption draft:** Bench-dragon passage through the two-arc turnaround at four representative times; the dashed circle marks the permitted turn region.  
**TAKEAWAY:** The tangent two-arc path fits the turn region and provides a continuous geometric transition from inbound to outbound spirals.

## 4.5 Q5 GRAPH EDITOR ANALYSIS — maximum admissible head speed

- **Question objective:** choose the largest head speed that keeps every handle below the prescribed speed limit.
- **Core result:** maximum head speed `1.246266358 m/s`; maximum amplification `1.60479` at path coordinate `14.47997 m`; handles 3–7 are limiting.
- **Evidence needed:** global amplification profile and an enlarged critical neighborhood.
- **Candidate plots:** whole-passage + zoom; limiting-handle bars; repeated trajectories; raw speed histories.
- **High-value plot:** two-panel whole/zoom amplification curve with the optimum highlighted.
- **Final selection:** one main multi-panel figure; handle details in table or appendix.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Whole-passage amplification + critical zoom | 10 | 9 | 10 | 9 | 0 | 38 | Main |
| Limiting-handle index profile | 6 | 7 | 6 | 7 | -3 | 23 | Appendix |
| Full trajectory geometry again | 5 | 4 | 4 | 6 | -5 | 14 | Do Not Plot |
| Many raw handle-speed histories | 6 | 4 | 5 | 6 | -6 | 15 | Do Not Plot |

### Q5 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | locate the global amplification maximum without losing context | path coordinate, maximum handle/head speed ratio, critical point, zoom window | Multi-panel / Origin / frozen Multi-panel | global and local scales are both necessary |
| Appendix Figure | identify limiting handles if not fully tabulated | handle index and local maximum ratio | Single line / Origin / frozen single-line | detailed audit only |
| Do Not Plot | repeated geometry or all raw histories | already-used paths and dense signals | none | obscures the scalar limiting mechanism |

**Caption draft:** Maximum speed-amplification ratio over the full passage and in the critical neighborhood; the highlighted peak determines the admissible head speed.  
**TAKEAWAY:** A localized transition-region amplification, generated by handles 3–7, sets the global head-speed limit.

## 4.6 2024A figure storyboard

1. **Kinematic setup:** initial/final spiral configurations.
2. **First failure mechanism:** collision geometry + clearance root.
3. **Design boundary:** pitch-clearance curve + critical contact.
4. **Constructive solution:** consolidated turnaround storyboard.
5. **Dynamic check (support):** speeds through the turnaround.
6. **Final operating limit:** whole/zoom amplification.

Recommended body count: **6 editorial figure units** (some with panels) + **1 supporting**. Geometry remains Python; analytical event and limit curves remain Origin.

---

# 5. 2025A — Smoke-screen deployment and cooperative assignment

## 5.1 Q1 GRAPH EDITOR ANALYSIS — prescribed single deployment

- **Question objective:** evaluate the effective obscuration interval of the prescribed strategy.
- **Core result:** effective interval `[8.0564, 9.4481] s`, duration `1.39164 s`.
- **Evidence needed:** sight-line margin crossing and, only if necessary, compact geometry that explains the event definition.
- **Candidate plots:** event margin; vertical/horizontal geometry projections; 3D scene; raw trajectories.
- **High-value plot:** event margin with the effective interval; current geometry projections contain large empty ranges and are supporting at best.
- **Final selection:** one main event figure, one optional supporting geometry figure. Interval shading is scientifically useful but not native to a frozen line template.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Sight-line margin + effective interval | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| Compact vertical/horizontal geometry | 8 | 7 | 7 | 7 | -3 | 26 | Supporting |
| Perspective 3D scene | 7 | 8 | 6 | 6 | -3 | 24 | Appendix |
| Raw missile/cloud trajectories | 6 | 4 | 5 | 6 | -6 | 15 | Do Not Plot |

### Q1 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | define and measure continuous effective obscuration | time, signed sight-line distance margin, zero reference, interval endpoints | line + event band / Origin / **TEMPLATE_ADAPTATION_REQUIRED** from frozen Single-line | interval shading and two threshold crossings are semantic data, not decoration |
| Supporting Figure | explain the spatial relation without perspective distortion | missile, cloud center, burst, target in `x–z` and `x–y`, cropped to relevant extents | compact 2-panel geometry / Python | useful only if event definition is otherwise hard to follow |
| Appendix Figure | show true 3D relation when projections remain ambiguous | spatial trajectories and obscuration volume | 3D geometry / Python | real spatial scene, not Origin 3D Surface |
| Do Not Plot | every trajectory component vs time | raw states | none | event margin is the sufficient statistic for Q1 |

**Adaptation needed:** preserve frozen typography/colors/axes, add a low-weight interval band and endpoint markers, and prohibit decorative fill elsewhere.  
**Caption draft:** Signed sight-line clearance for the prescribed deployment; the shaded interval between the two zero crossings is the continuous effective obscuration window.  
**TAKEAWAY:** The given strategy provides `1.39164 s` of continuous effective obscuration, determined by two explicit geometric threshold events.

## 5.2 Q2 GRAPH EDITOR ANALYSIS — optimal single smoke bomb

- **Question objective:** optimize UAV speed, heading, release time, and burst delay for one smoke bomb.
- **Core result:** duration `4.58798 s`, speed approximately `140 m/s`, heading `5.74°`, with the accepted timing pair from the completed solution.
- **Evidence needed:** parameter slices around the accepted solution and a timing landscape showing whether timing is well localized.
- **Candidate plots:** heading/speed slices; release/burst timing heatmap; convergence; 3D parameter surface.
- **High-value plots:** parameter-slice multi-panel and timing heatmap.
- **Final selection:** two main Origin figures; no 3D and no routine convergence.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Heading and speed slices | 10 | 9 | 10 | 9 | -1 | 37 | Main |
| Release-time × burst-delay heatmap | 9 | 9 | 9 | 9 | -1 | 35 | Main |
| Optimizer convergence | 5 | 4 | 4 | 7 | -5 | 15 | Do Not Plot |
| 3D timing surface | 6 | 4 | 5 | 6 | -6 | 15 | Do Not Plot |

### Q2 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure 1 | expose sensitivity and boundary behavior of heading/speed | heading slice, speed slice, obscuration duration, accepted values | Multi-panel / Origin / frozen Multi-panel | shows that heading is sharply localized while speed is near a boundary |
| Main Figure 2 | show timing basin and accepted pair | release time, burst delay, duration matrix, accepted point | Heatmap or Contour / Origin / frozen heatmap/contour | two-dimensional timing structure is not recoverable from a table |
| Appendix Figure | algorithm comparison only if multiple optimizers exist | best/mean vs evaluation | Optimization Convergence / Origin / frozen convergence | not justified by one search trace |
| Do Not Plot | 3D timing surface | same matrix | none | contour/heatmap is more quantitative |

**Caption draft:** Single-bomb strategy around the accepted solution: (a) obscuration duration along heading and speed slices; (b) duration over the feasible release-time/burst-delay plane.  
**TAKEAWAY:** The accepted strategy lies in a narrow heading region and near the speed bound, while the timing map identifies the usable local basin.

## 5.3 Q3 GRAPH EDITOR ANALYSIS — three-bomb interval chaining

- **Question objective:** maximize the union of effective intervals produced by three bombs from one UAV.
- **Core result:** union duration `7.60951 s`; marginal contributions approximately `3.84`, `2.58`, and `1.19 s`.
- **Evidence needed:** interval adjacency/overlap and marginal contribution, not three separate copies of Q1 geometry.
- **Candidate plots:** interval chain; contribution bars/curve; three cloud trajectories; convergence.
- **High-value plot:** event-interval chain. No current frozen template represents interval unions faithfully.
- **Final selection:** one main interval figure; contribution analysis supporting.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Three-bomb effective-interval chain | 10 | 10 | 10 | 9 | -1 | 38 | Main |
| Marginal contribution by bomb | 8 | 7 | 7 | 8 | -3 | 27 | Supporting |
| Three separate geometry plots | 7 | 4 | 5 | 6 | -6 | 16 | Do Not Plot |
| Optimizer convergence | 5 | 4 | 4 | 7 | -5 | 15 | Do Not Plot |

### Q3 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | show how individual windows form the union | bomb ID, interval start/end, overlap/gap, union envelope | interval-chain chart / Origin / **TEMPLATE_ADAPTATION_REQUIRED** | a Gantt-like interval grammar is the scientific object here |
| Supporting Figure | quantify diminishing returns | bomb sequence and marginal union contribution | compact bar/step chart / Origin / adaptation required unless table used | shows why the third bomb adds less coverage |
| Appendix Figure | geometry for one anomalous bomb only | selected trajectory/cloud geometry | Python | avoid repeating Q1 three times |
| Do Not Plot | separate cloud geometries and generic convergence | repeated trajectories/search history | none | neither explains interval union efficiently |

**Adaptation needed:** a dedicated interval-union template with horizontal bars, common time axis, direct row labels, neutral overlap encoding, and no categorical rainbow.  
**Caption draft:** Effective intervals of the three smoke bombs and their chained union on a common time axis.  
**TAKEAWAY:** The strategy gains `7.60951 s` by chaining partially adjacent windows, with diminishing marginal benefit from later bombs.

## 5.4 Q4 GRAPH EDITOR ANALYSIS — three-UAV cooperative obscuration

- **Question objective:** coordinate three UAVs to enlarge total obscuration coverage.
- **Core result:** total duration `11.51255 s` formed by three separated effective intervals.
- **Evidence needed:** timing structure across UAVs and, secondarily, their spatial division of labor.
- **Candidate plots:** UAV interval schedule; union-coverage curve; compact trajectory geometry; three individual event figures.
- **High-value plot:** common-axis interval schedule because the gaps are as important as the total.
- **Final selection:** one main interval figure; coverage/geometry supporting.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Three-UAV interval schedule | 10 | 10 | 10 | 8 | -1 | 37 | Main |
| Union coverage vs time | 8 | 7 | 8 | 8 | -2 | 29 | Supporting |
| Compact UAV trajectory geometry | 8 | 8 | 7 | 7 | -2 | 28 | Supporting |
| Three standalone event plots | 7 | 4 | 6 | 7 | -6 | 18 | Do Not Plot |

### Q4 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | show temporal cooperation and uncovered gaps | UAV ID, effective interval start/end, union row | interval schedule / Origin / **TEMPLATE_ADAPTATION_REQUIRED** | total duration alone hides separation and coordination quality |
| Supporting Figure 1 | show instantaneous coverage multiplicity | time, active-window count or binary union | Single/Multi-line / Origin / frozen line template with step semantics | makes overlap and gaps explicit |
| Supporting Figure 2 | explain spatial role allocation | three UAV paths, bursts, target/missile projections | geometry / Python | include only if trajectories differ meaningfully |
| Do Not Plot | one Q1-style margin chart per UAV | repetitive event evidence | none | common schedule is more efficient |

**Adaptation needed:** reuse the Q3 interval template once approved; add a union row rather than new colors.  
**Caption draft:** Effective obscuration intervals generated by the three UAVs and their temporal union.  
**TAKEAWAY:** Cooperation raises total coverage to `11.51255 s`, but the separated windows reveal residual gaps that the scalar objective alone conceals.

## 5.5 Q5 GRAPH EDITOR ANALYSIS — multi-UAV/multi-missile assignment

- **Question objective:** assign five UAVs and their smoke bombs across three missiles and report the combined coverage.
- **Core result:** FY1→M1, FY2→M2, FY3→M2, FY4→M1, FY5→M3; durations M1 `8.5457 s`, M2 `10.2215 s`, M3 `4.37867 s`, total `23.14588 s`. Five bombs have zero marginal contribution. An external comparison reaches about `24.32 s`, so this is high-quality feasible, not certified global optimum.
- **Evidence needed:** discrete assignment, union intervals by missile, and contribution/redundancy disclosure.
- **Candidate plots:** assignment matrix; missile interval schedule; contribution matrix; convergence; 3D battle scene.
- **High-value plots:** assignment plus missile intervals. Convergence cannot certify optimality and should be deleted.
- **Final selection:** one compact main multi-panel or two main figures; redundancy diagnostic supporting.

| Candidate | Info | Unique | Support | Read | Penalty | Total | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| UAV–missile assignment matrix | 9 | 9 | 10 | 9 | 0 | 37 | Main |
| Union intervals by missile | 10 | 10 | 10 | 9 | 0 | 39 | Main |
| Bomb contribution/redundancy matrix | 9 | 9 | 9 | 8 | -1 | 34 | Main |
| Zero-contribution bomb diagnostic | 8 | 9 | 8 | 8 | -2 | 31 | Supporting |
| Optimizer convergence | 4 | 4 | 3 | 7 | -6 | 12 | Do Not Plot |
| 3D battle scene | 6 | 6 | 5 | 5 | -6 | 16 | Do Not Plot |

### Q5 GRAPH PLAN

| Tier | Purpose | Data | Plot / tool / template | Why |
|---|---|---|---|---|
| Main Figure | jointly communicate allocation, realized intervals, and nonzero contributions | panel (a): UAV×missile binary assignment; panel (b): union intervals by missile; panel (c): contribution matrix or per-bomb marginal gain | Multi-panel / Origin / frozen Multi-panel, with frozen heatmap semantics plus **interval-template adaptation** | a single decision-result unit avoids three disconnected figures |
| Supporting Figure | disclose redundant resources and solution limitation | bomb ID, assigned missile, marginal union contribution, zero flags | contribution line/bar or annotated table / Origin | prevents the feasible solution from being narrated as globally efficient |
| Appendix Figure | method comparison only if comparable full solutions exist | objective by independent method/seed | Multi-line / Origin | external `24.32 s` comparison is better in a table unless full traces are comparable |
| Do Not Plot | optimization convergence and decorative 3D | search history/spatial scene | none | convergence does not prove globality; 3D does not clarify assignment |

**Adaptation needed:** the interval panel must use the proposed interval-union grammar; assignment and contribution panels can reuse frozen heatmap color hierarchy without implying continuous magnitude for binary cells.  
**Caption draft:** Cooperative five-UAV solution: (a) discrete UAV–missile assignment, (b) realized effective intervals by missile, and (c) marginal contribution of deployed bombs.  
**TAKEAWAY:** The solution delivers `23.14588 s` of aggregate coverage, but zero-contribution bombs and a stronger external feasible value show that it is not a certified global optimum.

## 5.6 2025A figure storyboard

1. **Event definition:** Q1 signed margin and effective interval.
2. **Single-device optimization:** Q2 parameter slices.
3. **Timing structure:** Q2 timing heatmap.
4. **Sequential cooperation:** Q3 interval chain.
5. **Distributed cooperation:** Q4 UAV interval schedule.
6. **System-level decision:** Q5 assignment + intervals + contributions.
7. **Optional spatial explanation:** one compact projection figure reused conceptually, never repeated per question.

Recommended body count: **6 main editorial units + at most 2 supporting**. This problem exposes a genuine template gap: event intervals require adaptation; it does not justify altering the frozen line/heatmap templates.

---

# 6. Cross-year statistics and editorial findings

## 6.1 Recommended main-figure inventory

| Year | Main editorial units | Supporting | Appendix-only | Main narrative |
|---|---:|---:|---:|---|
| 2018A | 3 | 2 | 2 | calibration → thermal constraint → joint design/robustness |
| 2022A | 5 | 1 | 2 | dynamics → scalar optimization → coupled optimization/mechanism |
| 2023A | 5 | 1 | 0–1 | baseline spatial field → optimized layout → cross-design seasonality |
| 2024A | 6 | 1 | 2–3 | geometry → event → feasibility boundary → path → operating limit |
| 2025A | 6 | 1–2 | 1–2 | event → local optimization → temporal cooperation → assignment |

Across these projects, a strong A-paper usually needs **5–7 main editorial figure units**. Use **3–6 supporting/appendix figures** only where they add mechanism, robustness, or reproducibility. “One to three figures per question” is a ceiling, not a quota.

## 6.2 Frozen-template usage frequency in the selected plans

Counts refer to recommended figure uses, not existing files. A multi-panel counts once; embedded panel semantics are noted separately.

| Frozen template / class | Main | Supporting/appendix | Typical role |
|---|---:|---:|---|
| Single line | 5 | 4 | threshold crossing, scalar optimum, trade-off, critical boundary |
| Multi-line comparison | 1 | 5 | controlled scenario comparison; rarely the final headline |
| Sensitivity | 0 | 2 | robustness/assumption qualification |
| Contour | 3 | 1 | two-parameter objective or feasibility landscape |
| Scatter + Fit | 1 | 0 | calibration credibility; residual carried with it |
| Heatmap continuous | 1 | 4 | field mechanism or dense two-dimensional response |
| Optimization convergence | 0 | 1 conditional | only multi-algorithm/stability evidence, never routine decoration |
| Multi-panel | 8 | 3 | combine complementary evidence under one conclusion |
| 3D Surface Auxiliary | 0 | 0 | none of the audited results needs it |
| Python geometry/spatial figure | 9 | 5 | layout, collision/contact, path, occlusion geometry |
| Interval-union adaptation | 4 | 1 | 2025A event windows and schedules |

The important usage result is not that Multi-panel “wins.” It is that main figures frequently require **two complementary evidence modes**—for example geometry + clearance, trade-off + safety, contour + decomposition. Multi-panel is justified only when the panels close one conclusion.

## 6.3 Python vs Origin division

| Use Python when… | Use Origin when… |
|---|---|
| exact aspect ratio, polygons, collision/contact, trajectories, spatial assignment, irregular field coordinates, or real 3D geometry are the evidence | the evidence is a scalar/parameter response, fit, residual, sensitivity, regular matrix field, convergence comparison, or aligned analytical panels |
| geometry must remain faithful under zoom/cropping | direct labels, optimum markers, threshold references, shared axes, and publication exports dominate |
| mixing coordinate systems or constructing spatial insets is unavoidable | data already form tidy columns or a regular matrix |

Do not transfer a real spatial-geometry problem into Origin merely to reuse a template. Conversely, do not use Python for conventional analytical curves when a frozen Origin template already carries the approved hierarchy.

## 6.4 Most frequently deleted plots

1. **Routine convergence traces** from one optimizer or one discretization. They report software behavior, not a model conclusion.
2. **3D surfaces duplicating a contour.** Across five years, no audited case earns main or auxiliary 3D Surface use.
3. **Near-duplicate response figures** separated only by model/scenario names; combine on aligned axes or retain only the decisive comparison.
4. **Dense time snapshots** around a collision/contact event; one critical geometry plus one signed-clearance curve is stronger.
5. **Repeated geometry in later questions.** Reuse the established coordinate system and plot only the changed decision or mechanism.
6. **Raw state histories** when a derived safety margin, union interval, or amplification ratio is the sufficient statistic.

## 6.5 Decision rules learned from the five projects

- A main figure must support a sentence that cannot be supported as clearly by a table.
- Prefer a **signed margin with a zero line** over plotting both sides of a constraint separately.
- Pair geometry with an analytical event curve only when they answer different questions: **what/where** versus **when/how close**.
- Put exact parameter values in tables; plot their landscape, trade-off, uncertainty, or mechanism.
- Sensitivity belongs in supporting material unless robustness is itself the main claim.
- A convergence plot enters the paper only when it compares algorithms/seeds, reveals instability, or is necessary to justify numerical trust.
- A 3D surface is never selected merely because the model has two inputs. If contour shows optimum, gradient, feasible domain, and multimodality, stop at contour.
- A multi-panel figure must have one shared takeaway. Four available panels do not create four obligations.
- Do not use template consistency to erase scientific structures such as interval unions. Mark `TEMPLATE_ADAPTATION_REQUIRED` and define the smallest semantic extension.
- If a result is conditional or not globally certified, the figure/caption must preserve that limitation.

## 6.6 Final Phase 3 verdict

The stable system is **result-first, evidence-second, template-third**:

1. state the exact conclusion;
2. identify the minimum visual evidence required;
3. score and delete redundant candidates;
4. select Python or Origin based on scientific geometry/data structure;
5. apply the closest frozen template without changing its visual language;
6. adapt only when a real data grammar is absent.

No frozen template was modified in this phase. The only new template need discovered is an **event interval / interval-union chart**, which should be trained separately rather than folded into the frozen Single-line or Multi-panel classes.

