# Signature Scientific Style v1.1 — Style Guide

Status: **SIGNATURE SCIENTIFIC STYLE V1.1 — FROZEN**.

Fixed character: **clean · restrained · publication-grade · analytical · premium**.

## 1. Visual character

The system should feel academic, contemporary, quiet, hierarchical, and publication-ready. White space and contrast carry the hierarchy. Decoration does not.

Default prohibitions: rainbow palettes, saturated multi-hue defaults, gradient backgrounds, shadows, glow, 3D bars, oversized titles, very thick strokes, Excel defaults, commercial-slide styling, AI-infographic styling, and ornamental icons.

## 2. Semantic color language

The canonical machine-readable values are in `palettes/signature_palette.json`.

| Role | Hex | Visual role | Use | Avoid |
|---|---:|---|---|---|
| Primary | `#1F4E79` | Deep navy; strongest stable signal | final solution, main model, central curve | using for every series |
| Secondary | `#76A3B5` | Light muted blue-teal | secondary method or response | competing visually with Primary |
| Highlight | `#C97B2A` | Restrained amber; focal event | optimum, critical point, selected threshold | large filled areas or routine series |
| Neutral | `#969AA0` | Light neutral gray | baseline, reference, auxiliary context | important conclusions |
| Green Accent | `#5D8D7C` | Low-saturation green | supplementary comparison method | using as a positive/negative judgment by itself |
| Purple | `#917EA3` | Muted purple; conditional extension | fourth analytical response only when needed | routine use in small series sets |
| Warning | `#A63D40` | Muted dark red; adverse state | constraint violation, failure, negative exception | ordinary comparison series |

Purple is not part of the default three-series comparison. It is retained only when a fourth analytical response cannot be encoded clearly with the Primary, Secondary, Green Accent, and Neutral roles. Never assign Warning red merely to make a palette more colorful.

Color checks:

- The conclusion must remain understandable in grayscale.
- Primary and Highlight must differ in lightness as well as hue.
- Baseline is Neutral and visually subordinate.
- Do not rely on red–green opposition alone.
- Filled color fields use the v1 low-saturation sequence `#244B66 → #2F667F → #3F8393 → #58A09F → #78B79F → #9AC996 → #BAD88E → #D6E38C → #E8E99B → #F2ECB1`. It is ordered dark blue through cyan/green to light yellow, with no purple endpoint.

## 3. Figure sizes and aspect ratios

Use physical dimensions, not arbitrary screen pixels.

| Use | Width | Typical height | Aspect |
|---|---:|---:|---:|
| Single-column compact | 85 mm | 55–65 mm | 1.31–1.55 |
| Single-column standard | 85 mm | 70 mm | 1.21 |
| Double-column standard | 178 mm | 105–120 mm | 1.48–1.70 |
| Standalone benchmark | 120 mm | 80 mm | 1.50 |
| Two-panel horizontal | 178 mm | 78–90 mm | 1.98–2.28 |

The benchmark canvas remains 120 × 80 mm so round-to-round changes are directly comparable. Multi-panel pages should be designed at final publication size.

## 4. Typography

- Default family: Arial. Fallback: Helvetica, then a neutral sans-serif.
- Mathematical symbols: Origin's Unicode/math text or a consistent serif math face where required.
- Axis title: 6.5 pt, regular.
- Tick labels: 5.8–6.0 pt.
- Legend, only when unavoidable: 5.0–5.5 pt.
- Direct curve labels: 4.8–5.2 pt; use the curve's semantic color.
- Small point annotation: 4.2–4.8 pt.
- Panel labels `(a)`, `(b)`, `(c)`: 9 pt bold, placed consistently at the upper-left outside or just inside the plotting region.
- Figure title: normally omitted inside a manuscript figure. If required for a standalone diagnostic, 9 pt semibold and left aligned.
- Avoid all caps except short technical abbreviations.

## 5. Axes and ticks

- Axis line: 0.45 pt, near-black `#2B2F33`.
- Major ticks: outward, about 2.0 pt long, 0.45 pt wide.
- Minor ticks: outward, about 1.2 pt long, 0.35 pt wide; use only when they aid reading.
- Contour benchmark exception: 1.2 pt / 0.28 pt major ticks and 0.7 pt / 0.22 pt minor ticks, matching the lighter visual weight of the line-plot family.
- Top and right axes: off by default. Turn on only for framed heatmaps/contours or paired axes where the frame improves registration.
- Begin count and magnitude comparisons at zero when zero is meaningful. Otherwise choose an honest range with 3–7% breathing room.
- Use at most 5–7 labeled major ticks per axis.
- An axis break requires a visible break mark and a note in the recipe/review.

## 6. Lines, symbols, and areas

