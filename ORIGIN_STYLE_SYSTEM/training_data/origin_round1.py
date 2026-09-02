"""Render and template the first Origin style round through an MCP stdio client."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SYSTEM_ROOT = Path(__file__).resolve().parents[1]
BENCH = SYSTEM_ROOT / "benchmarks"
OUTPUT = SYSTEM_ROOT / "outputs"
LOG_DIR = SYSTEM_ROOT / "training_data"
PYTHON_EXE = Path(
    r"C:\Users\YiPian\Documents\Codex\2026-05-21\skills\.venvs\origin-mcp\Scripts\python.exe"
)

PRIMARY = [31, 78, 121]
SECONDARY = [91, 143, 168]
HIGHLIGHT = [201, 123, 42]
NEUTRAL = [122, 127, 135]
GREEN = [63, 125, 108]
PURPLE = [128, 100, 162]


def jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def decode_result(result: Any) -> dict[str, Any]:
    if getattr(result, "isError", False):
        texts = [getattr(item, "text", "") for item in result.content]
        raise RuntimeError("\n".join(texts) or "Origin MCP tool returned an error")
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)
        if text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    return {"content": jsonable(getattr(result, "content", []))}


async def call(session: ClientSession, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return decode_result(await session.call_tool(name, arguments=arguments))


def export_spec(stem: str) -> dict[str, Any]:
    return {
        "qa": {
            "require_axis_titles": True,
            "require_plots": True,
            "require_legend": False,
        },
    }


def common_spec(figure_id: str, source: Path, roles: dict[str, Any]) -> dict[str, Any]:
    return {
        "figure": {"id": figure_id, "title": figure_id},
        "runtime": {"show_origin": True, "new_project": False, "save_project": False},
        "data": [{"id": "data", "source": str(source), "object": "worksheet", "roles": roles}],
        "page": {"layout": "single"},
        "layers": [{"id": "main", "data_ref": "data"}],
        "plots": [],
        "annotations": [],
        "style": {
            "theme": "nature",
            "font_family": "Arial",
            "annotation_font_size": 9,
            "palette_role": "hero",
        },
        "export": export_spec(figure_id),
    }


def build_specs() -> list[dict[str, Any]]:
    single = common_spec(
        "B01_single_line_main",
        BENCH / "single_peak_time_curve.csv",
        {"x": "time_h", "y": "response_index"},
    )
    single["runtime"]["new_project"] = True
    single["layers"][0].update(
        {
            "x": {"title": "Time (h)", "limits": [0, 24], "step": 4},
            "y": {"title": "Response index", "limits": [0, 90], "step": 15},
        }
    )
    single["plots"] = [
        {
            "id": "response",
            "layer": "main",
            "type": "line",
            "map": {"x": "time_h", "y": "response_index"},
            "style": {"color": PRIMARY, "line_width": 2.2, "line_style": 0},
        },
        {
            "id": "peak_point",
            "layer": "main",
            "type": "scatter",
            "data_ref": "peak",
            "map": {"x": "time_h", "y": "response_index"},
            "style": {"color": HIGHLIGHT, "symbol_kind": 3, "symbol_size": 5.5},
        },
    ]
    single["data"].append(
        {
            "id": "peak",
            "source": str(BENCH / "single_peak_point.csv"),
            "object": "worksheet",
            "roles": {"x": "time_h", "y": "response_index"},
        }
    )

    multi = common_spec(
        "B02_multi_line_comparison",
        BENCH / "multi_solution_time_curves.csv",
        {"x": "time_h", "y": ["baseline", "conservative", "aggressive", "proposed"]},
    )
    multi["layers"][0].update(
        {
            "x": {"title": "Time (h)", "limits": [0, 24], "step": 4},
            "y": {"title": "Performance index", "limits": [20, 100], "step": 10},
        }
    )
    multi["plots"] = [
        {
            "id": "strategies",
            "layer": "main",
            "type": "line",
            "map": {"x": "time_h", "y": ["baseline", "conservative", "aggressive", "proposed"]},
            "group_style": {
                "series": [
                    {"color": NEUTRAL, "line_width": 1.25, "line_style": 1},
                    {"color": SECONDARY, "line_width": 1.45, "line_style": 2},
                    {"color": GREEN, "line_width": 1.45, "line_style": 3},
                    {"color": PRIMARY, "line_width": 2.2, "line_style": 0},
                ]
            },
        }
    ]
    multi["annotations"] = [{"type": "legend", "layer": "main", "location": "top-left", "frame": False}]

    sensitivity = common_spec(
        "B03_sensitivity_analytical",
        BENCH / "single_parameter_sensitivity.csv",
        {"x": "perturbation_pct", "y": ["demand", "capacity", "unit_cost", "efficiency"]},
    )
    sensitivity["layers"][0].update(
        {
            "x": {"title": "Parameter perturbation (%)", "limits": [-20, 20], "step": 5},
            "y": {"title": "Output change (%)", "limits": [-18, 24], "step": 6},
        }
    )
    sensitivity["plots"] = [
        {
            "id": "sensitivity_curves",
            "layer": "main",
            "type": "line",
            "map": {"x": "perturbation_pct", "y": ["demand", "capacity", "unit_cost", "efficiency"]},
            "group_style": {
                "series": [
                    {"color": SECONDARY, "line_width": 1.45, "line_style": 1},
                    {"color": GREEN, "line_width": 1.45, "line_style": 2},
                    {"color": PRIMARY, "line_width": 2.2, "line_style": 0},
                    {"color": PURPLE, "line_width": 1.45, "line_style": 3},
                ]
            },
        }
    ]
    sensitivity["annotations"] = [
        {"type": "reference_line", "layer": "main", "value": 0, "orientation": "vertical"},
        {"type": "reference_line", "layer": "main", "value": 0, "orientation": "horizontal"},
        {"type": "legend", "layer": "main", "location": "top-left", "frame": False},
    ]

    return [single, multi, sensitivity]


def find_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = find_key(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_key(child, key)
            if found is not None:
                return found
    return None


async def bridge_task(session: ClientSession, method: str, params: dict[str, Any]) -> dict[str, Any]:
    submitted = await call(
        session,
        "origin_bridge_submit_task",
        {"method": method, "params": params, "timeout": 10.0},
    )
    task_id = find_key(submitted, "task_id")
    if not task_id:
        raise RuntimeError(f"Bridge task submission returned no task_id: {submitted}")
    last: dict[str, Any] = submitted
    for _ in range(80):
        await asyncio.sleep(0.1)
        last = await call(
            session,
            "origin_bridge_task_status",
            {"task_id": task_id, "include_result": True, "include_logs": True, "log_limit": 10},
        )
        state = str(find_key(last, "status") or find_key(last, "state") or "").lower()
        if state in {"completed", "succeeded", "success", "failed", "cancelled", "canceled"}:
            if state in {"failed", "cancelled", "canceled"}:
                raise RuntimeError(f"Bridge task {method} ended as {state}: {last}")
            return last
    raise TimeoutError(f"Bridge task {method} did not complete: {last}")


async def export_graph_set(session: ClientSession, graph_name: str, stem: str) -> list[dict[str, Any]]:
    output_dir = str(OUTPUT).replace("\\", "/")
    exports = [
        await call(
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
            await call(
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


SERIES_STYLES: dict[str, list[dict[str, Any]]] = {
    "B01_single_line_main": [
        {"color": PRIMARY, "line_width": 1.6, "line_style": 0},
        {"color": HIGHLIGHT, "symbol_kind": 2, "symbol_size": 3.8, "line_width": 0.4},
    ],
    "B02_multi_line_comparison": [
        {"color": NEUTRAL, "line_width": 1.0, "line_style": 1},
        {"color": SECONDARY, "line_width": 1.2, "line_style": 2},
        {"color": GREEN, "line_width": 1.2, "line_style": 3},
        {"color": PRIMARY, "line_width": 1.6, "line_style": 0},
    ],
    "B03_sensitivity_analytical": [
        {"color": SECONDARY, "line_width": 1.2, "line_style": 1},
        {"color": GREEN, "line_width": 1.2, "line_style": 2},
        {"color": PRIMARY, "line_width": 1.6, "line_style": 0},
        {"color": PURPLE, "line_width": 1.2, "line_style": 3},
    ],
}


async def compact_style(
    session: ClientSession,
    graph_name: str,
    figure_id: str,
    *,
    chart_type: str = "line",
    show_legend: bool = False,
) -> dict[str, Any]:
    nature = await bridge_task(
        session,
        "apply_nature_style",
        {
            "graph_name": graph_name,
            "chart_type": chart_type,
            "page_width": 1800,
            "page_height": 1200,
            "font_family": "Arial",
            "axis_title_size": 8,
            "tick_label_size": 7,
            "legend_font_size": 7,
            "line_width": 1.2,
            "symbol_size": 5.0,
            "tick_length": 3,
            "show_legend": show_legend,
            "differentiate_series": False,
            "run_diagnostics": False,
        },
    )
    geometry = (
        {"layer_index": 0, "left": 19, "top": 7, "width": 52, "height": 65}
        if chart_type == "contour"
        else {"layer_index": 0, "left": 19, "top": 7, "width": 75, "height": 65}
    )
    arranged = await bridge_task(
        session,
        "arrange_layers",
        {"graph_name": graph_name, "rows": 1, "columns": 1, "layer_geometries": [geometry]},
    )
    grid = await call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; layer -s 1; '
                "layer.x.grid.show=0; layer.y.grid.show=0; "
                "layer.x.showAxes=1; layer.y.showAxes=1; "
                "layer.x.showLabels=1; layer.y.showLabels=1; "
                "layer.x.showlabel=1; layer.y.showlabel=1; "
                "layer.x2.showlabel=0; layer.y2.showlabel=0; "
                "layer.x2.showopposite=0; layer.y2.showopposite=0; "
                "layer.x2.ticks=0; layer.y2.ticks=0; "
                "layer.x2.label.color=0; layer.y2.label.color=0; "
                "layer.x2.label.pt=7; layer.y2.label.pt=7; "
                "doc -e D { set %C -q 0; }; "
                "doc -uw; sec -p 0.1;"
            )
        },
    )
    styled = []
    for plot_index, style in enumerate(SERIES_STYLES.get(figure_id, [])):
        styled.append(
            await call(
                session,
                "origin_set_plot_style",
                {"graph_name": graph_name, "layer_index": 0, "plot_index": plot_index, **style},
            )
        )
    legend = None
    if show_legend:
        legend = await bridge_task(
            session,
            "format_legend",
            {
                "graph_name": graph_name,
                "font_size": 7,
                "font_family": "Arial",
                "show_frame": False,
                "position": "top-left",
                "margin_percent": 3.0,
            },
        )
    return {
        "nature": nature,
        "arrange": arranged,
        "grid_and_opposite_axes": grid,
        "series": styled,
        "legend": legend,
    }


def load_objective_matrix() -> tuple[list[list[float]], list[float], list[float]]:
    with (BENCH / "two_parameter_objective.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    xs = sorted({float(row["x"]) for row in rows})
    ys = sorted({float(row["y"]) for row in rows})
    lookup = {(float(row["x"]), float(row["y"])): float(row["objective"]) for row in rows}
    matrix = [[lookup[(x, y)] for x in xs] for y in ys]
    return matrix, xs, ys


async def render_contour(session: ClientSession) -> dict[str, Any]:
    figure_id = "B04_contour_main"
    matrix, xs, ys = load_objective_matrix()
    created = await call(
        session,
        "origin_create_matrix",
        {
            "data": matrix,
            "book_name": "B04_Field",
            "sheet_name": "Objective",
            "xymap": [xs[0], xs[-1], ys[0], ys[-1]],
            "labels": ["Objective value"],
        },
    )
    data_ranges = find_key(created, "data_ranges")
    if not isinstance(data_ranges, list) or not data_ranges:
        raise RuntimeError(f"Matrix creation returned no data range: {created}")
    plotted = await bridge_task(
        session,
        "plot_matrix_by_id",
        {
            "data_range": data_ranges[0],
            "plot_type_id": 226,
            "template": "contour",
            "graph_name": "B04_Contour",
            "title": None,
        },
    )
    active_graph = await call(session, "origin_get_graph_info", {})
    graph_name = find_key(active_graph, "graph_name")
    if not graph_name:
        raise RuntimeError(f"Matrix plot returned no active graph: {plotted}; {active_graph}")
    optimum = await call(
        session,
        "origin_import_table",
        {
            "path": str(BENCH / "two_parameter_optimum.csv"),
            "book_name": "B04_Optimum",
            "sheet_name": "Point",
        },
    )
    worksheet = find_key(optimum, "worksheet")
    if not isinstance(worksheet, dict):
        raise RuntimeError(f"Optimum import returned no worksheet: {optimum}")
    worksheet_ref = f"[{worksheet['book_name']}]{worksheet['sheet_name']}"
    overlay = await call(
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
    compact = await compact_style(
        session, graph_name, figure_id, chart_type="contour", show_legend=False
    )
    contour_style = await call(
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
            "line_width": 0.45,
        },
    )
    optimum_style = await call(
        session,
        "origin_set_plot_style",
        {
            "graph_name": graph_name,
            "layer_index": 0,
            "plot_index": 1,
            "color": HIGHLIGHT,
            "symbol_kind": 2,
            "symbol_size": 3.8,
            "line_width": 0.4,
        },
    )
    axes = []
    for axis, start, end, title in (
        ("x", -3, 3, "Decision variable x"),
        ("y", -3, 3, "Decision variable y"),
    ):
        axes.append(
            await call(
                session,
                "origin_set_axis",
                {
                    "graph_name": graph_name,
                    "layer_index": 0,
                    "axis": axis,
                    "start": start,
                    "end": end,
                    "step": 1,
                    "title": title,
                },
            )
        )
    formatted = await call(
        session,
        "origin_format_graph",
        {"graph_name": graph_name, "show_legend": False, "rescale": False},
    )
    color_scale = await call(
        session,
        "origin_run_labtalk",
        {
            "script": (
                f'win -a "{graph_name}"; '
                "Spectrum1.labels.autodisp=0; "
                "Spectrum1.labels.font=font(Arial); Spectrum1.labels.fsize=7; "
                "Spectrum1.labels.bold=0; Spectrum1.labels.italic=0; "
                "Spectrum1.labels.formrange=0; Spectrum1.labels.numdisp=1; "
                "Spectrum1.labels.decplaces=0; Spectrum1.labels.rotate=0; "
                "Spectrum1.title=0; Spectrum1.barthick=240; Spectrum1.lgap=45; "
                "layer.cmap.colorAbove=layer.cmap.colorHigh; "
                "layer.cmap.colorBelow=layer.cmap.colorLow; "
                "layer.cmap.labelAbove=0; layer.cmap.lineAbove=0; "
                "layer.cmap.updateScale(); "
                "doc -uw; sec -p 0.1;"
            )
        },
    )
    info = await call(session, "origin_get_graph_info", {"graph_name": graph_name})
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
        "format": formatted,
        "color_scale_format": color_scale,
        "graph_info": info,
        "exports": exports,
    }


async def render(session: ClientSession) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    specs = build_specs()
    report: dict[str, Any] = {"ping": await call(session, "origin_ping", {"show": True}), "figures": []}
    for spec in specs:
        planned = await call(session, "origin_plan_figure_spec", {"spec": spec})
        plan_data = planned.get("data", planned)
        if not plan_data.get("executor_executable", False):
            raise RuntimeError(f"FigureSpec not executable for {spec['figure']['id']}: {json.dumps(planned, ensure_ascii=False)}")
        executed = await call(session, "origin_execute_figure_spec", {"spec": spec, "dry_run": False})
        execution_data = executed.get("data", executed)
        graph_name = execution_data.get("graph", {}).get("graph_name")
        if not graph_name:
            raise RuntimeError(
                f"No actual Origin graph name returned for {spec['figure']['id']}: "
                f"{json.dumps(executed, ensure_ascii=False)}"
            )
        figure_id = spec["figure"]["id"]
        show_legend = figure_id in {"B02_multi_line_comparison", "B03_sensitivity_analytical"}
        compact = await compact_style(
            session, graph_name, figure_id, chart_type="line", show_legend=show_legend
        )
        formatted = await call(
            session,
            "origin_format_graph",
            {"graph_name": graph_name, "show_legend": show_legend, "rescale": False},
        )
        info = await call(session, "origin_get_graph_info", {"graph_name": graph_name})
        exports = await export_graph_set(session, graph_name, figure_id)
        report["figures"].append(
            {
                "figure_id": figure_id,
                "graph_name": graph_name,
                "plan": planned,
                "execution": executed,
                "compact_style": compact,
                "format": formatted,
                "graph_info": info,
                "exports": exports,
            }
        )
    report["figures"].append(await render_contour(session))
    report["project_save"] = await bridge_task(
        session,
        "save_project",
        {"path": str(OUTPUT / "ORIGIN_STYLE_ROUND1.opju")},
    )
    return report


async def save_templates(session: ClientSession) -> dict[str, Any]:
    execution_log = json.loads((LOG_DIR / "round1_mcp_execution.json").read_text(encoding="utf-8"))
    graph_names = {item["figure_id"]: item["graph_name"] for item in execution_log["figures"]}
    library_before = await call(session, "origin_list_user_templates", {})
    existing_templates = library_before.get("data", {}).get("templates", [])
    existing_names = {
        item.get("name") for item in existing_templates if isinstance(item, dict)
    }
    templates = [
        ("SCP_SINGLE_LINE_MAIN_v01", "B01_single_line_main", ["line"], ["x", "y"], 2),
        ("SCP_MULTI_LINE_COMPARISON_v01", "B02_multi_line_comparison", ["line"], ["x", "baseline", "alternatives", "primary"], 5),
        ("SCP_SENSITIVITY_ANALYTICAL_v01", "B03_sensitivity_analytical", ["line"], ["perturbation", "responses"], 5),
        ("SCP_CONTOUR_MAIN_v01", "B04_contour_main", ["contour", "scatter"], ["x", "y", "z", "optimum"], 4),
    ]
    saved = []
    for name, graph_name, plot_types, roles, n_columns in templates:
        if name in existing_names:
            saved.append(
                {
                    "ok": True,
                    "message": "Verified existing Origin graph template; overwrite skipped.",
                    "data": {
                        "name": name,
                        "verified_existing": True,
                        "overwrite_skipped": True,
                    },
                }
            )
            continue
        saved.append(
            await call(
                session,
                "origin_save_graph_template",
                {
                    "name": name,
                    "description": "Scientific Competition Premium round-one candidate; human aesthetic approval pending.",
                    "tags": ["scientific-competition-premium", "round1", "candidate"],
                    "plot_types": plot_types,
                    "roles": roles,
                    "n_columns": n_columns,
                    "graph_name": graph_names[graph_name],
                    "overwrite": False,
                },
            )
        )
    return {
        "templates": saved,
        "library_before": library_before,
        "library_after": await call(session, "origin_list_user_templates", {}),
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
            tools = await session.list_tools()
            inventory = [
                {"name": tool.name, "description": tool.description}
                for tool in tools.tools
            ]
            (LOG_DIR / "origin_mcp_tool_inventory.json").write_text(
                json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if mode == "render":
                result = await render(session)
                target = LOG_DIR / "round1_mcp_execution.json"
            else:
                result = await save_templates(session)
                target = LOG_DIR / "round1_template_save.json"
            target.write_text(json.dumps(jsonable(result), ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"mode": mode, "result_file": str(target)}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("render", "save-templates"))
    args = parser.parse_args()
    asyncio.run(run(args.mode))


if __name__ == "__main__":
    main()
