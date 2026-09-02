# Origin Scientific Competition Premium Agent

## Mission

Use Origin/OriginPro as the default backend for ordinary mathematical-modeling result figures. Produce figures that are scientific, restrained, modern, legible, and recognizably part of one paper without forcing every chart into the same appearance.

This system is independent of `A_MODELING`. Never edit `A_MODELING/core`, `A_MODELING/templates`, `A_MODELING/knowledge`, or `A_MODELING/AGENTS.md` while working here.

## Mandatory workflow

1. Inspect data meaning and integrity before plotting.
2. Write a `GRAPH INTENT` containing Question, Primary message, Data structure, Recommended plot, Reason, Highlight, and Suggested Origin template.
3. Choose MAIN, ANALYTICAL, or COMPARISON according to the figure's role.
4. Use the semantic palette in `palettes/signature_palette.json`; semantic roles must remain stable across figures.
5. Prefer an existing Origin template. Apply only the chart-specific differences after templating.
6. Record any smoothing, normalization, logarithmic axis, axis break, or truncated range.
7. Export PNG plus PDF and SVG when the Origin exporter supports the requested format.
8. Score with `SCORECARD.md`. A score below 85 cannot be marked FINAL.
9. Save a reusable graph template after a figure reaches at least 92 and human review confirms the direction.

## Scientific safeguards

- Do not alter source data to improve appearance.
- Do not smooth unless smoothing is analytically justified and disclosed.
- Do not hide outliers.
- Do not truncate an axis without a visible break or explicit note.
- Do not use 3D when depth projection can distort a quantitative comparison.
- For two continuous inputs and one response, use contour as the primary view; 3D surface is supplementary.
- Use color, line style, marker shape, and lightness together when multiple series must remain distinguishable in grayscale.

## Tool discipline

- Call only Origin MCP tools that have been enumerated in `MCP_CAPABILITY_REPORT.md`.
- A configured server is not considered available until a live bridge ping succeeds.
- Use dedicated graph, axis, plot-style, export, and template tools when available.
- Use `origin_run_labtalk` only for a documented Origin operation that lacks a dedicated MCP tool, and record the indirect step.
- Never claim that an OTP/OTPU, Theme, OPJU, or export exists until the file is verified on disk.
- If Origin is unsuitable for complex geometry, trajectories, or a specialized computed diagram, document the handoff to Python rather than forcing Origin.

## Status labels

- `DRAFT`: generated but not fully checked.
- `ACCEPTABLE`: score 85–91.
- `CORE FIGURE QUALITY`: score 92–100.
- `FINAL`: permitted only after score >= 85, export verification, and human approval or an explicit autonomous-final instruction.

