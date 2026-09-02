"""Origin MCP refinement for Phase 2 Multi-panel and auxiliary 3D Surface.

This renderer intentionally creates a new Origin project and new candidate
templates.  It never loads, restyles, or overwrites any FROZEN template.
Python is limited to deterministic data preparation and MCP orchestration;
all graph construction and export is performed by Origin.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import origin_phase2 as p2
import origin_round2 as r2


SYSTEM_ROOT = p2.SYSTEM_ROOT
BENCH = p2.BENCH
OUTPUT = r2.base.OUTPUT / "phase2_refinement"
LOG_DIR = p2.LOG_DIR
PYTHON_EXE = p2.PYTHON_EXE

PRIMARY = p2.PRIMARY
HIGHLIGHT = p2.HIGHLIGHT
SECONDARY = p2.SECONDARY
INK = p2.INK
PALETTE = p2.PALETTE
SURFACE_PALETTE = SYSTEM_ROOT / "themes" / "SignatureScientificField19.pal"
ORIGIN_USER_PALETTE = Path(
    r"C:\Users\YiPian\Documents\OriginLab\User Files\Palettes\SignatureScientificField19.pal"
)


def rgb(value: list[int]) -> str:
    return p2.rgb(value)


def prepare_stress_table() -> Path:
    """Add positive absolute-error columns for a genuine log10 axis test."""
    source = BENCH / "phase2_multipanel_stress.csv"
    target = BENCH / "phase2_multipanel_refinement_stress.csv"
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    extra = ["abs_error_observed", "abs_error_model"]
    for name in extra:
        if name not in fields:
            fields.append(name)
    for row in rows:
        # The benchmark already records log10(abs(error)); invert that
        # disclosed transformation to obtain strictly positive values.
        row["abs_error_observed"] = f"{10 ** float(row['log10_abs_error_observed']):.12g}"
        row["abs_error_model"] = f"{10 ** float(row['log10_abs_error_model']):.12g}"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return target


def prepare_surface_palette() -> None:
    """Write a 256-step JASC palette interpolated from the frozen 19-color field family."""
    lines = ["JASC-PAL", "0100", "256"]
    last = len(PALETTE) - 1
    for i in range(256):
        position = i * last / 255
        left = min(int(position), last - 1)
        fraction = position - left
        color = [
            round(PALETTE[left][channel] * (1 - fraction) + PALETTE[left + 1][channel] * fraction)
            for channel in range(3)
        ]
        lines.append(" ".join(str(value) for value in color))
    payload = "\n".join(lines) + "\n"
    for path in (SURFACE_PALETTE, ORIGIN_USER_PALETTE):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="ascii")


async def render_panel_source(
    session: ClientSession,
    *,
    path: Path,
    graph_request: str,
    x_col: str,
    observed_col: str,
    model_col: str,
    y_label: str,
    log_y: bool = False,
    scientific_y: bool = False,
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
    graph = p2.graph_name(created)
    await p2.set_style(session, graph, 0, color=PRIMARY, line_width=1.12, line_style=0)
    await p2.set_style(session, graph, 1, color=SECONDARY, line_width=0.76, line_style=1)
    await r2.base.call(
        session,
        "origin_format_graph",
        {"graph_name": graph, "x_label": "", "y_label": y_label, "show_legend": False},
    )
    # Multi-panel typography is tuned as its own system.  These values are
    # intended for a 15.5 cm composite and are not a mechanical reduction of
    # the single-panel sizes.
    await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "line",
            "page_width": 1200,
            "page_height": 780,
            "font_family": "Arial",
            "axis_title_size": 4.2,
            "tick_label_size": 3.7,
            "legend_font_size": 3.8,
            "line_width": 0.86,
            "symbol_size": 2.2,
            "tick_length": 1.15,
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
            "layer_geometries": [{"layer_index": 0, "left": 16, "top": 5, "width": 80, "height": 82}],
        },
    )
    await p2.run_script(session, r2.base_labtalk(graph))
    await p2.set_style(session, graph, 0, color=PRIMARY, line_width=1.12, line_style=0)
    await p2.set_style(session, graph, 1, color=SECONDARY, line_width=0.76, line_style=1)
    if log_y:
        await r2.base.call(session, "origin_set_axis", {"graph_name": graph, "axis": "y", "scale": "log10"})
    number_format = (
        "layer.y.label.numFormat=2; layer.y.label.decPlaces=1;"
        if scientific_y
        else ""
    )
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; xb.text$=""; xt.text$=""; '
            "layer.x.showlabel=0; layer.x.thickness=0.38; layer.y.thickness=0.38;"
            "layer.x.tickthickness=0.30; layer.y.tickthickness=0.30;"
            "layer.x.ticklength=1.05; layer.y.ticklength=1.05;"
            "layer.x.minorTicks=0; layer.y.minorTicks=0;"
            "layer.x.label.pt=3.7; layer.y.label.pt=3.7;"
            "layer.x.grid.show=0; layer.y.grid.show=0;"
            f"{number_format} doc -uw; sec -p 0.1;"
        ),
    )
    return graph


def panel_label_position(layer: dict[str, Any], log_y: bool) -> tuple[float, float]:
    axes = layer.get("axes", {})
    x_limits = axes.get("x", {}).get("limits", [0.0, 1.0, 0.2])
    y_limits = axes.get("y", {}).get("limits", [0.0, 1.0, 0.2])
    x0, x1 = float(x_limits[0]), float(x_limits[1])
    y0, y1 = float(y_limits[0]), float(y_limits[1])
    x = x0 + 0.025 * (x1 - x0)
    if log_y and y0 > 0 and y1 > y0:
        y = y1 / ((y1 / y0) ** 0.045)
    else:
        y = y1 - 0.045 * (y1 - y0)
    return x, y


async def export_audit_png(session: ClientSession, graph: str, stem: str, width: int) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    await p2.run_script(session, "@MGI=1; @MGR=1; expGraph.DPI=300;")
    return await r2.base.call(
        session,
        "origin_export_graph",
        {
            "graph_name": graph,
            "path": str(OUTPUT / f"{stem}.png"),
            "overwrite": True,
            "width": width,
        },
    )


async def merge_multipanel(
    session: ClientSession,
    graphs: list[str],
    *,
    output_name: str,
    stem: str,
    log_panel: int | None,
    adaptation: bool,
) -> dict[str, Any]:
    merged = await r2.base.call(
        session,
        "origin_merge_graphs",
        {
            "graph_names": graphs,
            "output_name": output_name,
            "rows": 2,
            "columns": 2,
            "keep_sources": True,
            "arrange": True,
            "gap_x": 2.4,
            "gap_y": 3.0,
            "margins": [4.5, 5.0, 3.5, 5.5],
            "unit": "percent",
            "label_style": "none",
            "common_x_scale": True,
            "common_y_scale": False,
        },
    )
    graph = r2.base.find_key(merged, "output_graph")
    if not isinstance(graph, str) or not graph:
        graph = p2.graph_name(await r2.base.call(session, "origin_get_graph_info", {}))
    await p2.run_script(session, f'win -a "{graph}"; page.width=1800; page.height=1240; doc -uw; sec -p 0.2;')
    if adaptation:
        geometries = [
            {"layer_index": 0, "left": 9.0, "top": 6.5, "width": 39.5, "height": 39.5},
            {"layer_index": 1, "left": 54.5, "top": 6.5, "width": 40.0, "height": 39.5},
            {"layer_index": 2, "left": 9.0, "top": 51.0, "width": 39.5, "height": 39.5},
            {"layer_index": 3, "left": 54.5, "top": 51.0, "width": 40.0, "height": 39.5},
        ]
    else:
        geometries = [
            {"layer_index": 0, "left": 7.0, "top": 6.5, "width": 41.5, "height": 39.5},
            {"layer_index": 1, "left": 53.0, "top": 6.5, "width": 41.5, "height": 39.5},
            {"layer_index": 2, "left": 7.0, "top": 51.0, "width": 41.5, "height": 39.5},
            {"layer_index": 3, "left": 53.0, "top": 51.0, "width": 41.5, "height": 39.5},
        ]
    await r2.base.call(
        session,
        "origin_arrange_layers",
        {"graph_name": graph, "rows": 2, "columns": 2, "layer_geometries": geometries},
    )
    # Reapply the compact composite typography and low-weight axes after merge.
    for layer_index in range(1, 5):
        await p2.run_script(
            session,
            (
                f'win -a "{graph}"; layer -s {layer_index}; xb.text$=""; xt.text$=""; '
                "layer.x.showlabel=0; layer.x.thickness=0.38; layer.y.thickness=0.38;"
                "layer.x.tickthickness=0.30; layer.y.tickthickness=0.30;"
                "layer.x.ticklength=1.05; layer.y.ticklength=1.05;"
                "layer.x.minorTicks=0; layer.y.minorTicks=0;"
                "layer.x.label.font=font(Arial); layer.y.label.font=font(Arial);"
                "layer.x.label.pt=3.7; layer.y.label.pt=3.7;"
                "yl.font=font(Arial); yl.fsize=4.2; yr.fsize=4.2;"
                "layer.x.grid.show=0; layer.y.grid.show=0; doc -uw;"
            ),
        )
    info = await r2.base.call(session, "origin_get_graph_info", {"graph_name": graph})
    layers = r2.base.find_key(info, "layers")
    if not isinstance(layers, list) or len(layers) < 4:
        raise RuntimeError(f"Merged graph has no four-layer geometry: {info}")
    panel_page_positions = [(10.0, 5.0)] * 4
    for layer_index, (letter, (page_x, page_y)) in enumerate(zip("abcd", panel_page_positions), 1):
        await p2.run_script(
            session,
            (
                f'win -a "{graph}"; layer -s {layer_index}; '
                f'label -p {page_x} {page_y} -n P2RPanel{letter.upper()} "({letter})"; '
                f"P2RPanel{letter.upper()}.attach=1; "
                f"P2RPanel{letter.upper()}.font=font(Arial); P2RPanel{letter.upper()}.fsize=5.0; "
                f"P2RPanel{letter.upper()}.bold=1; P2RPanel{letter.upper()}.color=color(43,47,51); "
                f"P2RPanel{letter.upper()}.background=0; doc -uw;"
            ),
        )
    # Shared title and legend sit immediately outside the panel cluster.
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; '
            'label -p 45 2 -n P2RSharedLegend "\\l(1) Observed     \\l(2) Model"; '
            "P2RSharedLegend.attach=1; P2RSharedLegend.left=page.width/2-P2RSharedLegend.width/2;"
            "P2RSharedLegend.top=5; P2RSharedLegend.font=font(Arial);"
            "P2RSharedLegend.fsize=3.8; P2RSharedLegend.color=color(82,88,94);"
            "P2RSharedLegend.background=0;"
            'label -p 45 96 -n P2RSharedX "Time (s)"; '
            "P2RSharedX.attach=1; P2RSharedX.left=page.width/2-P2RSharedX.width/2;"
            "P2RSharedX.top=page.height-P2RSharedX.height-14;"
            "P2RSharedX.font=font(Arial); P2RSharedX.fsize=4.2;"
            "P2RSharedX.color=color(43,47,51); P2RSharedX.background=0; doc -uw; sec -p 0.2;"
        ),
    )
    await asyncio.sleep(0.5)
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; '
            "P2RSharedLegend.left=(page.width-P2RSharedLegend.width)/2; P2RSharedLegend.top=5;"
            "P2RSharedX.left=(page.width-P2RSharedX.width)/2;"
            "P2RSharedX.top=page.height-P2RSharedX.height-12;"
            f"P2RPanelA.left=page.width*{geometries[0]['left'] / 100}+190; P2RPanelA.top=page.height*0.065+20;"
            f"P2RPanelB.left=page.width*{geometries[1]['left'] / 100}+190; P2RPanelB.top=page.height*0.065+20;"
            f"P2RPanelC.left=page.width*{geometries[2]['left'] / 100}+190; P2RPanelC.top=page.height*0.51+20;"
            f"P2RPanelD.left=page.width*{geometries[3]['left'] / 100}+190; P2RPanelD.top=page.height*0.51+20;"
            "doc -uw; sec -p 0.3;"
        ),
    )
    if adaptation:
        # Panel (d) carries both the scientific-notation and genuine log10
        # axis stress tests over strictly positive absolute errors.
        await p2.run_script(
            session,
            (
                f'win -a "{graph}"; layer -s 4; '
                "layer.y.from=1e-8; layer.y.to=1e-3; layer.y.inc=1; layer.y.rescale=1;"
                "layer.y.labelSubtype=2; layer.y.decPlaces=0; doc -uw; sec -p 0.2;"
            ),
        )
    exports = await p2.export_graph(session, graph, stem, width=3600)
    audits = [
        await export_audit_png(session, graph, f"{stem}_155MM_AUDIT", 1831),
        await export_audit_png(session, graph, f"{stem}_088MM_AUDIT", 1040),
    ]
    return {
        "id": stem,
        "graph": graph,
        "merge": merged,
        "source_graphs": graphs,
        "exports": exports,
        "size_audits": {"155_mm_at_300_dpi": audits[0], "88_mm_at_300_dpi": audits[1]},
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_multipanels(session: ClientSession) -> list[dict[str, Any]]:
    standard_path = BENCH / "phase2_multipanel.csv"
    standard_specs = [
        ("P2R_MP_DISP", "displacement_observed", "displacement_model", "Displacement (mm)", False, False),
        ("P2R_MP_VEL", "velocity_observed", "velocity_model", "Velocity (m/s)", False, False),
        ("P2R_MP_POWER", "power_observed", "power_model", "Power (kW)", False, False),
        ("P2R_MP_ERROR", "error_observed", "error_model", "Error", False, False),
    ]
    standard_graphs = [
        await render_panel_source(
            session,
            path=standard_path,
            graph_request=name,
            x_col="time_s",
            observed_col=observed,
            model_col=model,
            y_label=label,
            log_y=log_y,
            scientific_y=scientific,
        )
        for name, observed, model, label, log_y, scientific in standard_specs
    ]
    standard = await merge_multipanel(
        session,
        standard_graphs,
        output_name="P2R_MULTIPANEL_2X2",
        stem="P2_MULTIPANEL_2X2_REFINED",
        log_panel=None,
        adaptation=False,
    )

    stress_path = prepare_stress_table()
    stress_specs = [
        ("P2R_MS_DISP", "displacement_observed", "displacement_model", "Displacement (m)", False, False),
        ("P2R_MS_VEL", "velocity_observed", "velocity_model", "Velocity (m/s)", False, False),
        ("P2R_MS_POWER", "power_observed", "power_model", "Power (W)", False, False),
        ("P2R_MS_ERROR", "abs_error_observed", "abs_error_model", "Absolute error", True, True),
    ]
    stress_graphs = [
        await render_panel_source(
            session,
            path=stress_path,
            graph_request=name,
            x_col="elapsed_operation_time_seconds",
            observed_col=observed,
            model_col=model,
            y_label=label,
            log_y=log_y,
            scientific_y=scientific,
        )
        for name, observed, model, label, log_y, scientific in stress_specs
    ]
    stress = await merge_multipanel(
        session,
        stress_graphs,
        output_name="P2R_MULTIPANEL_STRESS",
        stem="P2_MULTIPANEL_2X2_REFINED_STRESS",
        log_panel=4,
        adaptation=True,
    )
    return [standard, stress]


def surface_palette_script(graph: str, low: float, high: float) -> str:
    levels = [low + (high - low) * i / (len(PALETTE) - 1) for i in range(len(PALETTE))]
    # Six contour guides across 19 filled color levels.
    line_indices = {1, 5, 8, 12, 15, 19}
    parts = [f'win -a "{graph}"; layer -s 1;', f"layer.cmap.numColors={len(PALETTE)};"]
    for i, (level, color) in enumerate(zip(levels, PALETTE), 1):
        parts.extend(
            [
                f"layer.cmap.z{i}={level};",
                f"layer.cmap.color{i}={rgb(color)};",
                f"layer.cmap.line{i}={1 if i in line_indices else 0};",
                f"layer.cmap.lineWidth{i}=0.14;",
                f"layer.cmap.lineColor{i}=color(78,91,96);",
                f"layer.cmap.label{i}=0;",
            ]
        )
    parts.extend(
        [
            f"layer.cmap.colorLow={rgb(PALETTE[0])};",
            f"layer.cmap.colorHigh={rgb(PALETTE[-1])};",
            "layer.cmap.colorAbove=layer.cmap.colorHigh; layer.cmap.colorBelow=layer.cmap.colorLow;",
            "layer.cmap.labelAbove=0; layer.cmap.lineAbove=0;",
            "layer.cmap.updateScale(); doc -uw; sec -p 0.2;",
        ]
    )
    return " ".join(parts)


async def render_surface(
    session: ClientSession,
    *,
    data_path: Path,
    optimum_path: Path,
    graph_request: str,
    stem: str,
    z_limits: tuple[float, float, float],
    adaptation: bool,
) -> dict[str, Any]:
    graph, created, surface_range = await p2.create_matrix_plot(
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
    marker_lift = (z_limits[1] - z_limits[0]) * 0.018
    overlay = await p2.run_script(
        session,
        (
            f'win -a "{optimum_book}"; wks.col1.type=4; wks.col2.type=1; wks.col3.type=6; '
            f"range P2ROptimumZ=[{optimum_book}]{optimum_sheet_name}!col(C); "
            f"P2ROptimumZ=P2ROptimumZ+{marker_lift}; "
            f"plotxyz iz:=3 plot:=240 rescale:=0 ogl:=[{graph}]1!; "
            f'win -a "{graph}"; doc -uw; sec -p 0.2;'
        ),
    )
    count = await p2.plot_count(session, graph)
    await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "surface",
            "page_width": 1800,
            "page_height": 1200,
            "font_family": "Arial",
            "axis_title_size": 5.6,
            "tick_label_size": 4.5,
            "legend_font_size": 4.0,
            "line_width": 0.65,
            "symbol_size": 2.7,
            "tick_length": 0.9,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    await p2.set_style(
        session,
        graph,
        0,
        colormap="BlueGreenYellow",
        color_scale_limits=[z_limits[0], z_limits[1]],
        line_width=0.12,
    )
    if count > 1:
        await p2.set_style(
            session,
            graph,
            count - 1,
            color=HIGHLIGHT,
            colormap="Lite Orange",
            line_width=0.14,
            symbol_kind=2,
            symbol_size=3.5,
        )
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; range P2RSurfaceRange={surface_range}; '
            "set P2RSurfaceRange -b3m 0; doc -uw; sec -p 0.1;"
        ),
    )
    await p2.run_script(session, surface_palette_script(graph, z_limits[0], z_limits[1]))
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; range P2RSurfaceRange={surface_range}; '
            "set P2RSurfaceRange -cpal SignatureScientificField19; doc -uw; sec -p 0.3;"
        ),
    )
    palette_path = str(ORIGIN_USER_PALETTE).replace("/", "\\")
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; layer -s 1; '
            f'palApply fname:="{palette_path}" stretch:=1; doc -uw; sec -p 0.3;'
        ),
    )
    await r2.base.call(
        session,
        "origin_arrange_layers",
        {
            "graph_name": graph,
            "rows": 1,
            "columns": 1,
            "layer_geometries": [{"layer_index": 0, "left": 5.5, "top": 4.5, "width": 75.0, "height": 82.0}],
        },
    )
    for axis, start, end, step, title in (
        ("x", -3, 3, 1, "Decision variable x"),
        ("y", -3, 3, 1, "Decision variable y"),
        ("z", z_limits[0], z_limits[1], z_limits[2], "Objective value"),
    ):
        await r2.base.call(
            session,
            "origin_set_axis",
            {"graph_name": graph, "axis": axis, "start": start, "end": end, "step": step, "title": title},
        )
    # Drive the perspective angle to its minimum using Origin's documented
    # 3D rotation command.  A 60° inclination gives a calm 2.5D view while
    # retaining interpretable height cues.
    view_script = [
        f'win -a "{graph}"; layer -s 1; @OGLL=0; @OGLLE=0;',
        "layer.color=color(white); layer.border=0; layer.clip=0;",
        "layer.camera.azimuth=135; layer.camera.inclination=68; layer.camera.roll=0;",
        "layer.light.mode=1; layer.light.kd=38; layer.light.ks=0; layer.light.shininess=0;",
    ]
    view_script.extend(["layer -3d m P-1;"] * 10)
    view_script.extend(
        [
            "layer -3d m frame;",
            "layer.x.color=color(105,111,116); layer.y.color=color(105,111,116); layer.z.color=color(105,111,116);",
            "layer.x2.color=color(105,111,116); layer.y2.color=color(105,111,116); layer.z2.color=color(105,111,116);",
            "layer.x.thickness=0.26; layer.y.thickness=0.26; layer.z.thickness=0.26;",
            "layer.x2.thickness=0.26; layer.y2.thickness=0.26; layer.z2.thickness=0.26;",
            "layer.x.showAxes=1; layer.y.showAxes=1; layer.z.showAxes=1;",
            "layer.x.tickthickness=0.24; layer.y.tickthickness=0.24; layer.z.tickthickness=0.24;",
            "layer.x.ticklength=0.85; layer.y.ticklength=0.85; layer.z.ticklength=0.85;",
            "layer.x.minorTicks=0; layer.y.minorTicks=0; layer.z.minorTicks=0;",
            "layer.x.label.font=font(Arial); layer.y.label.font=font(Arial); layer.z.label.font=font(Arial);",
            "layer.x.label.pt=4.5; layer.y.label.pt=4.5; layer.z.label.pt=4.5;",
            "layer.x.grid.show=0; layer.y.grid.show=0; layer.z.grid.show=0;",
            'xb.text$="Decision variable x"; xt.text$="Decision variable x";',
            'yl.text$="Decision variable y"; yr.text$="Decision variable y";',
            'zb.text$=""; zf.text$="";',
            "xb.font=font(Arial); xt.font=font(Arial); yl.font=font(Arial); yr.font=font(Arial);",
            "zb.font=font(Arial); zf.font=font(Arial);",
            "xb.fsize=5.6; xt.fsize=5.6; yl.fsize=5.6; yr.fsize=5.6; zb.fsize=5.6; zf.fsize=5.6;",
            "doc -uw; sec -p 0.3;",
        ]
    )
    view = await p2.run_script(session, " ".join(view_script))
    await p2.run_script(session, f'win -a "{graph}"; label -r Spectrum1; spectrum; doc -uw; sec -p 0.1;')
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; Spectrum1.labels.autodisp=0; '
            "Spectrum1.labels.font=font(Arial); Spectrum1.labels.fsize=4.2;"
            "Spectrum1.labels.bold=0; Spectrum1.labels.color=color(105,111,116);"
            f"Spectrum1.levels.from={z_limits[0]}; Spectrum1.levels.to={z_limits[1]};"
            "Spectrum1.title=0;"
            "Spectrum1.levels.major=3; Spectrum1.levels.type=1; Spectrum1.levels.inc=1;"
            f"Spectrum1.levels.inc$={z_limits[2]}; Spectrum1.levels.minorticks=0;"
            "Spectrum1.barthick=38; Spectrum1.lgap=12;"
            "Spectrum1.lineWidth=0.16; Spectrum1.color=color(132,138,143);"
            "Spectrum1.gridLineWidth=0.15; Spectrum1.symbolLineThickness=0.15;"
            "Spectrum1.tableBorderWidth=0.15;"
            "Spectrum1.left=1530; Spectrum1.top=220; Spectrum1.height=690;"
            "Spectrum1.draw(global); doc -uw; sec -p 0.2;"
        ),
    )
    await p2.run_script(
        session,
        (
            f'win -a "{graph}"; label -px 1385 12 -n P2RSurfaceCBTitle "Objective value"; '
            "P2RSurfaceCBTitle.attach=1; P2RSurfaceCBTitle.font=font(Arial);"
            "P2RSurfaceCBTitle.fsize=4.2; P2RSurfaceCBTitle.color=color(82,88,94);"
            "P2RSurfaceCBTitle.background=0; P2RSurfaceCBTitle.left=page.width*0.72;"
            "P2RSurfaceCBTitle.top=page.height*0.002; doc -uw; sec -p 0.2;"
        ),
    )
    exports = await p2.export_graph(session, graph, stem, width=2800)
    info = await r2.base.call(session, "origin_get_graph_info", {"graph_name": graph})
    return {
        "id": stem,
        "graph": graph,
        "created": created,
        "optimum": optimum,
        "overlay": overlay,
        "marker_display_lift": marker_lift,
        "projection": "minimum-perspective 2.5D",
        "camera": {"azimuth": 135, "inclination": 68, "roll": 0},
        "filled_levels": 19,
        "surface_contour_lines": 6,
        "view": view,
        "graph_info": info,
        "exports": exports,
        "role": "AUXILIARY FIGURE",
        **({"adaptation": "TEMPLATE_ADAPTATION_REQUIRED"} if adaptation else {}),
    }


async def render_surfaces(session: ClientSession) -> list[dict[str, Any]]:
    return [
        await render_surface(
            session,
            data_path=BENCH / "two_parameter_objective.csv",
            optimum_path=BENCH / "two_parameter_optimum.csv",
            graph_request="P2R_SURFACE_3D",
            stem="P2_SURFACE_3D_25D_REDESIGN",
            z_limits=(0, 36, 6),
            adaptation=False,
        ),
        await render_surface(
            session,
            data_path=BENCH / "phase2_surface_stress.csv",
            optimum_path=BENCH / "phase2_surface_stress_optimum.csv",
            graph_request="P2R_SURFACE_3D_STRESS",
            stem="P2_SURFACE_3D_25D_REDESIGN_STRESS",
            z_limits=(0, 100, 20),
            adaptation=True,
        ),
    ]


async def render(session: ClientSession) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    p2.OUTPUT = OUTPUT
    ping = await r2.base.call(session, "origin_ping", {"show": True})
    fresh = await r2.base.call(session, "origin_new_project", {"show": True})
    multipanels = await render_multipanels(session)
    surfaces = await render_surfaces(session)
    source = await r2.base.call(
        session,
        "origin_save_project",
        {"path": str(OUTPUT / "ORIGIN_PHASE2_MULTIPANEL_SURFACE_REFINEMENT.opju"), "overwrite": True},
    )
    return {
        "phase": "Phase 2 — Multi-panel refinement and auxiliary 3D redesign",
        "frozen_templates_modified": False,
        "ping": ping,
        "fresh_project": fresh,
        "multipanels": multipanels,
        "surfaces": surfaces,
        "source_project": source,
    }


async def save_templates(session: ClientSession) -> dict[str, Any]:
    candidates = [
        (
            "SCP_MULTIPANEL_2X2_v21_REFINED_CANDIDATE",
            "P2R_MULTIPANEL_2X2",
            ["multi-panel", "line"],
            ["displacement", "velocity", "power", "error", "shared-legend", "shared-x-title", "panel-labels"],
            9,
        ),
        (
            "SCP_SURFACE_3D_AUXILIARY_v21_REDESIGN_CANDIDATE",
            "Graph9",
            ["surface-3d", "scatter-3d"],
            ["x", "y", "z", "optimum", "colorbar", "auxiliary", "2.5d"],
            3,
        ),
    ]
    saved = []
    for name, graph, plot_types, roles, n_columns in candidates:
        saved.append(
            await r2.base.call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": (
                        "Phase 2 post-review candidate. Multi-panel has compact composite typography; "
                        "3D is a low-perspective 2.5D AUXILIARY figure. Human approval pending. "
                        "No FROZEN template was loaded or modified."
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
        "status": "POST-REVIEW CANDIDATES — HUMAN APPROVAL PENDING",
        "frozen_templates_modified": False,
        "saved": saved,
        "library_after": await r2.base.call(session, "origin_list_user_templates", {}),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


async def run(mode: str) -> None:
    prepare_surface_palette()
    env = dict(os.environ)
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
                target = LOG_DIR / "phase2_refinement_mcp_execution.json"
            else:
                result = await save_templates(session)
                target = LOG_DIR / "phase2_refinement_template_save.json"
            target.write_text(json.dumps(r2.base.jsonable(result), ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"mode": mode, "result_file": str(target)}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("render", "save-templates"))
    args = parser.parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
