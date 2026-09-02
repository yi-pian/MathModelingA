"""Phase 2 Origin MCP renderer for new Signature Scientific Style candidates.

The four v1.1 FROZEN templates are never loaded for overwrite or modification.
Python is used only for deterministic data transport and MCP orchestration; every
figure, preview, and export is produced by Origin.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import math
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import origin_round2 as r2
import origin_v11 as v11


SYSTEM_ROOT = r2.SYSTEM_ROOT
BENCH = r2.BENCH
OUTPUT = r2.base.OUTPUT / "phase2"
LOG_DIR = r2.LOG_DIR
PYTHON_EXE = r2.PYTHON_EXE

PRIMARY = r2.PRIMARY
HIGHLIGHT = r2.HIGHLIGHT
SECONDARY = r2.SECONDARY
GREEN = r2.GREEN
NEUTRAL = r2.NEUTRAL
INK = [43, 47, 51]
PALETTE = v11.CONTOUR_COLORS_19


def graph_name(result: dict[str, Any]) -> str:
    name = r2.base.find_key(result, "graph_name")
    if not isinstance(name, str) or not name:
        raise RuntimeError(f"Origin result has no graph name: {result}")
    return name


def worksheet_ref(result: dict[str, Any]) -> str:
    worksheet = r2.base.find_key(result, "worksheet")
    if not isinstance(worksheet, dict):
        raise RuntimeError(f"Origin result has no worksheet: {result}")
    return f"[{worksheet['book_name']}]{worksheet['sheet_name']}"


def rgb(rgb_value: list[int]) -> str:
    return r2.rgb_expr(rgb_value)


def safe_direct_label(
    graph: str,
    name: str,
    text_value: str,
    x: float,
    y: float,
    color: list[int],
    *,
    size: float = 4.7,
    rotate: int = 0,
    layer_index: int = 1,
) -> str:
    quoted_text = text_value.replace('"', '\\"')
    return (
        f'win -a "{graph}"; layer -s {layer_index}; '
        f"double p2lx={x}; double p2ly={y}; "
        f'label -a p2lx p2ly -n {name} "{quoted_text}"; '
        f"{name}.font=font(Arial); {name}.fsize={size}; "
        f"{name}.color={rgb(color)}; {name}.rotate={rotate}; "
        f"{name}.background=0; {name}.clip=0; doc -uw; sec -p 0.05;"
    )


async def run_script(session: ClientSession, script: str) -> dict[str, Any]:
    return await r2.base.call(session, "origin_run_labtalk", {"script": script})


async def standard_2d(
    session: ClientSession,
    graph: str,
    *,
    frame: bool = False,
    field: bool = False,
    page_width_mm: float = 120,
    page_height_mm: float = 80,
) -> dict[str, Any]:
    # Use the same pixel-canvas normalization as the frozen v1.1 workflow.
    # Changing an Origin page directly to millimetres can preserve template
    # object pixel sizes and produce severely oversized labels.
    page = await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "contour" if field else "line",
            "page_width": 1800,
            "page_height": 1200,
            "font_family": "Arial",
            "axis_title_size": 7,
            "tick_label_size": 6,
            "legend_font_size": 5,
            "line_width": 1.0,
            "symbol_size": 3.0,
            "tick_length": 2,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    geometry = {
        "layer_index": 0,
        "left": 17,
        "top": 6,
        "width": 56 if field else 77,
        "height": 69,
    }
    arranged = await r2.base.call(
        session,
        "origin_arrange_layers",
        {"graph_name": graph, "rows": 1, "columns": 1, "layer_geometries": [geometry]},
    )
    formatted = await r2.base.call(
        session,
        "origin_format_graph",
        {"graph_name": graph, "show_legend": False, "rescale": False},
    )
    base = await run_script(session, r2.base_labtalk(graph, keep_frame=frame))
    return {"page": page, "arrange": arranged, "format": formatted, "base": base}


async def set_style(
    session: ClientSession,
    graph: str,
    index: int,
    **style: Any,
) -> dict[str, Any]:
    return await r2.base.call(
        session,
        "origin_set_plot_style",
        {"graph_name": graph, "layer_index": 0, "plot_index": index, **style},
    )


async def plot_count(session: ClientSession, graph: str) -> int:
    info = await r2.base.call(session, "origin_get_graph_info", {"graph_name": graph})
    plots = r2.base.find_key(info, "plots")
    if not isinstance(plots, list):
        raise RuntimeError(f"Origin graph info has no plot list: {info}")
    return len(plots)


async def set_axes(
    session: ClientSession,
    graph: str,
    x: tuple[float, float, float, str],
    y: tuple[float, float, float, str],
    *,
    y_scale: str | None = None,
) -> list[dict[str, Any]]:
    return [
        await r2.base.call(
            session,
            "origin_set_axis",
            {
                "graph_name": graph,
                "axis": "x",
                "start": x[0],
                "end": x[1],
                "step": x[2],
                "title": x[3],
            },
        ),
        await r2.base.call(
            session,
            "origin_set_axis",
            {
                "graph_name": graph,
                "axis": "y",
                "scale": y_scale,
                "start": y[0],
                "end": y[1],
                "step": y[2],
                "title": y[3],
            },
        ),
    ]


async def export_graph(
    session: ClientSession,
    graph: str,
    stem: str,
    *,
    width: int = 2400,
) -> list[dict[str, Any]]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for suffix in ("png", "pdf", "svg"):
        if suffix == "png":
            await run_script(session, "@MGI=1; @MGR=1; expGraph.DPI=600;")
        results.append(
            await r2.base.call(
                session,
                "origin_export_graph",
                {
                    "graph_name": graph,
                    "path": str(OUTPUT / f"{stem}.{suffix}"),
                    "overwrite": True,
                    "width": width if suffix == "png" else 0,
                },
            )
        )
    return results


def load_grid(path: Path, x_col: str, y_col: str, z_col: str) -> tuple[list[list[float]], list[float], list[float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    xs = sorted({float(row[x_col]) for row in rows})
    ys = sorted({float(row[y_col]) for row in rows})
    lookup = {(float(row[x_col]), float(row[y_col])): float(row[z_col]) for row in rows}
    matrix = [[lookup[(x, y)] for x in xs] for y in ys]
    return matrix, xs, ys


async def create_matrix_plot(
    session: ClientSession,
    *,
    data_path: Path,
    x_col: str,
    y_col: str,
    z_col: str,
    book_name: str,
    graph_request_name: str,
    plot_type_id: int,
    template: str,
) -> tuple[str, dict[str, Any], str]:
    matrix, xs, ys = load_grid(data_path, x_col, y_col, z_col)
    created = await r2.base.call(
        session,
        "origin_create_matrix",
        {
            "data": matrix,
            "book_name": book_name,
            "sheet_name": "Field",
            "xymap": [xs[0], xs[-1], ys[0], ys[-1]],
            "labels": [z_col],
        },
    )
    ranges = r2.base.find_key(created, "data_ranges")
    if not isinstance(ranges, list) or not ranges:
        raise RuntimeError(f"No Origin matrix range: {created}")
    matrix_info = r2.base.find_key(created, "matrix")
    if isinstance(matrix_info, dict):
        matrix_book = matrix_info.get("book_name")
        if isinstance(matrix_book, str) and matrix_book:
            # OpenGL 3D plots cache the matrix dimension labels when the graph
            # is created.  Set them before plotting so %(?X)/%(?Y)/%(?Z)
            # resolve to publication-ready English labels in the graph and in
            # any template saved from it.
            await run_script(
                session,
                (
                    f'win -a "{matrix_book}"; '
                    'wks.x.longname$="Decision variable x"; '
                    'wks.y.longname$="Decision variable y"; '
                    'wks.z.longname$="Objective value"; doc -uw;'
                ),
            )
    plotted = await r2.base.bridge_task(
        session,
        "plot_matrix_by_id",
        {
            "data_range": ranges[0],
            "plot_type_id": plot_type_id,
            "template": template,
            "graph_name": graph_request_name,
            "title": None,
        },
    )
    active = await r2.base.call(session, "origin_get_graph_info", {})
    return graph_name(active), {"matrix": created, "plot": plotted}, ranges[0]


def palette_script(
    graph: str,
    low: float,
    high: float,
    *,
    show_lines: int = 0,
) -> str:
    levels = [low + (high - low) * i / (len(PALETTE) - 1) for i in range(len(PALETTE))]
    parts = [
        f'win -a "{graph}"; layer -s 1;',
        f"layer.cmap.numColors={len(PALETTE)};",
    ]
    for i, (level, color) in enumerate(zip(levels, PALETTE), 1):
        parts.extend(
            [
                f"layer.cmap.z{i}={level};",
                f"layer.cmap.color{i}={rgb(color)};",
                f"layer.cmap.line{i}={1 if show_lines and i in {1, 4, 7, 10, 13, 16, 19} else 0};",
                f"layer.cmap.lineWidth{i}=0.20;",
                f"layer.cmap.label{i}=0;",
            ]
        )
    parts.extend(
        [
            f"layer.cmap.colorLow={rgb(PALETTE[0])};",
            f"layer.cmap.colorHigh={rgb(PALETTE[-1])};",
            "layer.cmap.colorAbove=layer.cmap.colorHigh;",
            "layer.cmap.colorBelow=layer.cmap.colorLow;",
            "layer.cmap.labelAbove=0; layer.cmap.lineAbove=0;",
            "layer.cmap.updateScale(); doc -uw; sec -p 0.1;",
        ]
    )
    return " ".join(parts)


async def style_colorbar(
    session: ClientSession,
    graph: str,
    *,
    low: float,
    high: float,
    increment: float,
    title: str,
    title_x: float,
    title_y: float,
) -> list[dict[str, Any]]:
    bar = await run_script(
        session,
        (
            f'win -a "{graph}"; '
            "Spectrum1.labels.autodisp=0; Spectrum1.labels.font=font(Arial);"
            "Spectrum1.labels.fsize=5.0; Spectrum1.labels.bold=0;"
            "Spectrum1.labels.color=color(94,100,106);"
            "Spectrum1.labels.formrange=0; Spectrum1.labels.numdisp=1;"
            "Spectrum1.labels.decplaces=0; Spectrum1.labels.rotate=0;"
            f"Spectrum1.levels.major=3; Spectrum1.levels.from={low};"
            f"Spectrum1.levels.to={high}; Spectrum1.levels.type=1;"
            f"Spectrum1.levels.inc=1; Spectrum1.levels.inc$={increment};"
            "Spectrum1.levels.minorticks=0; Spectrum1.title=0;"
            "Spectrum1.barthick=100; Spectrum1.lgap=23;"
            "Spectrum1.lineWidth=0.28; Spectrum1.color=color(118,124,130);"
            "Spectrum1.draw(global); doc -uw; sec -p 0.1;"
        ),
    )
    label = await run_script(
        session,
        safe_direct_label(
            graph,
            f"P2CB{abs(hash(graph)) % 100000}",
            title,
            title_x,
            title_y,
            [82, 88, 94],
            size=4.2,
            rotate=90,
        ),
    )
    return [bar, label]


async def render_scatter(session: ClientSession) -> list[dict[str, Any]]:
    path = BENCH / "phase2_scatter_fit.csv"
    created = await r2.base.call(
        session,
        "origin_plot_scatter",
        {
            "path": str(path), "x_col": "x", "y_cols": ["observed"],
            "graph_name": "P2_SCATTER_FIT", "show_legend": False,
        },
    )
    graph = graph_name(created)
    wref = worksheet_ref(created)
    await r2.base.call(
        session, "origin_add_plot_to_graph",
        {"worksheet": wref, "x_col": 0, "y_col": 4, "graph_name": graph, "plot_type": "l"},
    )
    outlier = await r2.base.call(
        session, "origin_import_table",
        {"path": str(BENCH / "phase2_scatter_outlier.csv"), "book_name": "P2_SCATTER_OUTLIER", "sheet_name": "Point"},
    )
    await r2.base.call(
        session, "origin_add_plot_to_graph",
        {"worksheet": worksheet_ref(outlier), "x_col": 0, "y_col": 1, "graph_name": graph, "plot_type": "s"},
    )
    await set_style(
        session, graph, 0, color=[103, 126, 142], line_width=0.18,
        symbol_kind=2, symbol_size=0.78, transparency=20,
    )
    await set_style(session, graph, 1, color=PRIMARY, line_width=0.68, line_style=0)
    await set_style(
        session, graph, 2, color=HIGHLIGHT, line_width=0.18,
        symbol_kind=2, symbol_size=1.25,
    )
    await set_axes(session, graph, (0, 10.8, 2, "Predictor x"), (0, 28, 5, "Observed response"))
    await standard_2d(session, graph)
    await set_style(
        session, graph, 0, color=[103, 126, 142], line_width=0.18,
        symbol_kind=2, symbol_size=0.78, transparency=20,
    )
    await set_style(session, graph, 1, color=PRIMARY, line_width=0.68, line_style=0)
    await set_style(
        session, graph, 2, color=HIGHLIGHT, line_width=0.18,
        symbol_kind=2, symbol_size=1.25,
    )
    labels = [
        safe_direct_label(graph, "P2Fit", "Model fit", 8.55, 22.2, PRIMARY),
        safe_direct_label(graph, "P2Outlier", "Outlier", 7.78, 19.35, HIGHLIGHT, size=4.2),
    ]
    for script in labels:
        await run_script(session, script)
    exports = await export_graph(session, graph, "P2_SCATTER_FIT")

    residual = await r2.base.call(
        session,
        "origin_plot_scatter",
        {
            "path": str(path), "x_col": "x", "y_cols": ["residual"],
            "graph_name": "P2_SCATTER_RESIDUAL", "show_legend": False,
        },
    )
    residual_graph = graph_name(residual)
    await set_style(
        session, residual_graph, 0, color=[103, 126, 142], line_width=0.25,
        symbol_kind=2, symbol_size=0.76, transparency=14,
    )
    residual_outlier = await r2.base.call(
        session, "origin_import_table",
        {"path": str(BENCH / "phase2_scatter_outlier.csv"), "book_name": "P2_RESIDUAL_OUTLIER", "sheet_name": "Point"},
    )
    await r2.base.call(
        session, "origin_add_plot_to_graph",
        {"worksheet": worksheet_ref(residual_outlier), "x_col": 0, "y_col": 2, "graph_name": residual_graph, "plot_type": "s"},
    )
    await set_style(
        session, residual_graph, 1, color=HIGHLIGHT, line_width=0.25,
        symbol_kind=2, symbol_size=1.25,
    )
    await set_axes(session, residual_graph, (0, 10.5, 2, "Predictor x"), (-2.5, 4.0, 1, "Residual"))
    await standard_2d(session, residual_graph)
    await set_style(
        session, residual_graph, 0, color=[103, 126, 142], line_width=0.18,
        symbol_kind=2, symbol_size=0.76, transparency=14,
    )
    await set_style(
        session, residual_graph, 1, color=HIGHLIGHT, line_width=0.20,
        symbol_kind=2, symbol_size=1.25,
    )
    await run_script(
        session,
        f'win -a "{residual_graph}"; layer -s 1; draw -n P2ResidualZero -l -h 0; '
        "P2ResidualZero.attach=2; P2ResidualZero.color=color(198,203,209);"
        "P2ResidualZero.lineWidth=0.45; P2ResidualZero.back=1; doc -uw;",
    )
    residual_exports = await export_graph(session, residual_graph, "P2_SCATTER_RESIDUAL")

    stress_path = BENCH / "phase2_scatter_stress.csv"
    stress = await r2.base.call(
        session,
        "origin_plot_scatter",
        {
            "path": str(stress_path),
            "x_col": "exposure_duration_with_extended_label_s",
            "y_cols": ["observed"],
            "graph_name": "P2_SCATTER_STRESS",
            "show_legend": False,
        },
    )
    stress_graph = graph_name(stress)
    stress_wref = worksheet_ref(stress)
    await r2.base.call(
        session,
        "origin_add_plot_to_graph",
        {
            "worksheet": stress_wref,
            "x_col": 0,
            "y_col": 2,
            "graph_name": stress_graph,
            "plot_type": "l",
        },
    )
    await set_style(
        session, stress_graph, 0, color=[103, 126, 142], line_width=0.18,
        symbol_kind=2, symbol_size=0.42, transparency=66,
    )
    stress_outlier = await r2.base.call(
        session, "origin_import_table",
        {"path": str(BENCH / "phase2_scatter_stress_outliers.csv"), "book_name": "P2_SCATTER_STRESS_OUTLIERS", "sheet_name": "Points"},
    )
    await r2.base.call(
        session, "origin_add_plot_to_graph",
        {"worksheet": worksheet_ref(stress_outlier), "x_col": 0, "y_col": 1, "graph_name": stress_graph, "plot_type": "s"},
    )
    await set_style(session, stress_graph, 1, color=PRIMARY, line_width=0.60, line_style=0)
    await set_style(
        session, stress_graph, 2, color=HIGHLIGHT, line_width=0.20,
        symbol_kind=2, symbol_size=1.05,
    )
    await set_axes(
        session,
        stress_graph,
        (0, 32.5, 5, "Exposure duration under repeated loading (s)"),
        (-2, 40, 7, "Observed response under dense sampling"),
    )
    await standard_2d(session, stress_graph)
    await set_style(
        session, stress_graph, 0, color=[103, 126, 142], line_width=0.18,
        symbol_kind=2, symbol_size=0.42, transparency=66,
    )
    await set_style(session, stress_graph, 1, color=PRIMARY, line_width=0.60, line_style=0)
    await set_style(
        session, stress_graph, 2, color=HIGHLIGHT, line_width=0.20,
        symbol_kind=2, symbol_size=1.05,
    )
    # Long-label stress adaptation: retain the full semantic title while
    # shrinking only this axis title enough to keep it inside the page.
    await run_script(
        session,
        f'win -a "{stress_graph}"; yl.fsize=5.2; yl.font=font(Arial); doc -uw;',
    )
    await run_script(session, safe_direct_label(stress_graph, "P2StressFit", "Model fit", 25.5, 32.0, PRIMARY))
    stress_exports = await export_graph(session, stress_graph, "P2_SCATTER_STRESS")
    return [
        {"id": "P2_SCATTER_FIT", "graph": graph, "created": created, "exports": exports},
        {"id": "P2_SCATTER_RESIDUAL", "graph": residual_graph, "created": residual, "exports": residual_exports},
        {
            "id": "P2_SCATTER_STRESS", "graph": stress_graph, "created": stress,
            "exports": stress_exports, "adaptation": "TEMPLATE_ADAPTATION_REQUIRED",
        },
    ]


async def render_heatmap_one(
    session: ClientSession,
    *,
    data_path: Path,
    x_col: str,
    y_col: str,
    z_col: str,
    graph_request: str,
    stem: str,
    x_axis: tuple[float, float, float, str],
    y_axis: tuple[float, float, float, str],
    z_limits: tuple[float, float, float],
    adaptation: bool,
) -> dict[str, Any]:
    graph, created, _ = await create_matrix_plot(
        session,
        data_path=data_path,
        x_col=x_col,
        y_col=y_col,
        z_col=z_col,
        book_name=f"{graph_request}_FIELD",
        graph_request_name=graph_request,
        # A filled matrix contour with all contour strokes suppressed gives
        # the continuous-field heatmap semantics while retaining the vertical
        # publication color scale used by the frozen contour family.
        plot_type_id=226,
        template="contour",
    )
    await set_style(
        session,
        graph,
        0,
        colormap="BlueGreenYellow",
        color_scale_limits=[z_limits[0], z_limits[1]],
        transparency=0,
    )
    await set_axes(session, graph, x_axis, y_axis)
    await standard_2d(session, graph, frame=True, field=True)
    levels = [z_limits[0] + (z_limits[1] - z_limits[0]) * i / 18 for i in range(19)]
    await set_style(
        session, graph, 0, colormap="BlueGreenYellow",
        contour_levels=levels, contour_minor_levels=0,
        color_scale_limits=[z_limits[0], z_limits[1]], transparency=0,
    )
    await run_script(session, palette_script(graph, z_limits[0], z_limits[1], show_lines=0))
    # Recreate the associated scale after page normalization.  This forces a
    # vertical publication color scale even when Origin's automatic placement
    # chooses a horizontal bar for a long-axis stress case.
    await run_script(session, f'win -a "{graph}"; label -r Spectrum1; spectrum; doc -uw; sec -p 0.1;')
    await style_colorbar(
        session,
        graph,
        low=z_limits[0],
        high=z_limits[1],
        increment=z_limits[2],
        title="Temperature (C)",
        title_x=x_axis[1] + 0.31 * (x_axis[1] - x_axis[0]),
        title_y=(y_axis[0] + y_axis[1]) / 2,
    )
    exports = await export_graph(session, graph, stem)
    return {
        "id": stem,
        "graph": graph,
        "created": created,
        "exports": exports,
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_heatmaps(session: ClientSession) -> list[dict[str, Any]]:
    standard = await render_heatmap_one(
        session,
        data_path=BENCH / "spatiotemporal_temperature.csv",
        x_col="position_m",
        y_col="time_s",
        z_col="temperature_c",
        graph_request="P2_HEATMAP",
        stem="P2_HEATMAP",
        x_axis=(0, 1, 0.2, "Position x (m)"),
        y_axis=(0, 10, 2, "Time t (s)"),
        z_limits=(20, 60, 10),
        adaptation=False,
    )
    stress = await render_heatmap_one(
        session,
        data_path=BENCH / "phase2_heatmap_stress.csv",
        x_col="position_along_extended_domain_m",
        y_col="elapsed_heating_time_s",
        z_col="temperature_c",
        graph_request="P2_HEATMAP_STRESS",
        stem="P2_HEATMAP_STRESS",
        x_axis=(0, 6, 1, "Position along extended domain (m)"),
        y_axis=(0, 180, 30, "Elapsed heating time (s)"),
        z_limits=(20, 120, 20),
        adaptation=True,
    )
    return [standard, stress]


async def render_convergence_one(
    session: ClientSession,
    *,
    path: Path,
    graph_request: str,
    stem: str,
    x_axis: tuple[float, float, float, str],
    y_axis: tuple[float, float, float, str],
    log_y: bool,
    label_positions: tuple[tuple[float, float], tuple[float, float]],
    adaptation: bool,
) -> dict[str, Any]:
    mean_col = "log10_population_mean" if adaptation else "population_mean"
    best_col = "log10_best_objective" if adaptation else "best_objective"
    created = await r2.base.call(
        session,
        "origin_plot_line",
        {
            "path": str(path),
            "x_col": "iteration",
            "y_cols": [mean_col, best_col],
            "graph_name": graph_request,
            "show_legend": False,
        },
    )
    graph = graph_name(created)
    final_path = BENCH / ("phase2_convergence_stress_final.csv" if adaptation else "phase2_convergence_final.csv")
    final_point = await r2.base.call(
        session, "origin_import_table",
        {"path": str(final_path), "book_name": f"{graph_request}_FINAL", "sheet_name": "Point"},
    )
    await r2.base.call(
        session,
        "origin_add_plot_to_graph",
        {
            "worksheet": worksheet_ref(final_point),
            "x_col": 0,
            "y_col": 1,
            "graph_name": graph,
            "plot_type": "s",
        },
    )
    await set_style(session, graph, 0, color=SECONDARY, line_width=0.85, line_style=1)
    await set_style(session, graph, 1, color=PRIMARY, line_width=1.50, line_style=0)
    await set_style(
        session, graph, 2, color=HIGHLIGHT, line_width=0.25,
        symbol_kind=2, symbol_size=3.0,
    )
    await set_axes(session, graph, x_axis, y_axis)
    await standard_2d(session, graph)
    await set_style(session, graph, 0, color=SECONDARY, line_width=0.85, line_style=1)
    await set_style(session, graph, 1, color=PRIMARY, line_width=1.50, line_style=0)
    await set_style(
        session, graph, 2, color=HIGHLIGHT, line_width=0.20,
        symbol_kind=2, symbol_size=1.20,
    )
    await run_script(
        session,
        safe_direct_label(
            graph, f"{graph_request}Best", "Best objective",
            label_positions[0][0], label_positions[0][1], PRIMARY,
        ),
    )
    await run_script(
        session,
        safe_direct_label(
            graph, f"{graph_request}Mean", "Population mean",
            label_positions[1][0], label_positions[1][1], SECONDARY,
        ),
    )
    exports = await export_graph(session, graph, stem)
    return {
        "id": stem,
        "graph": graph,
        "created": created,
        "exports": exports,
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_convergence(session: ClientSession) -> list[dict[str, Any]]:
    standard = await render_convergence_one(
        session,
        path=BENCH / "phase2_convergence.csv",
        graph_request="P2_CONVERGENCE",
        stem="P2_CONVERGENCE",
        x_axis=(0, 132, 20, "Iteration"),
        y_axis=(0, 1.05, 0.2, "Objective gap"),
        log_y=False,
        label_positions=((86, 0.080), (66, 0.145)),
        adaptation=False,
    )
    stress = await render_convergence_one(
        session,
        path=BENCH / "phase2_convergence_stress.csv",
        graph_request="P2_CONVERGENCE_STRESS",
        stem="P2_CONVERGENCE_STRESS",
        x_axis=(0, 2120, 400, "Iteration"),
        y_axis=(-3.5, 3.5, 1, "log10 objective gap"),
        log_y=False,
        label_positions=((1510, -2.75), (1270, -2.10)),
        adaptation=True,
    )
    return [standard, stress]


async def render_panel_source(
    session: ClientSession,
    *,
    path: Path,
    graph_request: str,
    x_col: str,
    observed_col: str,
    model_col: str,
    y_label: str,
    show_shared_legend: bool,
    log_y: bool = False,
) -> str:
    created = await r2.base.call(
        session,
        "origin_plot_line",
        {
            "path": str(path),
            "x_col": x_col,
            "y_cols": [observed_col, model_col],
            "graph_name": graph_request,
            "show_legend": False,
        },
    )
    graph = graph_name(created)
    await set_style(session, graph, 0, color=PRIMARY, line_width=1.15, line_style=0)
    await set_style(session, graph, 1, color=SECONDARY, line_width=0.80, line_style=1)
    await r2.base.call(
        session,
        "origin_format_graph",
        {"graph_name": graph, "x_label": "", "y_label": y_label, "show_legend": False},
    )
    await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "line",
            "page_width": 1200,
            "page_height": 780,
            "font_family": "Arial",
            "axis_title_size": 6,
            "tick_label_size": 5,
            "legend_font_size": 4,
            "line_width": 0.9,
            "symbol_size": 2.5,
            "tick_length": 1.5,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    await r2.base.call(
        session,
        "origin_arrange_layers",
        {
            "graph_name": graph,
            "rows": 1,
            "columns": 1,
            "layer_geometries": [{"layer_index": 0, "left": 19, "top": 7, "width": 75, "height": 72}],
        },
    )
    await run_script(session, r2.base_labtalk(graph))
    await set_style(session, graph, 0, color=PRIMARY, line_width=1.15, line_style=0)
    await set_style(session, graph, 1, color=SECONDARY, line_width=0.80, line_style=1)
    if log_y:
        await r2.base.call(
            session,
            "origin_set_axis",
            {"graph_name": graph, "axis": "y", "scale": "log10"},
        )
    if show_shared_legend:
        await run_script(
            session,
            f'win -a "{graph}"; layer -s 1; legend -d; '
            'Legend.text$="\\l(1) Observed     \\l(2) Model"; '
            "Legend.font=font(Arial); Legend.fsize=4.5; Legend.background=0;"
            "Legend.color=color(82,88,94); Legend.hgap=30; Legend.vgap=20;"
            "label -al 2; doc -uw;",
        )
    return graph


async def merge_multipanel(
    session: ClientSession,
    graphs: list[str],
    *,
    output_name: str,
    stem: str,
    adaptation: bool,
) -> dict[str, Any]:
    merge_args = {
        "graph_names": graphs,
        "output_name": output_name,
        "rows": 2,
        "columns": 2,
        "keep_sources": True,
        "arrange": True,
        # Let Origin derive the merged page from the four already normalized
        # source pages.  Percent spacing avoids the modal "layer frame too
        # small" failure that can occur when merge_graph interprets physical
        # page units before the merged page has acquired its final dimensions.
        "gap_x": 4,
        "gap_y": 5,
        "margins": [6, 8, 4, 7],
        "unit": "percent",
        "label_style": "none",
        "common_x_scale": True,
        "common_y_scale": False,
    }
    try:
        merged = await r2.base.call(session, "origin_merge_graphs", merge_args)
    except RuntimeError as exc:
        # Large 2x2 merges can finish in Origin just after the bridge's 30 s
        # response window.  Give the GUI time to settle, then recover the
        # active merged page instead of recreating the earlier panels.
        await asyncio.sleep(15)
        merged = {"recoverable_timeout": str(exc), "output_graph": output_name}
    graph = r2.base.find_key(merged, "output_graph")
    if not isinstance(graph, str) or not graph:
        graph = graph_name(await r2.base.call(session, "origin_get_graph_info", {}))
    info = await r2.base.call(session, "origin_get_graph_info", {"graph_name": graph})
    layers = r2.base.find_key(info, "layers")
    if not isinstance(layers, list) or len(layers) < 4:
        raise RuntimeError(f"Merged graph has no four-layer geometry: {info}")
    for layer_index, (letter, layer) in enumerate(zip("abcd", layers[:4]), 1):
        axes = layer.get("axes", {})
        x_limits = axes.get("x", {}).get("limits", [0, 1, 0.2])
        y_limits = axes.get("y", {}).get("limits", [0, 1, 0.2])
        x_pos = float(x_limits[0]) + 0.035 * (float(x_limits[1]) - float(x_limits[0]))
        y_pos = float(y_limits[1]) - 0.06 * (float(y_limits[1]) - float(y_limits[0]))
        await run_script(
            session,
            safe_direct_label(
                graph, f"P2Panel{letter.upper()}", f"({letter})", x_pos, y_pos,
                INK, size=6.4, layer_index=layer_index,
            ) + f" P2Panel{letter.upper()}.bold=1; doc -uw;",
        )
    await run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; xb.text$=""; layer.x.showlabel=0; '
            'layer -s 2; xb.text$=""; layer.x.showlabel=0; '
            'layer -s 3; xb.text$=""; layer -s 4; xb.text$=""; doc -uw;'
        ),
    )
    await run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; label -p 45 98 -n P2SharedX "Time (s)"; '
            "P2SharedX.attach=1; P2SharedX.left=page.width/2-P2SharedX.width/2;"
            "P2SharedX.top=page.height-P2SharedX.height-4;"
            "P2SharedX.font=font(Arial); P2SharedX.fsize=5.6;"
            "P2SharedX.background=0; doc -uw;"
        ),
    )
    await run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; '
            'label -p 45 2 -n P2SharedLegend "\\l(1) Observed     \\l(2) Model"; '
            "P2SharedLegend.attach=1;"
            "P2SharedLegend.left=page.width/2-P2SharedLegend.width/2; P2SharedLegend.top=4;"
            "P2SharedLegend.font=font(Arial); P2SharedLegend.fsize=4.6;"
            "P2SharedLegend.background=0; doc -uw; sec -p 0.1;"
        ),
    )
    exports = await export_graph(session, graph, stem, width=3600)
    return {
        "id": stem,
        "graph": graph,
        "merge": merged,
        "source_graphs": graphs,
        "exports": exports,
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_multipanels(session: ClientSession) -> list[dict[str, Any]]:
    path = BENCH / "phase2_multipanel.csv"
    configs = [
        ("P2_MP_DISP", "displacement_observed", "displacement_model", "Displacement (mm)"),
        ("P2_MP_VEL", "velocity_observed", "velocity_model", "Velocity (m/s)"),
        ("P2_MP_POWER", "power_observed", "power_model", "Power (kW)"),
        ("P2_MP_ERROR", "error_observed", "error_model", "Error"),
    ]
    graphs = []
    for i, (name, observed, model, label) in enumerate(configs):
        graphs.append(
            await render_panel_source(
                session,
                path=path,
                graph_request=name,
                x_col="time_s",
                observed_col=observed,
                model_col=model,
                y_label=label,
                show_shared_legend=i == 0,
            )
        )
    standard = await merge_multipanel(
        session, graphs, output_name="P2_MULTIPANEL_2X2", stem="P2_MULTIPANEL_2X2", adaptation=False
    )

    stress_path = BENCH / "phase2_multipanel_stress.csv"
    stress_configs = [
        ("P2_MS_DISP", "displacement_observed", "displacement_model", "Displacement (m)", False),
        ("P2_MS_VEL", "velocity_observed", "velocity_model", "Velocity (m/s)", False),
        ("P2_MS_POWER", "power_observed", "power_model", "Power (W)", False),
        (
            "P2_MS_ERROR", "log10_abs_error_observed", "log10_abs_error_model",
            "log10 |error|", False,
        ),
    ]
    stress_graphs = []
    for i, (name, observed, model, label, log_y) in enumerate(stress_configs):
        stress_graphs.append(
            await render_panel_source(
                session,
                path=stress_path,
                graph_request=name,
                x_col="elapsed_operation_time_seconds",
                observed_col=observed,
                model_col=model,
                y_label=label,
                show_shared_legend=i == 0,
                log_y=log_y,
            )
        )
    stress = await merge_multipanel(
        session,
        stress_graphs,
        output_name="P2_MULTIPANEL_STRESS",
        stem="P2_MULTIPANEL_STRESS",
        adaptation=True,
    )
    return [standard, stress]


async def render_surface_one(
    session: ClientSession,
    *,
    data_path: Path,
    optimum_path: Path,
    graph_request: str,
    stem: str,
    z_limits: tuple[float, float, float],
    adaptation: bool,
) -> dict[str, Any]:
    graph, created, surface_range = await create_matrix_plot(
        session,
        data_path=data_path,
        x_col="x",
        y_col="y",
        z_col="objective",
        book_name=f"{graph_request}_FIELD",
        graph_request_name=graph_request,
        plot_type_id=103,
        template="glcmap",
    )
    await set_style(
        session,
        graph,
        0,
        colormap="BlueGreenYellow",
        color_scale_limits=[z_limits[0], z_limits[1]],
        line_width=0.18,
    )
    await run_script(
        session,
        (
            f'win -a "{graph}"; range P2SurfaceRange={surface_range}; '
            "set P2SurfaceRange -cpal BlueGreenYellow; set P2SurfaceRange -b3m 0; doc -uw;"
        ),
    )
    optimum = await r2.base.call(
        session,
        "origin_import_table",
        {"path": str(optimum_path), "book_name": f"{graph_request}_OPT", "sheet_name": "Point"},
    )
    optimum_sheet = r2.base.find_key(optimum, "worksheet")
    if not isinstance(optimum_sheet, dict):
        raise RuntimeError(f"No optimum worksheet returned: {optimum}")
    optimum_book = str(optimum_sheet["book_name"])
    optimum_sheet_name = str(optimum_sheet["sheet_name"])
    marker_lift = (z_limits[1] - z_limits[0]) * 0.05
    # plotxyz is the native Origin route for adding a 3D scatter to an
    # existing OpenGL layer.  The visual-only Z lift prevents z-fighting at
    # a surface minimum; the source CSV and X/Y optimum coordinates remain
    # unchanged and the lift is recorded in the execution log.
    overlay = await run_script(
        session,
        (
            f'win -a "{optimum_book}"; '
            "wks.col1.type=4; wks.col2.type=1; wks.col3.type=6; "
            f"range P2OptimumZ=[{optimum_book}]{optimum_sheet_name}!col(C); "
            f"P2OptimumZ=P2OptimumZ+{marker_lift}; "
            f"plotxyz iz:=3 plot:=240 rescale:=0 ogl:=[{graph}]1!; "
            f'win -a "{graph}"; doc -uw; sec -p 0.1;'
        ),
    )
    count = await plot_count(session, graph)
    if count > 1:
        await set_style(
            session, graph, count - 1, color=HIGHLIGHT, colormap="Lite Orange",
            line_width=0.20, symbol_kind=2, symbol_size=4.2,
        )
    await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "surface",
            "page_width": 1800,
            "page_height": 1200,
            "font_family": "Arial",
            "axis_title_size": 6,
            "tick_label_size": 5,
            "legend_font_size": 4,
            "line_width": 0.8,
            "symbol_size": 3.0,
            "tick_length": 1.5,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    # apply_nature_style normalizes canvas typography but also normalizes plot
    # marks.  Restore the semantic surface/optimum encodings afterwards.
    await set_style(
        session, graph, 0, colormap="BlueGreenYellow",
        color_scale_limits=[z_limits[0], z_limits[1]], line_width=0.16,
    )
    if count > 1:
        await set_style(
            session, graph, count - 1, color=HIGHLIGHT, colormap="Lite Orange",
            line_width=0.18, symbol_kind=2, symbol_size=4.2,
        )
    await run_script(
        session,
        (
            f'win -a "{graph}"; range P2SurfaceRange={surface_range}; '
            "set P2SurfaceRange -cpal BlueGreenYellow; set P2SurfaceRange -b3m 0; doc -uw;"
        ),
    )
    await r2.base.call(
        session,
        "origin_arrange_layers",
        {
            "graph_name": graph,
            "rows": 1,
            "columns": 1,
            "layer_geometries": [
                {"layer_index": 0, "left": 10, "top": 7, "width": 68, "height": 73}
            ],
        },
    )
    for axis, start, end, step, title in (
        ("x", -3, 3, 1, "Decision variable x"),
        ("y", -3, 3, 1, "Decision variable y"),
        ("z", z_limits[0], z_limits[1], z_limits[2], "Objective value"),
    ):
        await r2.base.call(
            session, "origin_set_axis",
            {"graph_name": graph, "axis": axis, "start": start, "end": end, "step": step, "title": title},
        )
    view = await run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; layer.color=color(white); layer.border=0;'
            "layer.camera.azimuth=138; layer.camera.inclination=45; layer.camera.roll=0;"
            "layer.light.mode=1; layer.light.kd=55; layer.light.ks=8; layer.light.shininess=8;"
            "layer -3d m P-1; layer -3d m frame;"
            "layer.x.label.font=font(Arial); layer.y.label.font=font(Arial); layer.z.label.font=font(Arial);"
            "layer.x.label.pt=6; layer.y.label.pt=6; layer.z.label.pt=6;"
            "layer.x.ticklabel.pt=5; layer.y.ticklabel.pt=5; layer.z.ticklabel.pt=5;"
            "layer.x.ticks.len=1.5; layer.y.ticks.len=1.5; layer.z.ticks.len=1.5;"
            "layer.x.grid.show=0; layer.y.grid.show=0; layer.z.grid.show=0;"
            "doc -uw; sec -p 0.2;"
        ),
    )
    await run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; '
            'xb.text$="Decision variable x"; xt.text$="Decision variable x"; '
            'yl.text$="Decision variable y"; yr.text$="Decision variable y"; '
            'zb.text$="Objective value"; zf.text$="Objective value"; '
            "xb.font=font(Arial); xt.font=font(Arial); yl.font=font(Arial); yr.font=font(Arial); "
            "zb.font=font(Arial); zf.font=font(Arial); "
            "xb.fsize=6; xt.fsize=6; yl.fsize=6; yr.fsize=6; zb.fsize=6; zf.fsize=6; "
            "doc -uw; sec -p 0.1;"
        ),
    )
    await run_script(session, f'win -a "{graph}"; label -r Spectrum1; spectrum; doc -uw; sec -p 0.1;')
    await run_script(
        session,
        (
            f'win -a "{graph}"; Spectrum1.labels.autodisp=0; '
            "Spectrum1.labels.font=font(Arial); Spectrum1.labels.fsize=4.8;"
            "Spectrum1.labels.bold=0; Spectrum1.labels.color=color(94,100,106);"
            f"Spectrum1.levels.from={z_limits[0]}; Spectrum1.levels.to={z_limits[1]};"
            f"Spectrum1.levels.inc$={z_limits[2]}; Spectrum1.levels.minorticks=0;"
            'Spectrum1.title$="Objective value"; Spectrum1.title=1;'
            "Spectrum1.barthick=70; Spectrum1.lgap=18; Spectrum1.lineWidth=0.24;"
            "Spectrum1.color=color(118,124,130); Spectrum1.draw(global); doc -uw; sec -p 0.1;"
        ),
    )
    exports = await export_graph(session, graph, stem)
    return {
        "id": stem,
        "graph": graph,
        "created": created,
        "optimum": optimum,
        "overlay": overlay,
        "marker_display_lift": marker_lift,
        "view": view,
        "exports": exports,
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_surfaces(session: ClientSession) -> list[dict[str, Any]]:
    standard = await render_surface_one(
        session,
        data_path=BENCH / "two_parameter_objective.csv",
        optimum_path=BENCH / "two_parameter_optimum.csv",
        graph_request="P2_SURFACE_3D",
        stem="P2_SURFACE_3D",
        z_limits=(0, 36, 6),
        adaptation=False,
    )
    stress = await render_surface_one(
        session,
        data_path=BENCH / "phase2_surface_stress.csv",
        optimum_path=BENCH / "phase2_surface_stress_optimum.csv",
        graph_request="P2_SURFACE_3D_STRESS",
        stem="P2_SURFACE_3D_STRESS",
        z_limits=(0, 100, 20),
        adaptation=True,
    )
    return [standard, stress]


async def render(session: ClientSession) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ping = await r2.base.call(session, "origin_ping", {"show": True})
    fresh = await r2.base.call(session, "origin_new_project", {"show": True})
    figures: list[dict[str, Any]] = []
    figures.extend(await render_scatter(session))
    figures.extend(await render_heatmaps(session))
    figures.extend(await render_convergence(session))
    figures.extend(await render_multipanels(session))
    figures.extend(await render_surfaces(session))
    source = await r2.base.call(
        session,
        "origin_save_project",
        {"path": str(OUTPUT / "ORIGIN_PHASE2_STYLE_TRAINING.opju"), "overwrite": True},
    )
    return {
        "phase": "Phase 2 — Signature Scientific Style migration",
        "frozen_templates_modified": False,
        "ping": ping,
        "fresh_project": fresh,
        "figures": figures,
        "source_project": source,
    }


async def save_templates(session: ClientSession) -> dict[str, Any]:
    library_before = await r2.base.call(session, "origin_list_user_templates", {})
    templates_before = r2.base.find_key(library_before, "templates")
    if not isinstance(templates_before, list):
        templates_before = []
    existing = {
        item.get("name")
        for item in templates_before
        if isinstance(item, dict)
    }
    candidates = [
        (
            "SCP_SCATTER_FIT_v20_CANDIDATE",
            "P2_SCATTER_FIT",
            ["scatter", "line", "uncertainty-band"],
            ["x", "observed", "fit", "confidence-interval", "outlier"],
            7,
        ),
        (
            "SCP_HEATMAP_CONTINUOUS_v20_CANDIDATE",
            "Graph4",
            ["heatmap"],
            ["x", "time", "temperature", "colorbar"],
            3,
        ),
        (
            "SCP_OPTIMIZATION_CONVERGENCE_v20_CANDIDATE",
            "P2_CONVERGENCE",
            ["line", "scatter"],
            ["iteration", "best", "mean", "final-optimum"],
            4,
        ),
        (
            "SCP_MULTIPANEL_2X2_v20_CANDIDATE",
            "P2_MULTIPANEL_2X2",
            ["multi-panel", "line"],
            ["displacement", "velocity", "power", "error", "shared-legend", "panel-labels"],
            9,
        ),
        (
            "SCP_SURFACE_3D_AUXILIARY_v20_CANDIDATE",
            "Graph16",
            ["surface-3d", "scatter-3d"],
            ["x", "y", "z", "optimum", "colorbar", "auxiliary"],
            3,
        ),
    ]
    saved = []
    for name, graph, plot_types, roles, n_columns in candidates:
        if name in existing:
            saved.append({"name": name, "skipped": True, "reason": "candidate already exists"})
            continue
        saved.append(
            await r2.base.call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": (
                        "Phase 2 candidate migrating Signature Scientific Style v1.1 to a new A-problem figure class. "
                        "Human aesthetic approval pending; does not modify v11_FROZEN templates."
                    ),
                    "tags": [
                        "signature-scientific-style-v1.1",
                        "phase2",
                        "candidate",
                        "human-review-pending",
                    ],
                    "plot_types": plot_types,
                    "roles": roles,
                    "n_columns": n_columns,
                    "graph_name": graph,
                    "overwrite": False,
                },
            )
        )
    return {
        "status": "PHASE2 CANDIDATES — HUMAN AESTHETIC REVIEW PENDING",
        "frozen_templates_modified": False,
        "templates": saved,
        "library_before": library_before,
        "library_after": await r2.base.call(session, "origin_list_user_templates", {}),
    }


async def freeze_passed_templates(session: ClientSession) -> dict[str, Any]:
    """Promote only the three human-approved Phase 2 graph classes.

    The source graphs are read without restyling.  New FROZEN names are used,
    overwrite is disabled, and the v11 frozen templates remain untouched.
    """
    approved = [
        (
            "SCP_SCATTER_FIT_v20_FROZEN",
            "Graph1",
            ["scatter", "line", "uncertainty-band"],
            ["x", "observed", "fit", "confidence-interval", "outlier"],
            7,
        ),
        (
            "SCP_HEATMAP_CONTINUOUS_v20_FROZEN",
            "Graph4",
            ["heatmap"],
            ["x", "time", "temperature", "colorbar"],
            3,
        ),
        (
            "SCP_OPTIMIZATION_CONVERGENCE_v20_FROZEN",
            "Graph6",
            ["line", "scatter"],
            ["iteration", "best", "mean", "final-optimum"],
            4,
        ),
    ]
    saved = []
    for name, graph, plot_types, roles, n_columns in approved:
        saved.append(
            await r2.base.call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": (
                        "HUMAN AESTHETIC REVIEW PASSED — FROZEN. Signature Scientific Style v1.1 "
                        "Phase 2 extension. Modify only when real competition data exposes a "
                        "scientific-accuracy, readability, or adaptation failure."
                    ),
                    "tags": [
                        "signature-scientific-style-v1.1",
                        "phase2",
                        "frozen",
                        "human-approved",
                        "publication-grade",
                    ],
                    "plot_types": plot_types,
                    "roles": roles,
                    "n_columns": n_columns,
                    "graph_name": graph,
                    "overwrite": False,
                },
            )
        )
    return {
        "status": "PHASE 2 PASS TEMPLATES — FROZEN",
        "frozen_templates_modified": False,
        "saved": saved,
        "library_after": await r2.base.call(session, "origin_list_user_templates", {}),
    }


async def run(mode: str) -> None:
    env = dict(os.environ)
    # Phase 2 uses fill-area, matrix heatmap, graph merge, and 3D surface tools,
    # which are intentionally outside the compact standard profile.
    env["ORIGIN_MCP_TOOL_PROFILE"] = "full"
    env["ORIGIN_MCP_ALLOWED_ROOTS"] = str(SYSTEM_ROOT)
    params = StdioServerParameters(
        command=str(PYTHON_EXE),
        args=["-m", "origin_mcp"],
        env=env,
        cwd=str(SYSTEM_ROOT.parent),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            if mode == "render":
                result = await render(session)
                target = LOG_DIR / "phase2_mcp_execution.json"
            elif mode == "save-templates":
                result = await save_templates(session)
                target = LOG_DIR / "phase2_template_save.json"
            elif mode == "freeze-passed":
                result = await freeze_passed_templates(session)
                target = LOG_DIR / "phase2_pass_freeze.json"
            else:
                result = {
                    name: await r2.base.call(session, "origin_get_graph_info", {"graph_name": name})
                    for name in ("Graph1", "Graph10", "P2_MULTIPANEL_2X2", "Graph16", "Graph17")
                }
                target = LOG_DIR / "phase2_graph_inspection.json"
            target.write_text(
                json.dumps(r2.base.jsonable(result), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(json.dumps({"mode": mode, "result_file": str(target)}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("render", "save-templates", "freeze-passed", "inspect"))
    args = parser.parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
