# EXTERNAL GRAPH CROSS-CHECK

## Cross-check boundary

This cross-check began only after `BLIND_GRAPH_EDITOR_ANALYSIS.md`, `BLIND_FIGURE_STORYBOARD.md`, and `BLIND_EDITOR_AUDIT.md` had been frozen. External material was used to test the independently selected evidence architecture; it was not used to rewrite the original decisions.

Problem: **2020 CUMCM A — Reflow Oven Temperature Profile**.

External references consulted:

- The [official problem archive](https://www.mcm.edu.cn/html_cn/node/10405905647c52abfd6377c0311632b5.html), used only for the problem statement and supplied experiment.
- A [China College Students Online commentary page](https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2020sxjmstjp/210603/1699283.shtml) attributed to organizing-committee expert Cai Zhijie; it confirms that model construction, parameter calibration, feasibility constraints, and optimization objectives are the central evidence chain.
- A [Shanghai Maritime University summary](https://wlxy.shmtu.edu.cn/wlxy/2022/0309/c10458a174069/page.psp) describing a heat-transfer/Newton-cooling model, least-squares calibration, a symmetry norm, and a dual-objective treatment of area and symmetry.
- A public [CUMCM2020A paper source](https://github.com/personqianduixue/CUMCM2020A/blob/master/%E8%AE%BA%E6%96%87.tex), inspected only after the blind plan was frozen. Its graphics include a calibration fit, speed-dependent indicators, optimized furnace curves, symmetry comparison, and sensitivity analysis.
- A peer-reviewed [experimental-technology article](https://www.sy.uestc.edu.cn/cn/article/doi/10.12179/1672-4550.20210278) whose figure set includes furnace temperature distribution and optimized temperature-profile curves.

## AGREEMENT

1. **Calibration requires visual evidence.** External solutions commonly show the measured-versus-predicted furnace curve. This agrees with MAIN-1, which adds a residual panel so agreement structure and systematic error can be judged together.
2. **The transient temperature profile is a core result.** External sources repeatedly use the furnace curve for the prescribed setting and optimized settings. This agrees with MAIN-2 and MAIN-4.
3. **Question 2 is a speed-feasibility problem.** Public work plots process indicators against conveyor speed. MAIN-3 uses the same evidential logic but isolates the active peak-temperature constraint instead of displaying every indicator with equal visual weight.
4. **Question 4 is multi-objective in substance.** The external summary explicitly combines area and symmetry. This agrees with MAIN-5's area–asymmetry envelope and the mirrored heating/cooling branches.
5. **Sensitivity is potentially relevant but secondary.** Public work includes sensitivity analysis. The blind plan already reserves a local temperature–speed contour as supporting evidence and refuses to let it stand in for a global optimality proof.

## OUR PLAN BETTER

1. **Active-constraint focus in Question 2.** A single peak-temperature-versus-speed curve communicates the limiting mechanism more directly than a crowded multi-indicator plot; the remaining constraints are reported numerically.
2. **Decision and shape are separated but paired in Question 4.** The left panel explains why the selected solution is acceptable in objective space; the right panel shows what improved symmetry means in the time domain. A generic optimized curve alone cannot do both jobs.
3. **Residual evidence is explicit.** The public fit example mainly communicates overlap. MAIN-1 prevents fit quality from being inferred solely from two visually coincident lines.
4. **Redundant software-output graphics are deleted.** Convergence traces, 3D surfaces, settings bar charts, and duplicate time/position profiles are excluded unless they answer a distinct claim.
5. **Claim limits are embedded in the captions.** Fit is described as calibration adequacy, not parameter identifiability; local scans and search results are not presented as global proofs.

## EXTERNAL PLAN BETTER

1. **Broader parameter sensitivity can be useful when operational robustness is the paper's emphasis.** The public solution's explicit sensitivity figure may reveal which temperature-zone errors dominate. Our blind plan includes only a local two-parameter supporting contour, so a full sensitivity treatment could be stronger in a reliability-focused paper.
2. **No change is made to the frozen blind plan.** The missing breadth is not a hard evidential gap for the stated five-figure main narrative, because feasibility margins and model limitations remain numerically reported. It is a legitimate supporting-analysis extension, not a replacement MAIN figure.

## DIFFERENT BUT DEFENSIBLE

1. **MAIN-2 overlays furnace-air forcing with PCB-center temperature.** Many external examples show only the center-temperature curve. The overlay is defensible here because it explains lag and connects the spatial oven setting to the transient response; the forcing line is visually subordinated.
2. **MAIN-3 plots only the limiting indicator.** External work may place several indicators against speed in one graph. The blind plan instead uses a focused plot plus a compact constraint table; both are scientifically valid, but the latter has clearer hierarchy.
3. **MAIN-5 uses an area–asymmetry evidence map rather than only a symmetry curve.** This is a stricter decision-oriented presentation. It is valid only if the feasible sample is sufficiently dense; production therefore retains the audit gate against a fabricated smooth frontier.

## Cross-check verdict

The independently selected graph architecture is consistent with the dominant external evidence chain and is more selective about hierarchy, redundancy, and claim scope. No external reference exposes a missing MAIN conclusion. The frozen plan therefore remains unchanged.

`EXTERNAL_CROSS_CHECK_RESULT = CONFIRMED_WITH_ONE_SUPPORTING_EXTENSION`
