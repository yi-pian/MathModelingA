"""Cross-question energy, sensitivity, Excel, and performance validation."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "core").is_dir())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.integration import integrate_samples
from core.ode import solve_ode
from core.performance import benchmark
from core.sensitivity import one_parameter_sensitivity
from core.validation import ValidationReport
from physics import (
    harmonic_state,
    heave_frequency_response,
    heave_rhs,
    nonlinear_coupled_rhs,
    nonlinear_observables,
    pitch_frequency_response,
)
from power import heave_power, rotational_power
from problem_data import PHYSICAL, wave_case
from q2 import _periodic_power
from q1 import official_times as q1_official_times, solve_case
from q3 import solve_formal
from q4 import _periodic_coupled_power
from steady_state import solve_periodic_orbit


RESULTS = ROOT / "results" / "2022A"


def _mean(time, values):
    return integrate_samples(time, values, method="simpson") / (time[-1] - time[0])


def q2_nonlinear_energy_balance(metrics):
    wave = wave_case(2)
    scale = metrics["nonlinear"]["optimal_scale"]
    exponent = metrics["nonlinear"]["optimal_exponent"]
    equivalent = max(1.0, scale * 0.1**exponent)
    guess = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, equivalent))[:, 0]
    orbit = solve_periodic_orbit(heave_rhs(wave, scale, exponent), wave.omega, guess, samples_per_cycle=512, rtol=1e-10, atol=1e-12)
    time = orbit.ode.time
    vf = orbit.ode.state[2]
    relative = orbit.ode.state[3] - orbit.ode.state[2]
    input_power = wave.excitation_force * np.cos(wave.omega * time) * vf
    radiation = wave.radiation_heave_damping * vf**2
    pto = heave_power(relative, scale, exponent)
    residual = _mean(time, input_power - radiation - pto)
    return {"input_w": _mean(time, input_power), "radiation_w": _mean(time, radiation), "pto_w": _mean(time, pto), "residual_w": residual}


def q4_energy_balance(metrics):
    wave = wave_case(4)
    linear = metrics["optimal_linear_damping_n_s_m"]
    rotation = metrics["optimal_rotational_damping_n_m_s"]
    heave_guess = harmonic_state([0.0], wave.omega, heave_frequency_response(wave, linear))[:, 0]
    pitch_guess = harmonic_state([0.0], wave.omega, pitch_frequency_response(wave, rotation))[:, 0]
    guess = np.array([heave_guess[1]-heave_guess[0], heave_guess[0], pitch_guess[0], pitch_guess[1], heave_guess[3]-heave_guess[2], heave_guess[2], pitch_guess[2], pitch_guess[3]])
    orbit = solve_periodic_orbit(nonlinear_coupled_rhs(wave, linear, rotation), wave.omega, guess, samples_per_cycle=512, rtol=1e-10, atol=1e-12)
    time = orbit.ode.time
    x_dot = orbit.ode.state[4]
    float_velocity = orbit.ode.state[5]
    float_omega = orbit.ode.state[6]
    relative_omega = orbit.ode.state[7] - float_omega
    input_power = wave.excitation_force*np.cos(wave.omega*time)*float_velocity + wave.excitation_moment*np.cos(wave.omega*time)*float_omega
    radiation = wave.radiation_heave_damping*float_velocity**2 + wave.radiation_pitch_damping*float_omega**2
    pto = heave_power(x_dot, linear) + rotational_power(relative_omega, rotation)
    return {"input_w": _mean(time, input_power), "radiation_w": _mean(time, radiation), "pto_w": _mean(time, pto), "residual_w": _mean(time, input_power-radiation-pto)}


def run() -> dict:
    metrics = {name: json.loads((RESULTS / f"{name}_metrics.json").read_text(encoding="utf-8")) for name in ("q1", "q2", "q3", "q4")}
    q2_energy = q2_nonlinear_energy_balance(metrics["q2"])
    q4_energy = q4_energy_balance(metrics["q4"])

    q1_wave = wave_case(1)
    q1_dop853 = solve_case(10000.0, 0.0, rtol=1e-9, atol=1e-11)
    q1_rk45 = solve_ode(
        heave_rhs(q1_wave, 10000.0),
        (0.0, 40.0 * q1_wave.period),
        np.zeros(4),
        sample_times=q1_official_times(q1_wave.omega),
        method="RK45",
        rtol=1e-9,
        atol=1e-11,
        max_step=q1_wave.period / 32.0,
    )
    solver_comparison = {
        "methods": ["DOP853", "RK45"],
        "rtol": 1e-9,
        "atol": 1e-11,
        "max_abs_difference": float(np.max(np.abs(q1_dop853.state - q1_rk45.state))),
        "nfev": [q1_dop853.nfev, q1_rk45.nfev],
    }

    baseline_inertia = PHYSICAL.float_pitch_inertia
    wave3 = wave_case(3)
    def q3_pitch_amplitude(parameters):
        result = solve_formal_with_inertia(parameters["float_inertia"])
        observed = nonlinear_observables(result.state)
        return float(np.max(np.abs(observed[2])))

    def solve_formal_with_inertia(float_inertia):
        times = np.linspace(0.0, 40.0 * wave3.period, 1601)
        from core.ode import solve_ode
        return solve_ode(nonlinear_coupled_rhs(wave3, 10000.0, 1000.0, float_inertia_override=float_inertia), (0.0, times[-1]), np.zeros(8), sample_times=times, method="DOP853", rtol=2e-9, atol=2e-11, max_step=wave3.period/32.0)

    sensitivity = one_parameter_sensitivity(
        q3_pitch_amplitude,
        {"float_inertia": baseline_inertia},
        "float_inertia",
        changes=(-0.10, -0.05, 0.0, 0.05, 0.10),
    )
    from core.export import export_origin_table
    export_origin_table(RESULTS / "origin_data" / "q3_inertia_sensitivity.xlsx", sensitivity, x_column="change_rate", metadata={"purpose": "Q3 float inertia sensitivity"})

    rhs = nonlinear_coupled_rhs(wave_case(4), metrics["q4"]["optimal_linear_damping_n_s_m"], metrics["q4"]["optimal_rotational_damping_n_m_s"])
    rhs_benchmark = benchmark(rhs, 0.0, np.zeros(8), repeats=1000, warmup=10)
    q1_ode_benchmark = benchmark(lambda: solve_case(10000.0, 0.0), repeats=3, warmup=1)
    q2_periodic_benchmark = benchmark(
        lambda: _periodic_power(metrics["q2"]["nonlinear"]["optimal_scale"], metrics["q2"]["nonlinear"]["optimal_exponent"], samples=64, rtol=2e-8, atol=2e-10)[0],
        repeats=3,
        warmup=1,
    )
    q4_periodic_benchmark = benchmark(
        lambda: _periodic_coupled_power(metrics["q4"]["optimal_linear_damping_n_s_m"], metrics["q4"]["optimal_rotational_damping_n_m_s"], samples=64, rtol=2e-8, atol=2e-10)["total_power_w"],
        repeats=3,
        warmup=1,
    )
    performance = {
        "q1_seconds": metrics["q1"]["runtime_seconds"],
        "q2_seconds": metrics["q2"]["runtime_seconds"],
        "q3_seconds": metrics["q3"]["runtime_seconds"],
        "q4_seconds": metrics["q4"]["runtime_seconds"],
        "q1_single_ode": q1_ode_benchmark,
        "q4_rhs": rhs_benchmark,
        "q2_one_period_shooting": q2_periodic_benchmark,
        "q4_one_period_shooting": q4_periodic_benchmark,
    }
    (RESULTS / "performance.json").write_text(json.dumps(performance, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ValidationReport()
    for name, value in metrics.items(): report.add(f"{name.upper()} status", value["status"] == "PASS")
    report.add("Q2 nonlinear energy balance", abs(q2_energy["residual_w"]) < 2e-5, f"residual={q2_energy['residual_w']:.3e} W")
    report.add("Q4 coupled energy balance", abs(q4_energy["residual_w"]) < 2e-5, f"residual={q4_energy['residual_w']:.3e} W")
    report.add("Q1 DOP853/RK45 agreement", solver_comparison["max_abs_difference"] < 1e-7, f"max difference={solver_comparison['max_abs_difference']:.3e}")
    report.add("Q3 inertia sensitivity finite", np.all(np.isfinite(sensitivity["output"])), f"range={sensitivity['output'].min():.6g}..{sensitivity['output'].max():.6g} rad")
    report.add("Official Excel files", all(metrics[name].get("excel", {}).get("valid", True) if name != "q1" else all(item["valid"] for item in metrics[name]["excel"].values()) for name in metrics))
    result = {
        "status": "PASS" if report.passed else "FAIL",
        "energy": {"q2_nonlinear": q2_energy, "q4_coupled": q4_energy},
        "solver_comparison": solver_comparison,
        "inertia_sensitivity": sensitivity.to_dict(orient="records"),
        "performance": performance,
        "report": report.render(),
    }
    (RESULTS / "validation_2022a.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS / "validation_2022a.txt").write_text(report.render(), encoding="utf-8")
    if not report.passed:
        raise RuntimeError(report.render())
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
