# Q1 结果摘要

- 状态：PASS
- 模型：阿基米德螺线弧长反解 + 逐节弦长 Brent 求根 + 刚性杆速度传播。
- 时间：0–300 s，步长 1 s，共 301 个状态、224 个把手。
- 弧长求根最大残差：2.140e-10 m。
- 相邻把手距离误差：maximum=1.344e-10 m，mean=1.115e-10 m，P95=1.171e-10 m。
- 中心差分速度最大误差：6.721e-09 m/s。
- 单时刻整龙平均构造耗时：0.011855 s；Q1 总计算耗时：3.635 s。
- 官方结果：[result1.xlsx](result1.xlsx)；指定节点表：[q1_selected_results.xlsx](q1_selected_results.xlsx)。
- 图：[q1_shapes.png](figures/q1_shapes.png)、[q1_speeds.png](figures/q1_speeds.png)。
