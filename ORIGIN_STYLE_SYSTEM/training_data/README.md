# Training records

Store one review record per generated figure or review round. Required fields: figure ID, data source, GRAPH INTENT, template/theme, exports, score breakdown, three highest-value changes, transformations/disclosures, and human decision.

Human feedback takes priority over automated scores. Preserve rejected records and update the style guide through explicit versioned changes.

Second-round reproducibility records:

- `origin_round2.py`: live Origin MCP renderer, exporter, and v02 template saver.
- `round2_mcp_execution.json`: graph creation, styling, annotation, export, and OPJU-save results.
- `round2_template_save.json`: v02 user-template registration results.
- `round2_labtalk_audit.json`: compatibility audit that isolated one unsupported page-color assignment; the final renderer uses only the verified property sequence.

Frozen v1.1 reproducibility records:

- `origin_v11.py`: Origin MCP micro-refinement renderer, exporter, and frozen-template saver.
- `v11_mcp_execution.json`: live Origin connection, graph construction, styling, annotations, exports, and source-project save results.
- `v11_template_save.json`: successful registration record for the four `v11_FROZEN` templates.
- `../V1_1_MICRO_REFINEMENT_REVIEW.md`: six-dimension final visual review and freeze decision.
- `../FROZEN_MANIFEST_V1_1.json`: SHA-256 integrity manifest for frozen outputs and templates.

Phase 2 reproducibility records:

- `origin_phase2.py`: Origin MCP renderer, stress-test adapter, exporter, and candidate-template saver for five new graph classes.
- `phase2_mcp_execution.json`: 11 graph builds, annotations, adaptations, exports, and OPJU save result.
- `phase2_graph_inspection.json`: post-render graph-object inspection.
- `phase2_template_save.json`: five `v20_CANDIDATE` template registration results.
- `../PHASE2_STYLE_REVIEW.md`: cross-figure visual review and `TEMPLATE_ADAPTATION_REQUIRED` decisions.
- `../PHASE2_MANIFEST.json`: export and template integrity summary.
