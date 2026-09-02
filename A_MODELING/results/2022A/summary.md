# 2022A 结果摘要

完整实战验收、模型约定、精度、性能、Excel/Origin 和缺陷分类见 [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)，独立只读复核见 [AUDIT_REPORT.md](AUDIT_REPORT.md)。

- Q1–Q4 题目级状态：PASS。
- Q2 常阻尼最优：`37193.813485 N·s/m`，`229.333939838 W`。
- Q2 速度幂阻尼最优：`lambda=100000`、`p=0.415763073`，`229.994292217 W`。
- Q4 最优：直线阻尼 `59120.869430 N·s/m`、旋转阻尼 `100000 N·m·s`，总功率 `318.206804895 W`。
- Q4 周期能量残差：`-4.374e-11 W`；严格射击残差：`9.992e-16`。
- 官方结果文件：`result1-1.xlsx`、`result1-2.xlsx`、`result3.xlsx`，全部回读 PASS。
- 全库测试：66 passed；独立交付审查：40/40 PASS。
- 总体结论：CONDITIONAL PASS；条件来自 Q3/Q4 转动惯量和参考轴的题意解释敏感性，不来自数值不收敛。
