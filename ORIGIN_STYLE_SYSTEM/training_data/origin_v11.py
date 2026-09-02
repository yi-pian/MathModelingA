"""Origin MCP micro-refinement for frozen Signature Scientific Style v1.1."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import origin_round2 as r2


SYSTEM_ROOT = r2.SYSTEM_ROOT
BENCH = r2.BENCH
OUTPUT = r2.base.OUTPUT / "v1.1"
LOG_DIR = r2.LOG_DIR
PYTHON_EXE = r2.PYTHON_EXE

PRIMARY = r2.PRIMARY
HIGHLIGHT = r2.HIGHLIGHT
NEUTRAL = r2.NEUTRAL
SECONDARY = r2.SECONDARY
GREEN = r2.GREEN
PURPLE = r2.PURPLE


def midpoint(a: list[int], b: list[int]) -> list[int]:
    return [round((x + y) / 2) for x, y in zip(a, b)]


CONTOUR_COLORS_19: list[list[int]] = []
for left, right in zip(r2.CONTOUR_COLORS[:-1], r2.CONTOUR_COLORS[1:]):
    CONTOUR_COLORS_19.extend([left, midpoint(left, right)])
CONTOUR_COLORS_19.append(r2.CONTOUR_COLORS[-1])

CONTOUR_LEVELS = list(range(0, 38, 2))
CONTOUR_LINE_INDICES = {1, 4, 7, 10, 13, 16, 19}


def build_specs() -> list[dict[str, Any]]:
    specs = deepcopy(r2.build_specs())
    ids = [
        "V11_B01_single_line_main",
        "V11_B02_multi_line_comparison",
        "V11_B03_sensitivity_analytical",
    ]
    for spec, figure_id in zip(specs, ids):
        spec["figure"]["id"] = figure_id
        spec["figure"]["title"] = figure_id
        spec["style"]["palette_role"] = "signature-scientific-v1.1-frozen"
        spec["annotations"] = []
    # Five percent more right-side visual room than v1 for staggered direct labels.
    specs[1]["layers"][0]["x"]["limits"] = [0, 29]
    # Small x label margin and 3 units of y headroom above the last labeled tick.
    specs[2]["layers"][0]["x"]["limits"] = [-20, 24.5]
    specs[2]["layers"][0]["y"]["limits"] = [-18, 27]
    return specs


SERIES_STYLES: dict[str, list[dict[str, Any]]] = {
    "V11_B01_single_line_main": [
        {"color": PRIMARY, "line_width": 1.36, "line_style": 0},
        {
            "color": HIGHLIGHT,
            "symbol_kind": 2,
            "symbol_size": 3.05,
            "line_width": 0.32,
        },
    ],
    "V11_B02_multi_line_comparison": [
        {"color": NEUTRAL, "line_width": 0.75, "line_style": 1},
        {"color": SECONDARY, "line_width": 0.85, "line_style": 2},
        {"color": GREEN, "line_width": 0.90, "line_style": 3},
        {"color": PRIMARY, "line_width": 1.50, "line_style": 0},
    ],
    "V11_B03_sensitivity_analytical": [
        {"color": SECONDARY, "line_width": 0.90, "line_style": 1},
        {"color": GREEN, "line_width": 0.90, "line_style": 2},
        {"color": PRIMARY, "line_width": 1.50, "line_style": 0},
        {"color": PURPLE, "line_width": 0.90, "line_style": 3},
    ],
}


async def apply_compact_style(
    session: ClientSession,
    graph_name: str,
    figure_id: str,
    *,
    chart_type: str = "line",
) -> dict[str, Any]:
    nature = await r2.base.bridge_task(
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
    arranged = await r2.base.bridge_task(
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
            await r2.base.call(
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
    formatted = await r2.base.call(
        session,
        "origin_format_graph",
        {"graph_name": graph_name, "show_legend": False, "rescale": False},
    )
    base_style = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": r2.base_labtalk(
                graph_name, keep_frame=chart_type == "contour"
            )
        },
    )
    contour_ticks = None
    if chart_type == "contour":
        contour_ticks = await r2.base.call(
            session,
            "origin_run_labtalk",
            {
                "script": (
                    f'win -a "{graph_name}"; layer -s 1; '
                    "layer.x.ticklength=1.2; layer.y.ticklength=1.2; "
                    "layer.x.mticklength=0.7; layer.y.mticklength=0.7; "
                    "layer.x.tickthickness=0.28; layer.y.tickthickness=0.28; "
                    "layer.x.mtickthickness=0.22; layer.y.mtickthickness=0.22; "
                    "layer.x2.tickthickness=0.28; layer.y2.tickthickness=0.28; "
                    "doc -uw; sec -p 0.1;"
                )
            },
        )
    return {
        "nature": nature,
        "arrange": arranged,
        "series": styled,
        "format": formatted,
        "base_style": base_style,
        "contour_tick_micro_refinement": contour_ticks,
    }


def direct_label_script(
    graph_name: str,
    name: str,
    text: str,
    x: float,
    y: float,
    color: list[int],
    *,
    font_size: float = 4.8,
    rotate: int = 0,
) -> str:
    # LabTalk parses a negative numeric token after `label -a` as a command
    # switch.  Pass coordinates through variables so labels can safely occupy
    # the negative half of an analytical plot.
    return (
        f'win -a "{graph_name}"; layer -s 1; '
        f"double v11LabelX={x}; double v11LabelY={y}; "
        f"label -a v11LabelX v11LabelY -n {name} {text}; "
        f"{name}.font=font(Arial); {name}.fsize={font_size}; "
        f"{name}.color={r2.rgb_expr(color)}; {name}.rotate={rotate}; "
        f"{name}.background=0; {name}.clip=0; doc -uw; sec -p 0.1;"
    )


async def add_multi_labels(
    session: ClientSession, graph_name: str
) -> list[dict[str, Any]]:
    labels = [
        ("V11Proposed", "Proposed", 26.2, 94.5, PRIMARY),
        ("V11Conservative", "Conservative", 25.2, 82.6, [79, 128, 148]),
        ("V11Aggressive", "Aggressive", 18.8, 84.5, [63, 111, 96]),
        ("V11Baseline", "Baseline", 26.4, 70.6, [108, 112, 118]),
    ]
    return [
        await r2.base.call(
            session,
            "origin_run_labtalk",
            {
                "script": direct_label_script(
                    graph_name, name, text, x, y, color
                )
            },
        )
        for name, text, x, y, color in labels
    ]


async def add_sensitivity_analysis(
    session: ClientSession, graph_name: str
) -> list[dict[str, Any]]:
    zero = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; layer -s 1; '
                "draw -n V11ZeroLine -l -h 0; V11ZeroLine.attach=2; "
                "V11ZeroLine.color=color(198,203,209); "
                "V11ZeroLine.lineWidth=0.45; V11ZeroLine.lineType=1; "
                "V11ZeroLine.back=1; doc -uw; sec -p 0.1;"
            )
        },
    )
    labels = [
        ("V11UnitCost", "Unit cost", 18.6, 25.0, PRIMARY),
        ("V11Demand", "Demand", 21.9, 19.0, [79, 128, 148]),
        ("V11Capacity", "Capacity", 21.9, -5.3, [63, 111, 96]),
        ("V11Efficiency", "Efficiency", 18.5, -9.2, [112, 93, 132]),
    ]
    rendered = [zero]
    for name, text, x, y, color in labels:
        rendered.append(
            await r2.base.call(
                session,
                "origin_run_labtalk",
                {
                    "script": direct_label_script(
                        graph_name, name, text, x, y, color, font_size=4.7
                    )
                },
            )
        )
    return rendered


async def export_graph_set(
    session: ClientSession, graph_name: str, stem: str
) -> list[dict[str, Any]]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_dir = str(OUTPUT).replace("\\", "/")
    exports = [
        await r2.base.call(
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
            await r2.base.call(
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


async def render_contour(session: ClientSession) -> dict[str, Any]:
    figure_id = "V11_B04_contour_main"
    matrix, xs, ys = r2.load_objective_matrix()
    created = await r2.base.call(
        session,
        "origin_create_matrix",
        {
            "data": matrix,
            "book_name": "V11_B04_Field",
            "sheet_name": "Objective",
            "xymap": [xs[0], xs[-1], ys[0], ys[-1]],
            "labels": ["Objective value"],
        },
    )
    data_ranges = r2.base.find_key(created, "data_ranges")
    if not isinstance(data_ranges, list) or not data_ranges:
        raise RuntimeError(f"Matrix creation returned no data range: {created}")
    plotted = await r2.base.bridge_task(
        session,
        "plot_matrix_by_id",
        {
            "data_range": data_ranges[0],
            "plot_type_id": 226,
            "template": "contour",
            "graph_name": "V11_B04_Contour",
            "title": None,
        },
    )
    active_graph = await r2.base.call(session, "origin_get_graph_info", {})
    graph_name = r2.base.find_key(active_graph, "graph_name")
    if not graph_name:
        raise RuntimeError(f"Matrix plot returned no active graph: {plotted}")
    optimum = await r2.base.call(
        session,
        "origin_import_table",
        {
            "path": str(BENCH / "two_parameter_optimum.csv"),
            "book_name": "V11_B04_Optimum",
            "sheet_name": "Point",
        },
    )
    worksheet = r2.base.find_key(optimum, "worksheet")
    if not isinstance(worksheet, dict):
        raise RuntimeError(f"Optimum import returned no worksheet: {optimum}")
    overlay = await r2.base.call(
        session,
        "origin_add_plot_to_graph",
        {
            "worksheet": f"[{worksheet['book_name']}]{worksheet['sheet_name']}",
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
    contour_style = await r2.base.call(
        session,
        "origin_set_plot_style",
        {
            "graph_name": graph_name,
            "layer_index": 0,
            "plot_index": 0,
            "colormap": "viridis",
            "contour_levels": CONTOUR_LEVELS,
            "contour_minor_levels": 0,
            "color_scale_limits": [0, 36],
            "line_width": 0.22,
        },
    )
    optimum_style = await r2.base.call(
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
            await r2.base.call(
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
    palette_commands = [
        f"layer.cmap.color{i}={r2.rgb_expr(color)};"
        for i, color in enumerate(CONTOUR_COLORS_19, start=1)
    ]
    line_commands = []
    for i in range(1, 20):
        show = 1 if i in CONTOUR_LINE_INDICES else 0
        width = 0.22 if show else 0
        line_commands.extend(
            [
                f"layer.cmap.line{i}={show};",
                f"layer.cmap.lineWidth{i}={width};",
                f"layer.cmap.label{i}=0;",
            ]
        )
    cmap = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; layer -s 1; '
                + " ".join(palette_commands)
                + " "
                + " ".join(line_commands)
                + f" layer.cmap.colorLow={r2.rgb_expr(CONTOUR_COLORS_19[0])};"
                + f" layer.cmap.colorHigh={r2.rgb_expr(CONTOUR_COLORS_19[-1])};"
                + " layer.cmap.colorAbove=layer.cmap.colorHigh;"
                + " layer.cmap.colorBelow=layer.cmap.colorLow;"
                + " layer.cmap.labelAbove=0; layer.cmap.lineAbove=0;"
                + " layer.cmap.updateScale(); doc -uw; sec -p 0.1;"
            )
        },
    )
    colorbar = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; '
                "Spectrum1.labels.autodisp=0;"
                "Spectrum1.labels.font=font(Arial); Spectrum1.labels.fsize=5.1;"
                "Spectrum1.labels.bold=0; Spectrum1.labels.italic=0;"
                "Spectrum1.labels.color=color(94,100,106);"
                "Spectrum1.labels.formrange=0; Spectrum1.labels.numdisp=1;"
                "Spectrum1.labels.decplaces=0; Spectrum1.labels.rotate=0;"
                "Spectrum1.levels.major=3; Spectrum1.levels.from=0;"
                "Spectrum1.levels.to=36; Spectrum1.levels.type=1;"
                "Spectrum1.levels.inc=1; Spectrum1.levels.inc$=6;"
                "Spectrum1.levels.minorticks=0;"
                "Spectrum1.title=0; Spectrum1.barthick=102; Spectrum1.lgap=24;"
                "Spectrum1.lineWidth=0.28; Spectrum1.color=color(118,124,130);"
                "Spectrum1.draw(global); doc -uw; sec -p 0.1;"
            )
        },
    )
    colorbar_title = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": direct_label_script(
                graph_name,
                "V11ColorbarTitle",
                "Objective value",
                4.45,
                0,
                [82, 88, 94],
                font_size=4.3,
                rotate=90,
            )
        },
    )
    optimum_label = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": direct_label_script(
                graph_name,
                "V11Optimum",
                "Optimum",
                1.30,
                -0.42,
                [155, 88, 27],
                font_size=4.2,
            )
        },
    )
    final_ticks = await r2.base.call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; layer -s 1; '
                "layer.x.ticklength=1.2; layer.y.ticklength=1.2; "
                "layer.x.mticklength=0.7; layer.y.mticklength=0.7; "
                "layer.x.tickthickness=0.28; layer.y.tickthickness=0.28; "
                "layer.x.mtickthickness=0.22; layer.y.mtickthickness=0.22; "
                "doc -e D { set %C -q 0; }; doc -uw; sec -p 0.1;"
            )
        },
    )
    info = await r2.base.call(
        session, "origin_get_graph_info", {"graph_name": graph_name}
    )
    exports = await export_graph_set(session, graph_name, figure_id)
    return {
        "figure_id": figure_id,
        "graph_name": graph_name,
        "matrix": created,
        "matrix_plot": plotted,
        "optimum_import": optimum,
        "overlay": overlay,
        "compact_style": compact,
        "contour_style": contour_style,
        "optimum_style": optimum_style,
        "axes": axes,
        "continuous_palette_and_sparse_lines": cmap,
        "colorbar_micro_refinement": colorbar,
        "colorbar_title": colorbar_title,
        "optimum_label": optimum_label,
        "final_tick_refinement": final_ticks,
        "graph_info": info,
        "exports": exports,
    }


async def render(session: ClientSession) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "style": "Signature Scientific Style v1.1",
        "status_target": "FROZEN",
        "ping": await r2.base.call(session, "origin_ping", {"show": True}),
        "figures": [],
    }
    for spec in build_specs():
        planned = await r2.base.call(
            session, "origin_plan_figure_spec", {"spec": spec}
        )
        plan_data = planned.get("data", planned)
        if not plan_data.get("executor_executable", False):
            raise RuntimeError(f"FigureSpec not executable: {planned}")
        executed = await r2.base.call(
            session, "origin_execute_figure_spec", {"spec": spec, "dry_run": False}
        )
        graph_name = executed.get("data", executed).get("graph", {}).get("graph_name")
        if not graph_name:
            raise RuntimeError(f"No actual Origin graph returned: {executed}")
        figure_id = spec["figure"]["id"]
        compact = await apply_compact_style(session, graph_name, figure_id)
        annotations = []
        if figure_id == "V11_B02_multi_line_comparison":
            annotations = await add_multi_labels(session, graph_name)
        elif figure_id == "V11_B03_sensitivity_analytical":
            annotations = await add_sensitivity_analysis(session, graph_name)
        info = await r2.base.call(
            session, "origin_get_graph_info", {"graph_name": graph_name}
        )
        exports = await export_graph_set(session, graph_name, figure_id)
        report["figures"].append(
            {
                "figure_id": figure_id,
                "graph_name": graph_name,
                "plan": planned,
                "execution": executed,
                "compact_style": compact,
                "micro_annotations": annotations,
                "graph_info": info,
                "exports": exports,
            }
        )
    report["figures"].append(await render_contour(session))
    report["project_save"] = await r2.base.bridge_task(
        session,
        "save_project",
        {
            "path": str(
                OUTPUT / "ORIGIN_SIGNATURE_SCIENTIFIC_STYLE_V1_1_FROZEN.opju"
            )
        },
    )
    return report


async def save_templates(session: ClientSession) -> dict[str, Any]:
    execution_log = json.loads(
        (LOG_DIR / "v11_mcp_execution.json").read_text(encoding="utf-8")
    )
    graph_names = {
        item["figure_id"]: item["graph_name"] for item in execution_log["figures"]
    }
    library_before = await r2.base.call(session, "origin_list_user_templates", {})
    existing = library_before.get("data", {}).get("templates", [])
    existing_names = {item.get("name") for item in existing if isinstance(item, dict)}
    templates = [
        (
            "SCP_SINGLE_LINE_MAIN_v11_FROZEN",
            "V11_B01_single_line_main",
            ["line"],
            ["x", "y", "optimum"],
            2,
        ),
        (
            "SCP_MULTI_LINE_COMPARISON_v11_FROZEN",
            "V11_B02_multi_line_comparison",
            ["line"],
            ["x", "baseline", "alternatives", "primary", "direct-labels"],
            5,
        ),
        (
            "SCP_SENSITIVITY_ANALYTICAL_v11_FROZEN",
            "V11_B03_sensitivity_analytical",
            ["line"],
            ["perturbation", "responses", "zero-reference", "direct-labels"],
            5,
        ),
        (
            "SCP_CONTOUR_MAIN_v11_FROZEN",
            "V11_B04_contour_main",
            ["contour", "scatter"],
            ["x", "y", "z", "optimum", "labeled-colorbar"],
            4,
        ),
    ]
    saved = []
    for name, figure_id, plot_types, roles, n_columns in templates:
        if name in existing_names:
            saved.append(
                {
                    "ok": True,
                    "message": "Verified frozen template; overwrite skipped.",
                    "data": {"name": name, "verified_existing": True},
                }
            )
            continue
        saved.append(
            await r2.base.call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": (
                        "SIGNATURE SCIENTIFIC STYLE V1.1 — FROZEN. "
                        "Do not aesthetically iterate unless real competition data "
                        "exposes a new problem."
                    ),
                    "tags": [
                        "signature-scientific-style-v1.1",
                        "frozen",
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
        "status": "SIGNATURE SCIENTIFIC STYLE V1.1 — FROZEN",
        "templates": saved,
        "library_before": library_before,
        "library_after": await r2.base.call(session, "origin_list_user_templates", {}),
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
                target = LOG_DIR / "v11_mcp_execution.json"
            else:
                result = await save_templates(session)
                target = LOG_DIR / "v11_template_save.json"
            target.write_text(
                json.dumps(r2.base.jsonable(result), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(json.dumps({"mode": mode, "result_file": str(target)}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("render", "save-templates"))
    args = parser.parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
