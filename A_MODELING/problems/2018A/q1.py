"""Question 1: calibrated temperature field and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calibration import CalibrationResult, calibrate
from common import HeatSystem, SimulationResult, energy_balance_residual, interface_diagnostics, make_system, simulate


@dataclass(frozen=True)
class Q1Result:
    calibration: CalibrationResult
    system: HeatSystem
    simulation: SimulationResult
    interface_max_temperature_residual_c: float
    interface_max_flux_residual_w_m2: float
    energy_max_residual_w_m2: float
    elapsed_seconds: float


def solve_q1(calibration: CalibrationResult | None = None, *, target_dx_m: float = 1.0e-4, dt_s: float = 1.0) -> Q1Result:
    started = perf_counter()
    calibration = calibrate(final_dx_m=target_dx_m, dt_s=dt_s) if calibration is None else calibration
    system = make_system(75.0, calibration.h_out_w_m2k, calibration.h_skin_w_m2k, target_dx_m=target_dx_m)
    simulation = simulate(system, 5400.0, dt_s=dt_s)
    interfaces = interface_diagnostics(system, simulation.temperature_c[-1])
    energy = energy_balance_residual(system, simulation)
    return Q1Result(
        calibration=calibration,
        system=system,
        simulation=simulation,
        interface_max_temperature_residual_c=float(interfaces["temperature_residual_c"].abs().max()),
        interface_max_flux_residual_w_m2=float(interfaces["heat_flux_residual_w_m2"].abs().max()),
        energy_max_residual_w_m2=float(np.max(np.abs(energy))),
        elapsed_seconds=perf_counter() - started,
    )


if __name__ == "__main__":
    result = solve_q1()
    print(
        {
            "h_out_w_m2k": result.calibration.h_out_w_m2k,
            "h_skin_w_m2k": result.calibration.h_skin_w_m2k,
            "rmse_c": result.calibration.rmse_c,
            "mae_c": result.calibration.mae_c,
            "r2": result.calibration.r2,
            "final_skin_temperature_c": result.simulation.skin_temperature_c[-1],
            "energy_max_residual_w_m2": result.energy_max_residual_w_m2,
            "elapsed_seconds": result.elapsed_seconds,
        }
    )
