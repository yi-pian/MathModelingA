# 2022A 独立反向审查

结论：**PASS**

本轮不调用模型求解器，只重新读取最终指标、官方模板结果、图表和 Origin 数据。

## completion

- PASS — Q1 declared status：PASS
- PASS — Q2 declared status：PASS
- PASS — Q3 declared status：PASS
- PASS — Q4 declared status：PASS
## formula

- PASS — angle unit is rad：rad
- PASS — Q3 state order fixed：['x_rel', 'z_f', 'theta_f', 'theta_o', 'x_dot_rel', 'v_f', 'omega_f', 'omega_o']
- PASS — Q3 nonlinear model degenerates to heave：max error=6.809e-11
- PASS — Q3 small-signal linearization：relative error=1.365e-06
- PASS — inertia convention fully recorded：keys=['float_components', 'float_pitch_inertia', 'oscillator_axis_distance', 'oscillator_centroid_pitch_inertia']
## precision

- PASS — Q1 linear tolerance refinement：1.266e-06 -> 2.182e-08
- PASS — Q1 nonlinear tolerance refinement：5.504e-06 -> 1.795e-07
- PASS — Q1 long-transient frequency cross-check：relative error=4.212e-10
- PASS — Q2 frequency/shooting agreement：difference=3.684e-09 W
- PASS — Q2 nonlinear repeatability：range=0.000e+00 W
- PASS — Q3 periodic shooting closure：residual=6.053e-16
- PASS — Q3 long-transient agreement：relative error=3.792e-07
- PASS — Q4 strict shooting closure：1.551e-12 -> 7.813e-14 -> 9.992e-16
- PASS — Q1 DOP853/RK45 agreement：max difference=2.574e-09
## energy

- PASS — Q2 periodic energy balance：residual=-3.239e-06 W
- PASS — Q4 periodic energy balance：residual=-4.374e-11 W
## power

- PASS — Q4 channel sum：residual=7.858e-16 W
- PASS — all reported PTO powers nonnegative：minimum >= 0 W
## optimization

- PASS — Q2 nonlinear neighborhood：best neighbor=229.993669247 W
- PASS — Q4 neighborhood：best neighbor=318.206804892 W
- PASS — Q4 bounds and constrained upper optimum：(59120.869430, 100000.0)
- PASS — optimizers report success：global/local/strict_local
## excel

- PASS — result1-1.xlsx dimensions/time/finite：shape=(898, 5), t=0.0..179.4
- PASS — result1-1.xlsx official template preserved：sheet/header/merged cells
- PASS — result1-2.xlsx dimensions/time/finite：shape=(898, 5), t=0.0..179.4
- PASS — result1-2.xlsx official template preserved：sheet/header/merged cells
- PASS — result3.xlsx dimensions/time/finite：shape=(733, 9), t=0.0..146.4
- PASS — result3.xlsx official template preserved：sheet/header/merged cells
- PASS — Q1 key row matches metrics：max difference=0.000e+00
- PASS — Q3 key row matches metrics：max difference=2.220e-16
## figures

- PASS — all PNG/PDF/SVG files exist：files=21
- PASS — all Origin workbooks exist：files=11
- PASS — Q4 plotted data matches final metrics：max difference=5.684e-14 W
- PASS — Q2 periodic power-time table matches optimum：average=229.994339345 W
- PASS — Origin neighborhood tables match final metrics：max difference=4.803e-11 W
## performance

- PASS — all question runtimes recorded：q1_seconds=0.546s, q2_seconds=30.504s, q3_seconds=0.460s, q4_seconds=109.119s

## 审查员结论

未发现公式符号、单位/弧度、状态顺序、根残差、优化方向、Excel 模板或图表数据不一致。Q4 的旋转阻尼位于题设上界，是受约束最优而非内部驻点。浮子壳体转动惯量依赖题意解释，已显式记录并做 ±10% 灵敏度，因此保留为模型假设而非神秘常数。
