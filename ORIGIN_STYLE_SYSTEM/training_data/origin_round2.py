"""Second-round Origin MCP refinement: Signature Scientific Style v1."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import origin_round1 as base


SYSTEM_ROOT = base.SYSTEM_ROOT
BENCH = base.BENCH
OUTPUT = base.OUTPUT / "round2"
LOG_DIR = base.LOG_DIR
PYTHON_EXE = base.PYTHON_EXE

# Signature Scientific Style v1: muted, printable, and role-driven.
PRIMARY = [31, 78, 121]
HIGHLIGHT = [201, 123, 42]
NEUTRAL = [150, 154, 160]
SECONDARY = [118, 163, 181]
GREEN = [93, 141, 124]
PURPLE = [145, 126, 163]

CONTOUR_COLORS = [
    [36, 75, 102],
    [47, 102, 127],
    [63, 131, 147],
    [88, 160, 159],
    [120, 183, 159],
    [154, 201, 150],
    [186, 216, 142],
    [214, 227, 140],
    [232, 233, 155],
    [242, 236, 177],
]


def build_specs() -> list[dict[str, Any]]:
    specs = deepcopy(base.build_specs())
    ids = [
        "R2_B01_single_line_main",
        "R2_B02_multi_line_comparison",
        "R2_B03_sensitivity_analytical",
    ]
    for spec, figure_id in zip(specs, ids):
        spec["figure"]["id"] = figure_id
        spec["figure"]["title"] = figure_id
        spec["annotations"] = []
        spec["style"].update(
            {
                "font_family": "Arial",
                "annotation_font_size": 6,
                "palette_role": "signature-scientific-v1",
            }
        )
    specs[1]["layers"][0]["x"]["limits"] = [0, 27.5]
    specs[2]["layers"][0]["x"]["limits"] = [-20, 23.5]
    return specs


SERIES_STYLES: dict[str, list[dict[str, Any]]] = {
    "R2_B01_single_line_main": [
        {"color": PRIMARY, "line_width": 1.45, "line_style": 0},
        {
            "color": HIGHLIGHT,
            "symbol_kind": 2,
            "symbol_size": 3.3,
            "line_width": 0.35,
        },
    ],
    "R2_B02_multi_line_comparison": [
        {"color": NEUTRAL, "line_width": 0.75, "line_style": 1},
        {"color": SECONDARY, "line_width": 0.85, "line_style": 2},
        {"color": GREEN, "line_width": 0.90, "line_style": 3},
        {"color": PRIMARY, "line_width": 1.50, "line_style": 0},
    ],
    "R2_B03_sensitivity_analytical": [
        {"color": SECONDARY, "line_width": 0.90, "line_style": 1},
        {"color": GREEN, "line_width": 0.90, "line_style": 2},
        {"color": PRIMARY, "line_width": 1.50, "line_style": 0},
        {"color": PURPLE, "line_width": 0.90, "line_style": 3},
    ],
}


def rgb_expr(rgb: list[int]) -> str:
    return f'color("#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")'


def base_labtalk(graph_name: str, *, keep_frame: bool = False) -> str:
    opposite = 1 if keep_frame else 0
    return (
        f'win -a "{graph_name}"; layer -s 1; '
        "layer.color=color(white); layer.border=0; "
        "layer.x.grid.show=0; layer.y.grid.show=0; "
        "layer.x.showGrids=0; layer.y.showGrids=0; "
        "axis -ps X A 1; axis -ps Y A 1; "
        "layer.x.showAxes=1; layer.y.showAxes=1; "
        "layer.x.showLabels=1; layer.y.showLabels=1; "
        "layer.x.showlabel=1; layer.y.showlabel=1; "
        f"layer.x.opposite={opposite}; layer.y.opposite={opposite}; "
        f"layer.x.showopposite={opposite}; layer.y.showopposite={opposite}; "
        "layer.x2.showlabel=0; layer.y2.showlabel=0; "
        f"layer.x2.showopposite={opposite}; layer.y2.showopposite={opposite}; "
        "layer.x2.ticks=0; layer.y2.ticks=0; "
        "layer.x.thickness=0.45; layer.y.thickness=0.45; "
        "layer.x2.thickness=0.45; layer.y2.thickness=0.45; "
        "layer.x.tickthickness=0.45; layer.y.tickthickness=0.45; "
        "layer.x.mtickthickness=0.35; layer.y.mtickthickness=0.35; "
        "layer.x.label.font=font(Arial); layer.y.label.font=font(Arial); "
        "layer.x.label.fsize=5.8; layer.y.label.fsize=5.8; "
        "xb.font=font(Arial); yl.font=font(Arial); "
        "xb.fsize=6.5; yl.fsize=6.5; "
        "doc -e D { set %C -q 0; }; "
        "doc -uw; sec -p 0.1;"
    )


async def apply_compact_style(
    session: ClientSession,
    graph_name: str,
    figure_id: str,
    *,
    chart_type: str = "line",
) -> dict[str, Any]:
    nature = await base.bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph_name,
            "chart_type": chart_type,
            "page_width": 1800,
            "page_height": 1200,
            "font_family": "Arial",
            "axis_title_size": 7,
            "tick_label_size": 6,
            "legend_font_size": 5,
            "line_width": 1.0,
            "symbol_size": 4.0,
            "tick_length": 2,
            "show_legend": False,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    geometry = (
        {"layer_index": 0, "left": 17, "top": 6, "width": 56, "height": 69}
        if chart_type == "contour"
        else {"layer_index": 0, "left": 17, "top": 6, "width": 77, "height": 69}
    )
    arranged = await base.bridge_task(
        session,
        "arrange_layers",
        {
            "graph_name": graph_name,
            "rows": 1,
            "columns": 1,
            "layer_geometries": [geometry],
        },
    )
    styled = []
    for plot_index, style in enumerate(SERIES_STYLES.get(figure_id, [])):
        styled.append(
            await base.call(
                session,
                "origin_set_plot_style",
                {
                    "graph_name": graph_name,
                    "layer_index": 0,
                    "plot_index": plot_index,
                    **style,
                },
            )
        )
    formatted = await base.call(
        session,
        "origin_format_graph",
        {"graph_name": graph_name, "show_legend": False, "rescale": False},
    )
    # Apply these last: Origin's plot/graph-format helpers can restore template
    # grid, frame, and endpoint-label settings as a side effect.
    cleaned = await base.call(
        session,
        "origin_run_labtalk",
        {"script": base_labtalk(graph_name, keep_frame=chart_type == "contour")},
    )
    return {
        "nature": nature,
        "arrange": arranged,
        "base_labtalk": cleaned,
        "series": styled,
        "format": formatted,
    }


def label_script(
    graph_name: str,
    name: str,
    text: str,
    x: float,
    y: float,
    color: list[int],
    *,
    bold: bool = False,
    font_size: float = 4.8,
) -> str:
    return (
        f'win -a "{graph_name}"; layer -s 1; '
        f"label -n {name} {text}; {name}.attach=2; "
        f"{name}.x={x}; {name}.y={y}; {name}.anchor=27; "
        f"{name}.font=font(Arial); {name}.fsize={font_size}; "
        f"{name}.color={rgb_expr(color)}; {name}.background=0; "
        f"{name}.clip=0; doc -uw; sec -p 0.1;"
    )


async def add_multi_labels(session: ClientSession, graph_name: str) -> list[dict[str, Any]]:
    # Baseline and Aggressive finish less than 0.4 units apart. Tiny leaders keep
    # the labels honest while preserving direct identification.
    scripts = [
        label_script(graph_name, "R2Baseline", "Baseline", 24.55, 70.6, [108, 112, 118]),
        label_script(
            graph_name,
            "R2Conservative",
            "Conservative",
            24.55,
            80.70,
            [79, 128, 148],
        ),
        label_script(graph_name, "R2Aggressive", "Aggressive", 24.55, 74.8, [63, 111, 96]),
        label_script(graph_name, "R2Proposed", "Proposed", 24.55, 93.06, PRIMARY, bold=True),
    ]
    return [
        await base.call(session, "origin_run_labtalk", {"script": script})
        for script in scripts
    ]


async def add_sensitivity_analysis(
    session: ClientSession, graph_name: str
) -> list[dict[str, Any]]:
    scripts = [
        (
            f'win -a "{graph_name}"; layer -s 1; '
            "draw -n R2ZeroLine -l -h 0; R2ZeroLine.attach=2; "
            "R2ZeroLine.color=color(198,203,209); "
            "R2ZeroLine.lineWidth=0.45; R2ZeroLine.lineType=1; "
            "R2ZeroLine.back=1; doc -uw; sec -p 0.1;"
        ),
        label_script(graph_name, "R2Demand", "Demand", 20.45, 19.0, [79, 128, 148]),
        label_script(graph_name, "R2Capacity", "Capacity", 20.45, -6.25, [63, 111, 96]),
        label_script(graph_name, "R2UnitCost", "Unit cost", 20.10, 20.8, PRIMARY, bold=True),
        label_script(graph_name, "R2Efficiency", "Efficiency", 20.45, -8.35, [112, 93, 132]),
    ]
    return [
        await base.call(session, "origin_run_labtalk", {"script": script})
        for script in scripts
    ]


async def export_graph_set(
    session: ClientSession, graph_name: str, stem: str
) -> list[dict[str, Any]]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_dir = str(OUTPUT).replace("\\", "/")
    exports = [
        await base.call(
            session,
            "origin_run_labtalk",
            {
                "script": (
                    f'win -a "{graph_name}"; '
                    f'expGraph type:=png path:="{output_dir}" filename:="{stem}" '
                    "overwrite:=replace tr1.unit:=2 tr1.width:=2400 "
                    "tr2.png.dotsperinch:=600;"
                )
            },
        )
    ]
    for suffix in ("pdf", "svg"):
        exports.append(
            await base.call(
                session,
                "origin_export_graph",
                {
                    "path": str(OUTPUT / f"{stem}.{suffix}"),
                    "graph_name": graph_name,
                    "overwrite": True,
                    "width": 0,
                },
            )
        )
    return exports


def load_objective_matrix() -> tuple[list[list[float]], list[float], list[float]]:
    return base.load_objective_matrix()


async def render_contour(session: ClientSession) -> dict[str, Any]:
    figure_id = "R2_B04_contour_main"
    matrix, xs, ys = load_objective_matrix()
    created = await base.call(
        session,
        "origin_create_matrix",
        {
            "data": matrix,
            "book_name": "R2_B04_Field",
            "sheet_name": "Objective",
            "xymap": [xs[0], xs[-1], ys[0], ys[-1]],
            "labels": ["Objective value"],
        },
    )
    data_ranges = base.find_key(created, "data_ranges")
    if not isinstance(data_ranges, list) or not data_ranges:
        raise RuntimeError(f"Matrix creation returned no data range: {created}")
    plotted = await base.bridge_task(
        session,
        "plot_matrix_by_id",
        {
            "data_range": data_ranges[0],
            "plot_type_id": 226,
            "template": "contour",
            "graph_name": "R2_B04_Contour",
            "title": None,
        },
    )
    active_graph = await base.call(session, "origin_get_graph_info", {})
    graph_name = base.find_key(active_graph, "graph_name")
    if not graph_name:
        raise RuntimeError(f"Matrix plot returned no active graph: {plotted}; {active_graph}")
    optimum = await base.call(
        session,
        "origin_import_table",
        {
            "path": str(BENCH / "two_parameter_optimum.csv"),
            "book_name": "R2_B04_Optimum",
            "sheet_name": "Point",
        },
    )
    worksheet = base.find_key(optimum, "worksheet")
    if not isinstance(worksheet, dict):
        raise RuntimeError(f"Optimum import returned no worksheet: {optimum}")
    worksheet_ref = f"[{worksheet['book_name']}]{worksheet['sheet_name']}"
    overlay = await base.call(
        session,
        "origin_add_plot_to_graph",
        {
            "worksheet": worksheet_ref,
            "x_col": "x",
            "y_col": "y",
            "graph_name": graph_name,
            "layer_index": 0,
            "plot_type": "s",
        },
    )
    compact = await apply_compact_style(
        session, graph_name, figure_id, chart_type="contour"
    )
    contour_style = await base.call(
        session,
        "origin_set_plot_style",
        {
            "graph_name": graph_name,
            "layer_index": 0,
            "plot_index": 0,
            "colormap": "viridis",
            "contour_levels": [0, 4, 8, 12, 16, 20, 24, 28, 32, 36],
            "contour_minor_levels": 0,
            "color_scale_limits": [0, 36],
            "line_width": 0.28,
        },
    )
    optimum_style = await base.call(
        session,
        "origin_set_plot_style",
        {
            "graph_name": graph_name,
            "layer_index": 0,
            "plot_index": 1,
            "color": HIGHLIGHT,
            "symbol_kind": 2,
            "symbol_size": 3.3,
            "line_width": 0.35,
        },
    )
    axes = []
    for axis, title in (("x", "Decision variable x"), ("y", "Decision variable y")):
        axes.append(
            await base.call(
                session,
                "origin_set_axis",
                {
                    "graph_name": graph_name,
                    "layer_index": 0,
                    "axis": axis,
                    "start": -3,
                    "end": 3,
                    "step": 1,
                    "title": title,
                },
            )
        )
    final_axes = await base.call(
        session,
        "origin_run_labtalk",
        {"script": base_labtalk(graph_name, keep_frame=True)},
    )
    cmap_parts = [
        f"layer.cmap.color{i + 1}={rgb_expr(color)};"
        for i, color in enumerate(CONTOUR_COLORS)
    ]
    colorbar_scripts = [
        (
            f'win -a "{graph_name}"; layer -s 1; '
            + " ".join(cmap_parts)
            + f" layer.cmap.colorLow={rgb_expr(CONTOUR_COLORS[0])};"
            + f" layer.cmap.colorHigh={rgb_expr(CONTOUR_COLORS[-1])};"
            + " layer.cmap.colorAbove=layer.cmap.colorHigh;"
            + " layer.cmap.colorBelow=layer.cmap.colorLow;"
            + " layer.cmap.labelAbove=0; layer.cmap.lineAbove=0;"
            + " layer.cmap.updateScale(); doc -uw;"
        ),
        (
            f'win -a "{graph_name}"; '
            "Spectrum1.labels.autodisp=0;"
            "Spectrum1.labels.font=font(Arial); Spectrum1.labels.fsize=5.8;"
            "Spectrum1.labels.bold=0; Spectrum1.labels.italic=0;"
            "Spectrum1.labels.formrange=0; Spectrum1.labels.numdisp=1;"
            "Spectrum1.labels.decplaces=0; Spectrum1.labels.rotate=0;"
            "Spectrum1.barthick=125; Spectrum1.lgap=30;"
            f"Spectrum1.color={rgb_expr([70, 75, 80])};"
            "doc -uw;"
        ),
        (
            f'win -a "{graph_name}"; '
            'Spectrum1.title$="Objective value"; Spectrum1.title=1; '
            "Spectrum1.draw(global); doc -uw; sec -p 0.1;"
        ),
    ]
    colorbar = [
        await base.call(session, "origin_run_labtalk", {"script": script})
        for script in colorbar_scripts
    ]
    optimum_label = await base.call(
        session,
        "origin_run_labtalk",
        {
            "script": label_script(
                graph_name,
                "R2Optimum",
                "Optimum",
                1.03,
                -0.43,
                [155, 88, 27],
                bold=False,
                font_size=4.2,
            )
        },
    )
    colorbar_title = await base.call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; layer -s 1; '
                "label -a 4.45 0 -n R2ColorbarTitle Objective value; "
                "R2ColorbarTitle.rotate=90; "
                "R2ColorbarTitle.font=font(Arial); R2ColorbarTitle.fsize=4.8; "
                f"R2ColorbarTitle.color={rgb_expr([70, 75, 80])}; "
                "R2ColorbarTitle.background=0; R2ColorbarTitle.clip=0; "
                "doc -uw; sec -p 0.1;"
            )
        },
    )
    info = await base.call(session, "origin_get_graph_info", {"graph_name": graph_name})
    exports = await export_graph_set(session, graph_name, figure_id)
    return {
        "figure_id": figure_id,
        "graph_name": graph_name,
        "matrix": created,
        "matrix_plot": plotted,
        "active_graph_after_matrix_plot": active_graph,
        "optimum_import": optimum,
        "overlay": overlay,
        "compact_style": compact,
        "contour_style": contour_style,
        "optimum_style": optimum_style,
        "axes": axes,
        "final_axes_and_label_cleanup": final_axes,
        "custom_colormap_and_colorbar": colorbar,
        "colorbar_title": colorbar_title,
        "optimum_label": optimum_label,
        "graph_info": info,
        "exports": exports,
    }


async def render(session: ClientSession) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    specs = build_specs()
    report: dict[str, Any] = {
        "style": "Signature Scientific Style v1",
        "ping": await base.call(session, "origin_ping", {"show": True}),
        "figures": [],
    }
    for spec in specs:
        planned = await base.call(session, "origin_plan_figure_spec", {"spec": spec})
        plan_data = planned.get("data", planned)
        if not plan_data.get("executor_executable", False):
            raise RuntimeError(
                f"FigureSpec not executable for {spec['figure']['id']}: "
                f"{json.dumps(planned, ensure_ascii=False)}"
            )
        executed = await base.call(
            session, "origin_execute_figure_spec", {"spec": spec, "dry_run": False}
        )
        execution_data = executed.get("data", executed)
        graph_name = execution_data.get("graph", {}).get("graph_name")
        if not graph_name:
            raise RuntimeError(f"No actual Origin graph name returned: {executed}")
        figure_id = spec["figure"]["id"]
        compact = await apply_compact_style(session, graph_name, figure_id)
        analytical = []
        if figure_id == "R2_B02_multi_line_comparison":
            analytical = await add_multi_labels(session, graph_name)
        elif figure_id == "R2_B03_sensitivity_analytical":
            analytical = await add_sensitivity_analysis(session, graph_name)
        info = await base.call(session, "origin_get_graph_info", {"graph_name": graph_name})
        exports = await export_graph_set(session, graph_name, figure_id)
        report["figures"].append(
            {
                "figure_id": figure_id,
                "graph_name": graph_name,
                "plan": planned,
                "execution": executed,
                "compact_style": compact,
                "analytical_annotations": analytical,
                "graph_info": info,
                "exports": exports,
            }
        )
    report["figures"].append(await render_contour(session))
    report["project_save"] = await base.bridge_task(
        session,
        "save_project",
        {"path": str(OUTPUT / "ORIGIN_SIGNATURE_STYLE_V1_ROUND2.opju")},
    )
    return report


async def save_templates(session: ClientSession) -> dict[str, Any]:
    execution_log = json.loads(
        (LOG_DIR / "round2_mcp_execution.json").read_text(encoding="utf-8")
    )
    graph_names = {
        item["figure_id"]: item["graph_name"] for item in execution_log["figures"]
    }
    library_before = await base.call(session, "origin_list_user_templates", {})
    existing_templates = library_before.get("data", {}).get("templates", [])
    existing_names = {
        item.get("name") for item in existing_templates if isinstance(item, dict)
    }
    templates = [
        ("SCP_SINGLE_LINE_MAIN_v02", "R2_B01_single_line_main", ["line"], ["x", "y"], 2),
        (
            "SCP_MULTI_LINE_COMPARISON_v02",
            "R2_B02_multi_line_comparison",
            ["line"],
            ["x", "baseline", "alternatives", "primary"],
            5,
        ),
        (
            "SCP_SENSITIVITY_ANALYTICAL_v02",
            "R2_B03_sensitivity_analytical",
            ["line"],
            ["perturbation", "responses", "zero-reference"],
            5,
        ),
        (
            "SCP_CONTOUR_MAIN_v02",
            "R2_B04_contour_main",
            ["contour", "scatter"],
            ["x", "y", "z", "optimum", "colorbar-label"],
            4,
        ),
    ]
    saved = []
    for name, figure_id, plot_types, roles, n_columns in templates:
        if name in existing_names:
            saved.append(
                {
                    "ok": True,
                    "message": "Verified existing Origin graph template; overwrite skipped.",
                    "data": {"name": name, "verified_existing": True},
                }
            )
            continue
        saved.append(
            await base.call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": (
                        "Signature Scientific Style v1 round-two Origin template; "
                        "smaller typography, lighter frame, stronger hierarchy."
                    ),
                    "tags": [
                        "signature-scientific-style-v1",
                        "round2",
                        "publication-grade",
                    ],
                    "plot_types": plot_types,
                    "roles": roles,
                    "n_columns": n_columns,
                    "graph_name": graph_names[figure_id],
                    "overwrite": False,
                },
            )
        )
    return {
        "templates": saved,
        "library_before": library_before,
        "library_after": await base.call(session, "origin_list_user_templates", {}),
    }


async def run(mode: str) -> None:
    env = dict(os.environ)
    env["ORIGIN_MCP_TOOL_PROFILE"] = "standard"
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
                target = LOG_DIR / "round2_mcp_execution.json"
            elif mode == "save-templates":
                result = await save_templates(session)
                target = LOG_DIR / "round2_template_save.json"
            else:
                commands = [
                    'win -a "Graph1";',
                    "layer -s 1;",
                    "page.color=color(white);",
                    "layer.color=color(white);",
                    "layer.border=0;",
                    "layer.x.grid.show=0;",
                    "layer.y.grid.show=0;",
                    "layer.x.showGrids=0;",
                    "layer.y.showGrids=0;",
                    "axis -ps X A 1;",
                    "axis -ps Y A 1;",
                    "layer.x.opposite=0;",
                    "layer.x.showopposite=0;",
                    "layer.x.thickness=0.45;",
                    "layer.x.tickthickness=0.45;",
                    "layer.x.mtickthickness=0.35;",
                    "layer.x.label.fsize=5.8;",
                    "xb.fsize=6.5;",
                    "set Book2_B -q 0;",
                    "doc -e D { set %C -q 0; };",
                    'win -a "Graph4";',
                    'Spectrum1.title$="Objective value";',
                    "Spectrum1.title=1;",
                    "Spectrum1.draw(global);",
                    "Spectrum1.barthick=125;",
                    "Spectrum1.lineWidth=0.40;",
                    'Spectrum1.color=color("#464B50");',
                    "R2Optimum.anchor=27;",
                    'R2Optimum.color=color("#9B581B");',
                    "R2Optimum.fsize=4.3;",
                ]
                result = []
                for script in commands:
                    result.append(
                        {
                            "script": script,
                            "result": await base.call(
                                session, "origin_run_labtalk", {"script": script}
                            ),
                        }
                    )
                target = LOG_DIR / "round2_labtalk_audit.json"
            target.write_text(
                json.dumps(base.jsonable(result), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(json.dumps({"mode": mode, "result_file": str(target)}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("render", "save-templates", "audit-labtalk"))
    args = parser.parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