- Primary line: 1.45–1.50 pt solid; the frozen MAIN SINGLE LINE mother template uses 1.36 pt after v1.1 micro-refinement.
- Secondary line: 0.85–0.90 pt with a clear dash pattern.
- Neutral baseline: 0.75 pt dashed.
- Warning/constraint: 0.90–1.10 pt dash-dot.
- Highlight marker: 3.05 pt in the frozen MAIN SINGLE LINE mother template; increase only when the final physical size demands it.
- Marker interval: reduce marker density so symbols do not form a second line.
- Confidence/uncertainty band: 15–22% opacity with no heavy outline.
- Avoid smoothing splines unless the mathematics or method explicitly supports interpolation.

## 7. Legends and direct labels

- Prefer direct labels for stable endpoints, including four-curve analytical comparisons when spacing permits.
- Direct labels may use different x positions and do not need to sit at the final sample. Collision-free identification takes precedence over endpoint uniformity.
- Otherwise use a frameless legend, ordered by rhetorical importance rather than worksheet order.
- Default placement: unused interior corner; next choice is above the plotting area in one row; outside-right only when width permits.
- Legend samples must show both line and marker encoding.
- Do not repeat units in every legend item when the axis already carries them.

## 8. Grid lines

- No grid by default for sparse line/scatter plots.
- Sensitivity analysis uses one analytical `y=0` rule in `#C6CBD1`, about 0.45 pt. It is not treated as a decorative grid.
- Never show dense major and minor grids simultaneously.
- Heatmaps and contours use no Cartesian grid over the color field.

## 9. Annotation

- Annotate only the result that changes interpretation: optimum, threshold, baseline, or critical transition.
- Highlight point: amber marker with a short neutral leader.
- Annotation text must state a value or scientific meaning, not merely “important”.
- Keep labels away from data; use concise wording and consistent alignment.
- Maximum routine annotation count: three per single-panel figure.

## 10. Numbers, notation, and units

- Use 2–4 significant digits according to measurement precision.
- Percentages: normally one decimal place; use integers only when the data precision supports it.
- Scientific notation: use a common axis multiplier such as `×10^−3`, not repeated `E-3` labels.
- Put units in parentheses: `Time (h)`, `Temperature (°C)`, `Cost (10³ CNY)`.
- Dimensionless quantities: state `(dimensionless)` only when ambiguity is likely; otherwise use the symbol alone.
- Variables are italic where Origin formatting supports it; units and descriptors remain upright.

## 11. White space and layout

- Benchmark layer rectangle: approximately 77% of page width × 69% of page height for line plots; 56% × 69% for contour plots plus color scale. This increases effective data area by about 9% over round one without clipping titles.
- Left margin must accommodate the full y-axis title without crowding.
- Keep 4–6 mm visual padding around a standalone plot.
- Multi-panel horizontal gap: 5–8 mm; vertical gap: 6–9 mm.
- Align plot rectangles, not outer text boxes.
- Shared axes should share limits and tick locations; suppress repeated interior labels only when unambiguous.

## 12. Chart-specific defaults

- Single line: one Primary curve, optional Highlight point, no legend if the axis/title makes identity clear.
- Multi-line: baseline Neutral; proposed Primary; alternatives Secondary and Green Accent. Use line-end labels before considering a legend.
- Sensitivity: zero-reference line Neutral; parameters ordered by effect magnitude when categories are discrete. For continuous perturbation curves, emphasize the most influential parameter.
- Contour: for a continuous response surface use 16–20 filled levels and about 6–8 visible contour lines. The frozen benchmark uses 19 filled levels, 7 contour lines, 7 colorbar major ticks, the v1 blue–cyan–green–light-yellow sequence, a narrow labeled colorbar, and an optimum marker in Highlight.
- Heatmap: color bar with units, missing values explicitly encoded, no interpolation that invents values.
- 3D surface: supplementary; use moderate camera elevation, orthographic-like view when available, and a paired contour for exact reading.

## 13. Export contract

- PNG: 600 dpi for line art and mixed figures; transparent background off unless publication requires it.
- PDF: vector export with fonts embedded or converted consistently.
- SVG: editable vector text where Origin supports it.
- Keep an Origin project (`.opju`) for source traceability.
- Verify file existence, dimensions, and non-zero size after every export.
- Do not upscale a low-resolution raster after export.

## 14. Versioning

Version history:

- `v0.1 / Scientific Competition Premium`: pre-feedback baseline.
- `v1 / Signature Scientific Style`: smaller typography, 0.45 pt frame language, larger plot area, direct labels, explicit sensitivity zero rule, role-muted comparison curves, and a custom unified contour/colorbar system.
- `v1.1 / Signature Scientific Style — FROZEN`: collision-safe staggered direct labels, small sensitivity headroom, lighter contour ticks, a narrower lower-weight colorbar, 19-level continuous fill with 7 visible contour lines, and a tighter optimum annotation relationship.

The four v1.1 mother templates are frozen. Do not continue aesthetic iteration unless real competition data exposes a new readability, scientific-accuracy, or layout problem. Any justified change must create a new version and review record; never overwrite v1.1 silently.
