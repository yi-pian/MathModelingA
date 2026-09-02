# Structured benchmark data

Run `generate_benchmarks.py` to recreate the eight deterministic datasets. These are mathematical test structures, not random-noise samples.

| File | Structure | Intended figure |
|---|---|---|
| `single_peak_time_curve.csv` | Gamma-shaped response with known peak near 7 h | single line |
| `single_peak_point.csv` | One-row maximum extracted from the single-response table | peak overlay |
| `multi_solution_time_curves.csv` | Four saturating strategies with controlled crossover | multi-line |
| `scatter_plus_fit.csv` | Quadratic truth plus deterministic oscillatory measurement deviation | scatter + fit |
| `single_parameter_sensitivity.csv` | Four asymmetric nonlinear perturbation responses | sensitivity |
| `two_parameter_objective.csv` | Smooth convex basin plus mild periodic structure | contour |
| `two_parameter_optimum.csv` | Grid-search minimum extracted from the same objective table | contour optimum overlay |
| `spatiotemporal_temperature.csv` | Moving, diffusing, decaying thermal pulse | heatmap |
| `optimization_convergence.csv` | Four deterministic convergence laws | convergence |
| `three_solution_comparison.csv` | Six normalized benefit criteria for three schemes | grouped comparison |

No stochastic generator is used, so every rerun is bitwise reproducible for the same Python version and CSV formatting. The peak and optimum overlays are auxiliary tables, not additional benchmark classes.

Phase 2 adds deterministic standard and stress datasets through `generate_phase2_data.py`. Stress cases cover dense/overlapping scatter, long labels, edge-localized heatmap structure, long convergence histories with order-of-magnitude changes, disparate multi-panel units, and a boundary optimum for 3D surface review. These files exist to test template adaptation, not to force identical axis ranges or transforms across all real data.
