"""Geometry workflow with explicit global xyz coordinates and a spherical obstacle."""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import export_origin_table
from core.geometry import line_of_sight_blocked_by_sphere, point_to_segment_distance

OUTPUT = ROOT / "results" / "template_geometry"


def evaluate(observer_xyz_m, target_xyz_m, obstacle_center_xyz_m, obstacle_radius_m):
    clearance_m = point_to_segment_distance(obstacle_center_xyz_m, observer_xyz_m, target_xyz_m) - obstacle_radius_m
    blocked = line_of_sight_blocked_by_sphere(observer_xyz_m, target_xyz_m, obstacle_center_xyz_m, obstacle_radius_m)
    return {"clearance_m": clearance_m, "blocked": blocked}


def main():
    observer = np.array([-2.0, 0.0, 0.0]); target = np.array([2.0, 0.0, 0.0]); center = np.zeros(3)
    result = evaluate(observer, target, center, 0.5)
    if not result["blocked"] or result["clearance_m"] > 0: raise RuntimeError("analytic obstruction check failed")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    points = pd.DataFrame({"x_m": [*observer[:1], *center[:1], *target[:1]], "y_m": [observer[1], center[1], target[1]], "z_m": [observer[2], center[2], target[2]], "role": ["observer", "obstacle", "target"]})
    export_origin_table(OUTPUT / "geometry.xlsx", points, x_column="x_m", metadata={"coordinate_system": "global right-handed xyz", "obstacle_radius_m": "0.5"})


if __name__ == "__main__": main()
