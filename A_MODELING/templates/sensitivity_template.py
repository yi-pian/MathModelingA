"""Baseline -> local percentage perturbations -> figure -> Origin table."""

from pathlib import Path
import sys

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))

from core.export import export_origin_table
from core.plotting import plot_sensitivity
from core.sensitivity import multi_parameter_sensitivity

OUTPUT = ROOT / "results" / "template_sensitivity"


def response(parameters):
    return parameters["speed_m_s"] ** 2 / (2 * parameters["deceleration_m_s2"])


def main():
    data = multi_parameter_sensitivity(response, {"speed_m_s": 20.0, "deceleration_m_s2": 5.0}, changes=(-0.10, -0.05, -0.01, 0.0, 0.01, 0.05, 0.10))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plot_sensitivity(data, xlabel="Parameter change rate (-)", ylabel="Stopping-distance change rate (-)", output=OUTPUT / "sensitivity")
    export_origin_table(OUTPUT / "sensitivity.xlsx", data, x_column="change_rate", metadata={"method": "one-at-a-time local perturbation"})


if __name__ == "__main__": main()
