"""Render the GRAPH EDITOR BLIND TEST MAIN figures through Origin MCP.

Python is used only for MCP orchestration. Origin creates, styles, merges,
exports, and saves every graph. Frozen templates are instantiated but never
saved over or modified in the template library.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import origin_round2 as r2


SYSTEM = Path(__file__).resolve().parents[1]
DATA = SYSTEM / "blind_test_workspace" / "figure_data"
OUT = SYSTEM / "outputs" / "graph_editor_blind_test"
LOG = SYSTEM / "training_data" / "blind_test_mcp_execution.json"
PROJECT = OUT / "ORIGIN_GRAPH_EDITOR_BLIND_TEST.opju"
PYTHON_EXE = r2.PYTHON_EXE

PRIMARY = [31, 78, 121]
HIGHLIGHT = [201, 123, 42]
SECONDARY = [118, 163, 181]
GREEN = [93, 141, 124]
NEUTRAL = [150, 154, 160]
INK = [43, 47, 51]
LIGHT = [205, 208, 211]


def j(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): j(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [j(v) for v in value]
    return value


def worksheet_ref(result: dict[str, Any]) -> str:
    ws = r2.base.find_key(result, "worksheet")
    if not isinstance(ws, dict):
        raise RuntimeError(f"No worksheet in MCP response: {result}")
    return f"[{ws['book_name']}]{ws['sheet_name']}"


def graph_name(result: dict[str, Any]) -> str:
    name = r2.base.find_key(result, "graph_name") or r2.base.find_key(result, "output_graph")
    if not isinstance(name, str) or not name:
        raise RuntimeError(f"No graph name in MCP response: {result}")
    return name


async def call(session: ClientSession, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return await r2.base.call(session, name, args)


async def script(session: ClientSession, text: str) -> dict[str, Any]:
    return await call(session, "origin_run_labtalk", {"script": text})


async def set_style(session: ClientSession, graph: str, plot: int, *, layer: int = 0, **style: Any):
    return await call(
        session,
        "origin_set_plot_style",
        {"graph_name": graph, "layer_index": layer, "plot_index": plot, **style},
    )


async def set_axes(
    session: ClientSession,
    graph: str,
    x: tuple[float, float, float, str],
    y: tuple[float, float, float, str],
    *,
    layer: int = 0,
):
    return [
        await call(
            session,
            "origin_set_axis",
            {"graph_name": graph, "layer_index": layer, "axis": "x", "start": x[0], "end": x[1], "step": x[2], "title": x[3]},
        ),
        await call(
            session,
            "origin_set_axis",
            {"graph_name": graph, "layer_index": layer, "axis": "y", "start": y[0], "end": y[1], "step": y[2], "title": y[3]},
        ),
    ]


async def compact(session: ClientSession, graph: str, *, panel: bool = False):
    if panel:
        sizes = dict(axis_title_size=5.2, tick_label_size=4.6, legend_font_size=4.2, tick_length=1.25)
        page = (1200, 800)
        geom = {"layer_index": 0, "left": 15, "top": 5, "width": 80, "height": 80}
    else:
        sizes = dict(axis_title_size=7, tick_label_size=6, legend_font_size=5, tick_length=2)
        page = (1800, 1200)
        geom = {"layer_index": 0, "left": 17, "top": 6, "width": 77, "height": 69}
    await r2.base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph,
            "chart_type": "line",
            "page_width": page[0],
            "page_height": page[1],
            "font_family": "Arial",
            **sizes,
            "line_width": 1.0,
            "symbol_size": 3.0,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    await call(session, "origin_arrange_layers", {"graph_name": graph, "rows": 1, "columns": 1, "layer_geometries": [geom]})
    await call(session, "origin_format_graph", {"graph_name": graph, "show_legend": False, "rescale": False})
    await script(session, r2.base_labtalk(graph))
    await script(
        session,
        f'win -a "{graph}"; layer -s 1; layer.border=0; layer.x2.showAxes=0; layer.y2.showAxes=0; '
        f'layer.x2.ticks=0; layer.y2.ticks=0; layer.x.thickness=0.40; layer.y.thickness=0.40; '
        f'layer.x.tickthickness=0.32; layer.y.tickthickness=0.32; doc -uw;',
    )


def label(graph: str, name: str, text: str, x: float, y: float, color: list[int], size: float = 4.7) -> str:
    escaped = text.replace('"', '\\"')
    return (
        f'win -a "{graph}"; layer -s 1; double lx={x}; double ly={y}; '
        f'label -a lx ly -n {name} "{escaped}"; {name}.font=font(Arial); '
        f'{name}.fsize={size}; {name}.color={r2.rgb_expr(color)}; '
        f'{name}.background=0; {name}.clip=0; doc -uw; sec -p 0.05;'
    )


async def export(session: ClientSession, graph: str, stem: str, width: int = 2400):
    OUT.mkdir(parents=True, exist_ok=True)
    await script(session, "@MGI=1; @MGR=1; expGraph.DPI=600;")
    results = []
    for ext in ("png", "pdf", "svg"):
        results.append(
            await call(
                session,
                "origin_export_graph",
                {"graph_name": graph, "path": str(OUT / f"{stem}.{ext}"), "overwrite": True, "width": width if ext == "png" else 0},
            )
        )
    return results


async def render_calibration(session: ClientSession):
    fit = await call(
        session,
        "origin_plot_scatter",
        {
            "path": str(DATA / "main1_measured_display.csv"),
            "x_col": "time_s",
            "y_cols": ["measured_C"],
            "graph_name": "BT_F1_FIT",
            "template": "SCP_SCATTER_FIT_v20_FROZEN",
            "show_legend": False,
        },
    )
    gfit = graph_name(fit)
    model = await call(session, "origin_import_table", {"path": str(DATA / "main1_model_line.csv"), "book_name": "BT_CAL_MODEL", "sheet_name": "Curve"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(model), "x_col": 0, "y_col": 1, "graph_name": gfit, "plot_type": "l"})
    await compact(session, gfit, panel=True)
    await set_style(session, gfit, 0, color=NEUTRAL, symbol_kind=3, symbol_size=0.62, line_width=0.0, transparency=18)
    await set_style(session, gfit, 1, color=PRIMARY, line_width=1.25, line_style=0, symbol_size=0.0)
    await script(
        session,
        f'win -a "{gfit}"; layer -s 1; range pm=!1; range pf=!2; '
        f'set pm -c {r2.rgb_expr(NEUTRAL)}; set pm -k 2; set pm -z 0.8; '
        f'set pf -c {r2.rgb_expr(PRIMARY)}; set pf -wp 0.72; doc -uw;',
    )
    await set_axes(session, gfit, (19, 373, 50, ""), (25, 250, 25, "Temperature (°C)"))
    await script(session, f'win -a "{gfit}"; label -r P2Fit; label -r P2Outlier; doc -uw;')
    await script(session, f'win -a "{gfit}"; layer -s 1; xb.text$=""; doc -uw;')
    await script(session, label(gfit, "BTFitLabel", "Model", 320, 178, PRIMARY, 4.2))
    await script(session, label(gfit, "BTMeasuredLabel", "Measured", 58, 86, NEUTRAL, 4.1))

    res = await call(
        session,
        "origin_plot_scatter",
        {
            "path": str(DATA / "main1_residual_display.csv"),
            "x_col": "time_s",
            "y_cols": ["residual_C"],
            "graph_name": "BT_F1_RES",
            "show_legend": False,
        },
    )
    gres = graph_name(res)
    await compact(session, gres, panel=True)
    await set_style(session, gres, 0, color=SECONDARY, symbol_kind=3, symbol_size=0.55, line_width=0.0, transparency=22)
    await script(session, f'win -a "{gres}"; layer -s 1; range pr=!1; set pr -c {r2.rgb_expr(SECONDARY)}; set pr -k 2; set pr -z 0.8; doc -uw;')
    await set_axes(session, gres, (19, 373, 50, "Time (s)"), (-6, 6, 2, "Residual (°C)"))
    await script(
        session,
        f'win -a "{gres}"; layer -s 1; draw -n BTZero -l {{19,0,373,0}}; BTZero.color={r2.rgb_expr(LIGHT)}; BTZero.width=0.45; doc -uw;',
    )
    await script(session, label(gres, "BTResidualPanel", "(b)", 28, 5.1, INK, 4.6))
    merged = await call(
        session,
        "origin_merge_graphs",
        {
            "graph_names": [gfit, gres], "output_name": "BT_MAIN1_CALIBRATION", "rows": 2, "columns": 1,
            "keep_sources": True, "arrange": True, "gap_y": 1.8, "margins": [7, 5, 5, 7], "unit": "percent", "label_style": "none", "common_x_scale": True,
        },
    )
    graph = graph_name(merged)
    await script(session, f'win -a "{graph}"; page.width=1800; page.height=1500; doc -uw;')
    await call(
        session,
        "origin_arrange_layers",
        {"graph_name": graph, "rows": 2, "columns": 1, "layer_geometries": [
            {"layer_index": 0, "left": 15, "top": 5, "width": 80, "height": 58},
            {"layer_index": 1, "left": 15, "top": 69, "width": 80, "height": 23},
        ]},
    )
    await script(
        session,
        f'win -a "{graph}"; layer -s 1; layer.border=0; layer.x2.showAxes=0; layer.y2.showAxes=0; '
        f'layer.x.thickness=0.38; layer.y.thickness=0.38; layer.x.tickthickness=0.30; layer.y.tickthickness=0.30; '
        f'layer.x.label.pt=3.8; layer.y.label.pt=3.8; xb.fsize=4.4; yl.fsize=4.4; '
        f'label -a 27 243 -n BTPA "(a)"; BTPA.fsize=4.8; BTPA.bold=1; '
        f'layer -s 2; layer.border=0; layer.x2.showAxes=0; layer.y2.showAxes=0; '
        f'layer.x.thickness=0.38; layer.y.thickness=0.38; layer.x.tickthickness=0.30; layer.y.tickthickness=0.30; '
        f'layer.x.label.pt=3.8; layer.y.label.pt=3.8; xb.fsize=4.4; yl.fsize=4.4; '
        f'label -n BTPB "(b)"; BTPB.attach=2; BTPB.x=40; BTPB.y=4.8; BTPB.fsize=4.8; BTPB.bold=1; doc -uw;',
    )
    return {"graph": graph, "exports": await export(session, graph, "MAIN1_MODEL_CALIBRATION", 2700)}


async def render_q1(session: ClientSession):
    made = await call(
        session,
        "origin_plot_line",
        {
            "path": str(DATA / "main2_q1_profiles.csv"), "x_col": "time_s", "y_cols": ["air_C", "temperature_C"],
            "graph_name": "BT_MAIN2_Q1", "template": "SCP_MULTI_LINE_COMPARISON_v11_FROZEN", "show_legend": False,
        },
    )
    graph = graph_name(made)
    points = await call(session, "origin_import_table", {"path": str(DATA / "main2_q1_checkpoints.csv"), "book_name": "BT_Q1_POINTS", "sheet_name": "Checkpoints"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(points), "x_col": "time_s", "y_col": "checkpoint_C", "graph_name": graph, "plot_type": "s"})
    await compact(session, graph)
    await set_style(session, graph, 0, color=NEUTRAL, line_width=0.72, line_style=1)
    await set_style(session, graph, 1, color=PRIMARY, line_width=1.45, line_style=0)
    await set_style(session, graph, 2, color=HIGHLIGHT, symbol_kind=2, symbol_size=2.75, line_width=0.25)
    await set_axes(session, graph, (0, 340, 50, "Time (s)"), (20, 270, 50, "Temperature (°C)"))
    await script(session, f'win -a "{graph}"; label -r V11Proposed; label -r V11Conservative; label -r V11Aggressive; label -r V11Baseline; doc -uw;')
    for args in [
        ("BTQ1Air", "Furnace air", 270, 252, NEUTRAL, 4.4),
        ("BTQ1PCB", "PCB center", 274, 188, PRIMARY, 4.5),
        ("BTQ1P1", "129.9°C", 88, 139, HIGHLIGHT, 4.0),
        ("BTQ1P2", "170.8°C", 169, 181, HIGHLIGHT, 4.0),
        ("BTQ1P3", "190.7°C", 197, 201, HIGHLIGHT, 4.0),
        ("BTQ1P4", "225.0°C", 236, 235, HIGHLIGHT, 4.0),
    ]:
        await script(session, label(graph, *args))
    return {"graph": graph, "exports": await export(session, graph, "MAIN2_Q1_THERMAL_RESPONSE")}


async def render_q2(session: ClientSession):
    made = await call(
        session,
        "origin_plot_line",
        {
            "path": str(DATA / "main3_q2_peak_vs_speed.csv"), "x_col": "speed_cm_min", "y_cols": ["peak"],
            "graph_name": "BT_MAIN3_Q2", "template": "SCP_SINGLE_LINE_MAIN_v11_FROZEN", "show_legend": False,
        },
    )
    graph = graph_name(made)
    lower = await call(session, "origin_import_table", {"path": str(DATA / "main3_q2_lower_limit.csv"), "book_name": "BT_Q2_LOW", "sheet_name": "Line"})
    upper = await call(session, "origin_import_table", {"path": str(DATA / "main3_q2_upper_limit.csv"), "book_name": "BT_Q2_HIGH", "sheet_name": "Line"})
    for item in (lower, upper):
        await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(item), "x_col": 0, "y_col": 1, "graph_name": graph, "plot_type": "l"})
    selected = await call(session, "origin_import_table", {"path": str(DATA / "main3_q2_selected.csv"), "book_name": "BT_Q2_SELECTED", "sheet_name": "Point"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(selected), "x_col": 0, "y_col": 1, "graph_name": graph, "plot_type": "s"})
    await compact(session, graph)
    await set_style(session, graph, 0, color=PRIMARY, line_width=1.36, line_style=0)
    await set_style(session, graph, 1, color=NEUTRAL, line_width=0.55, line_style=2)
    await set_style(session, graph, 2, color=LIGHT, line_width=0.45, line_style=2)
    await set_style(session, graph, 3, color=HIGHLIGHT, symbol_kind=2, symbol_size=3.05, line_width=0.25)
    await set_axes(session, graph, (65, 100, 5, "Conveyor speed (cm/min)"), (231, 251, 2, "Peak temperature (°C)"))
    await script(session, label(graph, "BTQ2Curve", "Peak temperature", 88.5, 235.2, PRIMARY, 4.3))
    await script(session, label(graph, "BTQ2Limit", "240°C lower limit", 84.5, 240.75, NEUTRAL, 4.0))
    await script(session, label(graph, "BTQ2Selected", "77.871 cm/min", 78.6, 241.15, HIGHLIGHT, 4.0))
    return {"graph": graph, "exports": await export(session, graph, "MAIN3_Q2_MAXIMUM_SPEED")}


async def render_q3(session: ClientSession):
    made = await call(
        session,
        "origin_plot_line",
        {
            "path": str(DATA / "main4_q3_objective_area.csv"), "x_col": "time_s", "y_cols": ["temperature_C"],
            "graph_name": "BT_MAIN4_Q3", "template": "SCP_SINGLE_LINE_MAIN_v11_FROZEN", "show_legend": False,
        },
    )
    graph = graph_name(made)
    extras = []
    for path, book in [
        ("main4_q3_threshold.csv", "BT_Q3_THRESHOLD"),
        ("main4_q3_area_upper.csv", "BT_Q3_AREA_UPPER"),
        ("main4_q3_area_lower.csv", "BT_Q3_AREA_LOWER"),
    ]:
        item = await call(session, "origin_import_table", {"path": str(DATA / path), "book_name": book, "sheet_name": "Data"})
        extras.append(item)
        await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(item), "x_col": 0, "y_col": 1, "graph_name": graph, "plot_type": "l"})
    peak = await call(session, "origin_import_table", {"path": str(DATA / "main4_q3_peak.csv"), "book_name": "BT_Q3_PEAK", "sheet_name": "Point"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(peak), "x_col": 0, "y_col": 1, "graph_name": graph, "plot_type": "s"})
    await compact(session, graph)
    await set_style(session, graph, 0, color=PRIMARY, line_width=1.36, line_style=0)
    await set_style(session, graph, 1, color=NEUTRAL, line_width=0.55, line_style=2)
    await set_style(session, graph, 2, color=HIGHLIGHT, line_width=0.0, transparency=82)
    await set_style(session, graph, 3, color=HIGHLIGHT, line_width=0.0, transparency=100)
    await set_style(session, graph, 4, color=HIGHLIGHT, symbol_kind=2, symbol_size=3.05, line_width=0.25)
    await set_axes(session, graph, (0, 300, 50, "Time (s)"), (20, 255, 50, "PCB center temperature (°C)"))
    await script(
        session,
        f'win -a "{graph}"; layer -s 1; range BTArea=!3; set BTArea -pf 1; set BTArea -pfv 9; '
        f'set BTArea -pfb {r2.rgb_expr([236, 210, 175])}; set BTArea -p2fb {r2.rgb_expr([236, 210, 175])}; '
        f'set BTArea -paap 20; set BTArea -c {r2.rgb_expr(HIGHLIGHT)}; set BTArea -wp 0.35; '
        f'range BTFloor=!4; set BTFloor -w 0; doc -uw; sec -p 0.1;',
    )
    await script(session, label(graph, "BTQ3Threshold", "217°C", 270, 212, NEUTRAL, 4.1))
    await script(session, label(graph, "BTQ3Area", "Area = 419.599°C·s", 165, 204, HIGHLIGHT, 4.1))
    await script(session, label(graph, "BTQ3Peak", "Selected", 239, 244, HIGHLIGHT, 4.2))
    return {"graph": graph, "exports": await export(session, graph, "MAIN4_Q3_LOW_AREA_DESIGN")}


async def render_q4(session: ClientSession):
    cloud = await call(
        session,
        "origin_plot_scatter",
        {"path": str(DATA / "main5_q4_cloud_display.csv"), "x_col": "area_C_s", "y_cols": ["asymmetry_C"], "graph_name": "BT_Q4_TRADEOFF", "show_legend": False},
    )
    ga = graph_name(cloud)
    front = await call(session, "origin_import_table", {"path": str(DATA / "main5_q4_nondominated_frontier.csv"), "book_name": "BT_Q4_FRONT", "sheet_name": "Front"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(front), "x_col": "area_C_s", "y_col": "asymmetry_C", "graph_name": ga, "plot_type": "l"})
    q3p = await call(session, "origin_import_table", {"path": str(DATA / "main5_q4_selected_q3.csv"), "book_name": "BT_Q4_Q3", "sheet_name": "Point"})
    q4p = await call(session, "origin_import_table", {"path": str(DATA / "main5_q4_selected_q4.csv"), "book_name": "BT_Q4_Q4", "sheet_name": "Point"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(q3p), "x_col": "area_C_s", "y_col": "asymmetry_C", "graph_name": ga, "plot_type": "s"})
    await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(q4p), "x_col": "area_C_s", "y_col": "asymmetry_C", "graph_name": ga, "plot_type": "s"})
    await compact(session, ga, panel=True)
    await set_style(session, ga, 0, color=NEUTRAL, symbol_kind=3, symbol_size=0.36, line_width=0.0, transparency=58)
    await set_style(session, ga, 1, color=PRIMARY, line_width=0.9, line_style=0)
    await set_style(session, ga, 2, color=PRIMARY, symbol_kind=1, symbol_size=2.8, line_width=0.25)
    await set_style(session, ga, 3, color=HIGHLIGHT, symbol_kind=2, symbol_size=3.2, line_width=0.25)
    await script(
        session,
        f'win -a "{ga}"; layer -s 1; range pc=!1; set pc -c {r2.rgb_expr(NEUTRAL)}; set pc -k 2; set pc -z 0.72; '
        f'range p3=!3; set p3 -z 3.0; range p4=!4; set p4 -z 3.2; doc -uw;',
    )
    await set_axes(session, ga, (415, 455, 10, "Pre-peak excess area (°C·s)"), (1.5, 2.6, 0.2, "Asymmetry metric (°C)"))
    await script(session, label(ga, "BTQ4Q3", "Q3", 421.1, 1.78, PRIMARY, 4.1))
    await script(session, label(ga, "BTQ4Q4", "Q4 selected", 424.0, 1.58, HIGHLIGHT, 4.1))
    await script(session, label(ga, "BTQ4Scope", "verified feasible sample", 428.5, 2.47, NEUTRAL, 3.3))

    q3 = await call(session, "origin_plot_line", {"path": str(DATA / "main5_q4_mirror_q3.csv"), "x_col": "relative_time_s", "y_cols": ["heating_C", "cooling_C"], "graph_name": "BT_Q4_MIRROR", "show_legend": False})
    gb = graph_name(q3)
    q4 = await call(session, "origin_import_table", {"path": str(DATA / "main5_q4_mirror_q4.csv"), "book_name": "BT_Q4_MIRROR_Q4", "sheet_name": "Branches"})
    for col in ("heating_C", "cooling_C"):
        await call(session, "origin_add_plot_to_graph", {"worksheet": worksheet_ref(q4), "x_col": "relative_time_s", "y_col": col, "graph_name": gb, "plot_type": "l"})
    await compact(session, gb, panel=True)
    await set_style(session, gb, 0, color=NEUTRAL, line_width=0.72, line_style=0)
    await set_style(session, gb, 1, color=NEUTRAL, line_width=0.72, line_style=2)
    await set_style(session, gb, 2, color=PRIMARY, line_width=1.15, line_style=0)
    await set_style(session, gb, 3, color=PRIMARY, line_width=1.15, line_style=2)
    await set_axes(session, gb, (0, 27, 5, "Peak-relative time (s)"), (216, 242, 5, "Temperature (°C)"))
    await script(session, label(gb, "BTQ4Design", "Q4 selected", 13.7, 232.0, PRIMARY, 4.0))
    await script(session, label(gb, "BTQ3Design", "Q3", 18.0, 223.8, NEUTRAL, 3.9))
    await script(session, label(gb, "BTQ4LineKey", "solid: heating · dashed: cooling", 1.0, 217.0, INK, 3.4))
    await script(session, label(gb, "BTMirrorPanel", "(b)", 1.0, 239.0, INK, 4.4))

    merged = await call(
        session,
        "origin_merge_graphs",
        {"graph_names": [ga, gb], "output_name": "BT_MAIN5_Q4", "rows": 1, "columns": 2, "keep_sources": True, "arrange": True,
         "gap_x": 2.5, "margins": [5, 5, 4, 7], "unit": "percent", "label_style": "none"},
    )
    graph = graph_name(merged)
    await script(session, f'win -a "{graph}"; page.width=2800; page.height=1100; doc -uw;')
    await call(
        session,
        "origin_arrange_layers",
        {"graph_name": graph, "rows": 1, "columns": 2, "layer_geometries": [
            {"layer_index": 0, "left": 14, "top": 8, "width": 32, "height": 66},
            {"layer_index": 1, "left": 65, "top": 8, "width": 30, "height": 66},
        ]},
    )
    await script(
        session,
        f'win -a "{graph}"; layer -s 1; layer.border=0; layer.x2.showAxes=0; layer.y2.showAxes=0; '
        f'layer.x.thickness=0.35; layer.y.thickness=0.35; layer.x.tickthickness=0.28; layer.y.tickthickness=0.28; '
        f'layer.x.label.pt=2.7; layer.y.label.pt=2.7; xb.fsize=3.4; yl.fsize=3.4; '
        f'label -a 416.2 2.54 -n BTQ4PA "(a)"; BTQ4PA.attach=2; BTQ4PA.fsize=4.5; BTQ4PA.bold=1; '
        f'layer -s 2; layer.border=0; layer.x2.showAxes=0; layer.y2.showAxes=0; '
        f'layer.x.thickness=0.35; layer.y.thickness=0.35; layer.x.tickthickness=0.28; layer.y.tickthickness=0.28; '
        f'layer.x.label.pt=2.7; layer.y.label.pt=2.7; xb.fsize=3.4; yl.fsize=3.4; '
        f'label -n BTQ4PB "(b)"; BTQ4PB.attach=2; BTQ4PB.x=1.0; BTQ4PB.y=239.5; BTQ4PB.fsize=4.5; BTQ4PB.bold=1; doc -uw;',
    )
    return {"graph": graph, "exports": await export(session, graph, "MAIN5_Q4_SYMMETRY_COMPROMISE", 3000)}


async def run():
    env = dict(os.environ)
    env["ORIGIN_MCP_TOOL_PROFILE"] = "full"
    env["ORIGIN_MCP_ALLOWED_ROOTS"] = str(SYSTEM)
    params = StdioServerParameters(command=str(PYTHON_EXE), args=["-m", "origin_mcp"], env=env, cwd=str(SYSTEM.parent))
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await r2.base.bridge_task(session, "new_project", {"show": True})
            figures = []
            for name, renderer in [
                ("MAIN1", render_calibration), ("MAIN2", render_q1), ("MAIN3", render_q2), ("MAIN4", render_q3), ("MAIN5", render_q4)
            ]:
                print(f"rendering {name}", flush=True)
                figures.append({"id": name, **await renderer(session)})
            saved = await call(session, "origin_save_project", {"path": str(PROJECT)})
            result = {"figures": figures, "project": saved, "frozen_templates_modified": False}
            LOG.write_text(json.dumps(j(result), ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"ok": True, "log": str(LOG), "project": str(PROJECT)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(run())
