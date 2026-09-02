"""Compact publication-style Matplotlib plots with explicit labels and units."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def use_paper_style():
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans", "Arial"], "axes.unicode_minus": False, "font.size": 9, "axes.labelsize": 10, "axes.titlesize": 11, "axes.linewidth": 0.8, "lines.linewidth": 1.6, "legend.frameon": False, "savefig.bbox": "tight"})


def save_figure(figure, output, *, formats=("png", "pdf", "svg"), dpi=300):
    base = Path(output)
    base.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for extension in formats:
        path = base.with_suffix(f".{extension}")
        figure.savefig(path, dpi=dpi if extension == "png" else None, bbox_inches="tight")
        written.append(path)
    return written


def _finish(figure, axis, *, title=None, output=None):
    if title:
        axis.set_title(title)
    axis.grid(True, color="#D9D9D9", linewidth=0.5, alpha=0.8)
    figure.tight_layout()
    if output is not None:
        save_figure(figure, output)
    return figure, axis


def plot_time_series(time, values, *, xlabel, ylabel, label=None, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.2, 3.3))
    axis.plot(time, values, color=COLORS[0], label=label)
    axis.set(xlabel=xlabel, ylabel=ylabel)
    if label: axis.legend()
    return _finish(figure, axis, title=title, output=output)


def plot_multi_series(x, series, *, xlabel, ylabel, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.2, 3.3))
    items = series.items() if hasattr(series, "items") else series
    for index, (label, values) in enumerate(items): axis.plot(x, values, label=label, color=COLORS[index % len(COLORS)])
    axis.set(xlabel=xlabel, ylabel=ylabel); axis.legend()
    return _finish(figure, axis, title=title, output=output)


def plot_scatter_fit(x, observed, predicted, *, xlabel, ylabel, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(4.5, 3.5))
    order = np.argsort(x); axis.scatter(x, observed, s=20, facecolor="white", edgecolor=COLORS[0], label="Observed"); axis.plot(np.asarray(x)[order], np.asarray(predicted)[order], color=COLORS[1], label="Fit")
    axis.set(xlabel=xlabel, ylabel=ylabel); axis.legend()
    return _finish(figure, axis, title=title, output=output)


def plot_trajectory_2d(x, y, *, xlabel, ylabel, title=None, output=None):
    x_values, y_values = np.asarray(x, float), np.asarray(y, float)
    if x_values.ndim != 1 or y_values.shape != x_values.shape or x_values.size == 0:
        raise ValueError("x and y must be matching non-empty one-dimensional sequences")
    use_paper_style(); figure, axis = plt.subplots(figsize=(4.4, 4.0)); axis.plot(x_values, y_values, color=COLORS[0]); axis.scatter([x_values[0], x_values[-1]], [y_values[0], y_values[-1]], c=[COLORS[2], COLORS[1]], s=28); axis.set_aspect("equal", adjustable="datalim"); axis.set(xlabel=xlabel, ylabel=ylabel)
    return _finish(figure, axis, title=title, output=output)


def plot_trajectory_3d(x, y, z, *, xlabel, ylabel, zlabel, title=None, output=None):
    use_paper_style(); figure = plt.figure(figsize=(5.0, 4.0)); axis = figure.add_subplot(111, projection="3d"); axis.plot(x, y, z, color=COLORS[0]); axis.set(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel)
    if title: axis.set_title(title)
    figure.tight_layout()
    if output is not None: save_figure(figure, output)
    return figure, axis


def plot_sensitivity(data, *, parameter_column="parameter", change_column="change_rate", value_column="output_change_rate", xlabel="Parameter change", ylabel="Output change", title=None, output=None):
    grouped = {str(name): group[value_column].to_numpy() for name, group in data.groupby(parameter_column)}
    changes = next(iter(data.groupby(parameter_column)))[1][change_column].to_numpy()
    return plot_multi_series(changes, grouped, xlabel=xlabel, ylabel=ylabel, title=title, output=output)


def plot_convergence(iterations, values, *, xlabel, ylabel, title=None, output=None, logy=False):
    figure, axis = plot_time_series(iterations, values, xlabel=xlabel, ylabel=ylabel, title=title, output=None)
    if logy: axis.set_yscale("log")
    if output is not None: save_figure(figure, output)
    return figure, axis


def plot_heatmap(matrix, *, xlabel, ylabel, colorbar_label, x_ticks=None, y_ticks=None, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.0, 3.8)); image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="viridis"); colorbar = figure.colorbar(image, ax=axis); colorbar.set_label(colorbar_label); axis.set(xlabel=xlabel, ylabel=ylabel)
    if x_ticks is not None: axis.set_xticks(np.arange(len(x_ticks)), x_ticks)
    if y_ticks is not None: axis.set_yticks(np.arange(len(y_ticks)), y_ticks)
    return _finish(figure, axis, title=title, output=output)


def plot_contour(x, y, z, *, xlabel, ylabel, colorbar_label, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.0, 3.8)); contour = axis.contourf(x, y, z, levels=20, cmap="viridis"); figure.colorbar(contour, ax=axis, label=colorbar_label); axis.set(xlabel=xlabel, ylabel=ylabel)
    return _finish(figure, axis, title=title, output=output)


def plot_surface_3d(x, y, z, *, xlabel, ylabel, zlabel, title=None, output=None):
    use_paper_style(); figure = plt.figure(figsize=(5.2, 4.1)); axis = figure.add_subplot(111, projection="3d"); surface = axis.plot_surface(x, y, z, cmap="viridis", edgecolor="none"); figure.colorbar(surface, ax=axis, shrink=0.65, pad=0.12); axis.set(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel)
    if title: axis.set_title(title)
    figure.tight_layout()
    if output is not None: save_figure(figure, output)
    return figure, axis


def plot_residual(x, residuals, *, xlabel, ylabel="Residual", title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.0, 3.2)); axis.axhline(0.0, color="#555555", linewidth=0.8); axis.scatter(x, residuals, s=18, color=COLORS[0]); axis.set(xlabel=xlabel, ylabel=ylabel)
    return _finish(figure, axis, title=title, output=output)


def plot_parameter_comparison(names, values, *, xlabel, ylabel, title=None, output=None):
    use_paper_style(); figure, axis = plt.subplots(figsize=(5.0, 3.2)); axis.bar(names, values, color=COLORS[:len(names)]); axis.set(xlabel=xlabel, ylabel=ylabel)
    return _finish(figure, axis, title=title, output=output)
