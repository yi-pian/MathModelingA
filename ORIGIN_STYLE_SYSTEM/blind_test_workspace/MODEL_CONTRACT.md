# 2020A Blind-Test Numerical Model Contract

Purpose: provide a self-contained numerical result package for Graph Editor selection. No plotting is permitted.

## State model

The PCB-center temperature `T(t)` follows a lumped thermal-inertia equation

`dT/dt = k(T) [Ta(x(t)) - T]`, `x(t) = v t`,

where `Ta(x)` is the stationary oven-air temperature profile and `v` is conveyor speed.

`Ta(x)` is constructed from the commanded zone temperatures, interpolation across uncontrolled gaps/front/rear regions, a calibrated furnace-entry infiltration exponent, a calibrated cooling-transition length, and one calibrated spatial smoothing scale. The extended cooling transition represents boundary influence between the last reflow zone and the nominal 25 °C cooling zones.

`k(T,Ta) = exp[-log_tau0 - beta (T - 150)/100 - gamma_c w_c]`,

where `w_c` changes smoothly from zero in heating to one in cooling. The asymmetric time constant is required because the official cooling section cannot be represented by the heating response constant.

This temperature dependence is an effective representation of combined convection and through-thickness thermal response. It is a calibration model, not a claim of separately identifiable heat-transfer/material parameters.

## Calibration

Fit `log_tau0`, `beta`, cooling multiplier, furnace-entry exponent, and spatial smoothing scale to the official 70 cm/min experiment by robust nonlinear least squares. Report RMSE, MAE, maximum absolute residual, and sampled-zone validation.

Good agreement supports calibration adequacy only. It does not prove parameter identifiability.

## Process metrics

- maximum rising slope, `°C/s`;
- minimum falling slope, `°C/s`;
- duration in `150–190 °C` on the rising branch, `s`;
- duration above `217 °C`, `s`;
- peak temperature, `°C`;
- Q3 area: integral of `T-217` from the upward `217 °C` crossing to the peak, `°C·s`;
- Q4 asymmetry: integrated absolute left/right temperature difference around the peak, normalized by the common comparison duration, with unmatched above-217 tail penalized.

## Optimization

Q2 uses monotonic bounded search for maximum feasible speed with fixed temperatures.

Q3 searches the official bounds

- `T1–5: 165–185 °C`
- `T6: 185–205 °C`
- `T7: 225–245 °C`
- `T8–9: 245–265 °C`
- speed: `65–100 cm/min`

using differential evolution with explicit feasibility penalties and local refinement.

Q4 minimizes asymmetry subject to all process limits and an area cap of 105% of the Q3 minimum. This expresses “combine with Q3” as a transparent lexicographic compromise.

## Limitation

All optimum statements are restricted to the adopted lumped model, the official parameter bounds, the stated Q4 compromise rule, and the numerical search performed. Global optimality is not proven.
