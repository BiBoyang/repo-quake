# witness/integrity：第 0–2 期的完整性证人和驱动

第 0–2 期把故障注入打在文件上：截断、删除、引用断裂。宿主看到被改过的副本之前，先由一个确定性的检查器（guard）
读一遍，证明伤口确实送到了、长什么样。

| 文件 | 期 | 作用 |
|---|---|---|
| `eve_guard.py` | 0、1 | Eve agent 目录的完整性证人。硬错误 H1–H4（instructions 缺失或为空、引用路径不存在、skill frontmatter 为空、`tools/*.ts` 括号不平衡），告警 W1–W3（止于标题或冒号、悬挂代码围栏、空文件）。 |
| `py_guard.py` | 1′ | 小型 Python agent 项目的完整性证人。 |
| `run_matrix.sh` | 1 | Eve 检出矩阵的驱动：在哈希命名的目录里放改过的副本，先跑 `eve_guard.py`，再按格 × 宿主 × N 逐次派发无头宿主。 |
| `run_matrix_py.sh` | 1′ | PydanticAI 项目的驱动；staging 放到 `/tmp/rqs`，产物放在宿主看不见的目录树里。 |
| `run_phase2.sh` | 2 | 三家考官 skill（skill-creator、eval-guide）的驱动；加了 fake HOME，干净原件对宿主不可达。 |

这些驱动保持当时的样子，没有维护成可以直接重跑的工具：
- 里面写死了这台机器的路径，比如 `ROOT=/Users/boyang/repo-quake`、`/tmp/pydeps-venv`、skill-quake 的安装位置；
- 用的也是当时的宿主命令。

要重跑，先按现在的环境改。正交实验包（`../factorial/`）沿用 `eve_guard.py`，`run_matrix.sh` 里冻结的第 1 期 prompt 也由它沿用：dry-run 每次都会核对这两样，所以它们的内容不能改。

2026-11-21 之前，这些文件放在 `witness/` 顶层。
