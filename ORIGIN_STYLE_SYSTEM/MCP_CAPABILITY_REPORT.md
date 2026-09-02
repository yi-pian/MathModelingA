# Origin MCP Capability Report

Audit date: 2026-08-30 (Asia/Shanghai)

## Runtime audit result

- Configured server: `origin_mcp` 0.1.4.
- Origin runtime: Origin 2026 / bridge-reported Origin version 10.350229.
- Live bridge: connected, visible, and responsive.
- Tool profile: compact by default, 25 registered MCP tools; server reports 118 tools in the standard/legacy profile.
- Initial failure found and repaired: the dedicated environment contained MCP SDK 2.1.1, while `origin_mcp` imports the MCP 1.x `FastMCP` API. The dedicated environment was pinned back to MCP 1.29.1, after which tool enumeration and live Origin ping succeeded.

## Directly available compact tools

The 25 verified registered tools are:

`origin_run_analysis`, `origin_ping`, `origin_capabilities`, `origin_bridge_shutdown`, `origin_doctor`, `origin_bridge_submit_task`, `origin_bridge_task_status`, `origin_bridge_cancel_task`, `origin_bridge_list_tasks`, `origin_plan_figure_spec`, `origin_execute_figure_spec`, `origin_get_graph_info`, `origin_export_graph`, `origin_view_graph`, `origin_format_graph`, `origin_browse_knowledge`, `origin_query_knowledge`, `origin_run_labtalk`, `origin_plot`, `origin_recommend_chart`, `origin_plot_auto`, `origin_import_table`, `origin_read_worksheet`, `origin_write_worksheet`, `origin_diagnose_worksheet`.

## Operations verified by tool/schema or live bridge capability response

- Connect to and inspect Origin/OriginPro.
- Import CSV, TSV, TXT, DAT, XLS, and XLSX tables.
- Read, write, and diagnose worksheets.
- Recommend and create plots, including line/scatter/table-based plotting and chart-atlas routes.
- Plan and execute figure specifications.
- Get graph/layer information and render previews.
- Format graph pages, layers, axes, legends, labels, and plot properties through dedicated formatting endpoints or bridge methods.
- Run selected Origin analyses and inspect results.
- Export individual graphs and all graphs.
- Save graph templates through the standard-profile `origin_save_graph_template` tool.
- List/search/rename/delete/update metadata for user graph templates in the standard profile.
- Save/open Origin projects through allowlisted bridge methods (`save_project`, `open_project`).
- Execute LabTalk through `origin_run_labtalk` for supported indirect Origin operations.

## Directly settable graph properties

The registered standard profile exposes dedicated endpoints for:

- Graph page formatting and page size.
- Axis scale, range, ticks, titles, and axis breaks.
- Plot style and individual plot properties.
- Legend formatting.
- Graph labels, reference lines, uncertainty bands, and inset layers.
- Adding/removing plots, changing plot data/type, arranging/merging/linking layers.
- Template saving and graph export.

Exact property names remain runtime-dependent. They must be queried through style-capability tools or tested against the live graph; unsupported properties must not be guessed.

## Indirect operations

- `origin_run_labtalk` is the verified escape hatch for documented LabTalk operations that lack a dedicated tool.
- Project saving can also be submitted through the bridge task interface because `save_project` is allowlisted by the live bridge.
- Existing Theme application may be selected by plotting style modes or performed through documented Origin commands. No dedicated compact or standard MCP tool named create/save Theme was found.

## Template capability

- Verified standard tools: save graph template, search templates, list user templates, rename template, delete template, and update template metadata.
- Reuse can occur through plotting/template routes and batch plotting from a template.
- Template files must be checked on disk before being recorded as available.

## Theme capability

- Cross-graph styling is supported through MCP formatting, named palettes, nature/style profiles, and Origin template reuse.
- No dedicated `origin_save_theme` or `origin_create_theme` tool was enumerated.
- Therefore this phase does not promise a standalone Theme file unless a documented LabTalk route is successfully tested. A graph template is the required reusable artifact for round one.

## Data import capability

- Direct table import supports CSV/TSV/TXT/DAT/XLS/XLSX.
- Schema options include Excel sheet, delimiter, encoding, header, skipped rows, row limits, and additional missing-value markers.
- The bridge additionally reports connectors, refresh, CSV import, clone import, and matrix/image routes.

## Image export capability

- Direct graph export and preview rendering are registered.
- The bridge reports individual export, export-all, preview export, PNG rendering, and export inspection.
- Requested round-one targets are 600 dpi PNG, PDF, and SVG, subject to live exporter validation.

## Origin project saving

- The live bridge explicitly allowlists `save_project` and `open_project`.
- A saved `.opju` is only considered complete after a non-zero file is verified in `outputs/`.

## Known limitations and non-claims

- The current Codex task started before the dependency repair, so its static tool inventory did not automatically gain named Origin tools. Calls in this phase are made through an MCP SDK client against the repaired configured server and live Origin bridge.
- There is no verified dedicated Theme-creation API.
- The MCP cannot make an arbitrary visual choice scientifically correct; data semantics, axis honesty, and annotation still require review.
- Unsupported Origin object-tree properties may require LabTalk and must be tested rather than invented.
- Complex geometric schematics and specialized trajectory illustrations remain Python-first under the team policy.

