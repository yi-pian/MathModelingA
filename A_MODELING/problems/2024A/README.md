# 2024A 实战验收工程

本目录只存放《板凳龙》题目专用逻辑。通用库保持不变，除非后续证明确有跨题缺陷并配套 regression test。

主要文件：`common.py`、`deliverables.py`、`q1.py` 至 `q5.py`、`chain_error_export.py`、`audit.py` 和 `tests/`。运行环境使用项目根目录 `.venv`。

逐问运行示例：`.venv\\Scripts\\python.exe problems\\2024A\\q1.py`。五问完成后依次运行 `chain_error_export.py` 和 `audit.py`，生成逐链误差表与独立反向审查。

正式输出统一写入 `results/2024A/`，官方原始模板位于 `data/2024A/official/` 且只读。
