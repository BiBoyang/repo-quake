# witness/factorial：正交探针实验包（已备好，未开跑）

要回答的问题：在 `targets/greeting-agent` 上，一处伤口会不会被宿主报告？这有多大程度取决于伤口与任务路径的关系（`path_relation`）？又有多大程度受外壳（读不读）和模型（报不报）调节？

实验包 2026-10-30 造好，至今没有开跑过，宿主调用为零。它原定是第 3 期。第 3 期后来指 2026-10-15 那次 metacodes 断流快速探测，所以从实验卡 v3（2026-11-21）起，本包的标签改为 `factorial`。

| 路径 | 作用 |
|---|---|
| `prereg/EXPERIMENT-CARD.md` | 冻结的实验卡：假设、因子矩阵、预算三档（72 / 136 / 168 发）、开火顺序、停止条件、落账规则、17 条冻结哈希、卡片沿革 |
| `prereg/RUBRIC.md`、`prereg/INVALID-RULES.md` | 分级规则和 invalid 规则，同样冻结 |
| `cards/W1.md`–`W5.md` | 五张伤口卡：每类 `path_relation` 一张，W1 是阳性对照 |
| `gen_materials.sh` | 生成六个变体（C0 + W1–W5）和哈希登记表 |
| `run_factorial.sh` | 驱动。`--dry-run` 把每一发都演练一遍，不派发任何宿主；开火入口保留着，但处于关闭状态 |

跑一次 dry-run（零成本）：

```bash
bash witness/factorial/run_factorial.sh --dry-run
```

`tests/run_tests.sh` 的 `[factorial-dry-run]` 每次都跑它，`tests/test_factorial_materials.py` 还会核对物料能否复算。开火由 Owner 进行，流程见实验卡 §11。
