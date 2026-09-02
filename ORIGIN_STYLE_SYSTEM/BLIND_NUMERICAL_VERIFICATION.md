# BLIND NUMERICAL VERIFICATION

## Why this audit exists

After the graph plan and reverse audit were frozen, preparation of the Question 4 evidence map exposed a numerical-integrity issue: the initial heuristic Q3/Q4 selections were mildly dominated by newly sampled feasible designs. The graph choices were not changed. The result package was corrected before any MAIN figure was drawn.

## Verification procedure

- Generated 2,502 deterministic candidates around the initial Q3/Q4 solutions, along their connecting region, and across the official bounds.
- Used a coarse pass only for screening.
- Re-simulated every coarse-feasible candidate at `dt = 0.05 s`.
- Enforced the official slope, duration, peak-temperature, setting, and speed inequalities without a display tolerance.
- Retained 853 strictly feasible candidates.
- Promoted the lowest-area verified candidate for Q3.
- Promoted the lowest-asymmetry verified candidate satisfying `area <= 1.05 × corrected Q3 area` for Q4.

## Corrected selections

| Result | Initial | Strictly verified selection | Change |
|---|---:|---:|---:|
| Q3 area above 217°C before the peak (°C·s) | 420.973 | 419.599 | −1.374 |
| Q4 asymmetry metric (°C) | 1.621 | 1.604 | −0.017 |
| Q4 area (°C·s) | 423.971 | 422.621 | −1.350 |
| Q4 area cap (°C·s) | 442.021 | 440.579 | corrected from Q3 |

Corrected Q3 setting: `[172.118, 189.123, 229.005, 265.000] °C`, speed `88.918 cm/min`.

Corrected Q4 setting: `[167.447, 185.000, 225.000, 265.000] °C`, speed `85.550 cm/min`.

Both corrected profiles satisfy every adopted process constraint at the verification resolution. They remain **best found within the adopted model and deterministic search sample**, not globally proven optima.

## Isolation impact

`BLIND_GRAPH_EDITOR_ANALYSIS.md` and `BLIND_FIGURE_STORYBOARD.md` remain untouched as the time-stamped blind decisions. Only their numerical examples are superseded by this scientific-correction record. The Claim → Evidence → Figure mapping, main/supporting hierarchy, tool choice, and template choice are unchanged.

`NUMERICAL_VERIFICATION_RESULT = CORRECTED_BEFORE_PLOTTING`
