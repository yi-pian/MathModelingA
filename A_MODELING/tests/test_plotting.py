from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.plotting import plot_contour, plot_scatter_fit, plot_surface_3d, plot_time_series, plot_trajectory_2d


def test_plot_files_exist(tmp_path):
    x = np.linspace(0, 1, 10)
    figure, _ = plot_time_series(x, x**2, xlabel="Time (s)", ylabel="Value (-)", output=tmp_path / "series")
    plt.close(figure)
    assert all((tmp_path / f"series.{extension}").exists() for extension in ("png", "pdf", "svg"))


def test_scatter_contour_and_surface_smoke(tmp_path):
    x = np.linspace(-1, 1, 8); grid_x, grid_y = np.meshgrid(x, x); z = grid_x**2 + grid_y**2
    figures = [
        plot_scatter_fit(x, x**2, x**2, xlabel="x", ylabel="y")[0],
        plot_contour(grid_x, grid_y, z, xlabel="x", ylabel="y", colorbar_label="z")[0],
        plot_surface_3d(grid_x, grid_y, z, xlabel="x", ylabel="y", zlabel="z")[0],
        plot_trajectory_2d(pd.Series(x), pd.Series(x**2), xlabel="x", ylabel="y")[0],
    ]
    for figure in figures: plt.close(figure)
