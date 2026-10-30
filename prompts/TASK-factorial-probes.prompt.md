---
task: /Users/boyang/repo-quake/plans/TASK-factorial-probes.md
status: pending
from: Planner
to: Executor
created: 2026-10-30
---

# 任务：wound taxonomy v1.1 + 三因子正交探针实验包（phase3 物料）

## 目标

构建 phase3 正交实验物料包：伤口按台账 `path_relation` 五类系统设计（× 外壳 × 模型因子），配套 schema v1.1、变体生成器、dry-run 驱动脚本与预注册包。成功标准：`--dry-run` 全绿 + 基础校验全绿，且**全程零宿主调用**（开火是 Owner 后续动作）。

## 开工方式

1. 先读任务契约 `/Users/boyang/repo-quake/plans/TASK-factorial-probes.md`——设计决策、因子矩阵、Steps 与 DoD 全在里面，以契约为准。
2. 术语与纪律基准（只读）：`/Users/boyang/repo-quake/docs/eval-evidence-guide.md`、`/Users/boyang/repo-quake/ledger/SCHEMA.md`、`/Users/boyang/repo-quake/docs/phase1p-report.md`（2×2 先例）、`/Users/boyang/repo-quake/docs/phase2-report.md`（X-006 伤口设计教训）。
3. 按 S0 → S1 → S2 → S3 → S4 顺序执行，每完成一个 step 按下方「过程记录」落一行。

## 涉及文件（绝对路径）

新建：
- /Users/boyang/repo-quake/witness/factorial/cards/W1.md … W5.md（五张实验卡）
- /Users/boyang/repo-quake/witness/factorial/gen_materials.sh（变体生成器）
- /Users/boyang/repo-quake/witness/factorial/run_factorial.sh（驱动，--dry-run / --tier）
- /Users/boyang/repo-quake/witness/factorial/prereg/RUBRIC.md
- /Users/boyang/repo-quake/witness/factorial/prereg/INVALID-RULES.md
- /Users/boyang/repo-quake/witness/factorial/prereg/EXPERIMENT-CARD.md
- /Users/boyang/repo-quake/tests/test_factorial_materials.py（dry-run 物料机检）

修改：
- /Users/boyang/repo-quake/ledger/SCHEMA.md（v1.1：枚举拆分、on-path-no-gap、version 2、evidence 锚定声明）
- /Users/boyang/repo-quake/bin/ledger-check（枚举校验同步）
- /Users/boyang/repo-quake/ledger/ledger.json（迁移 RQ-F-001 issue status、RQ-F-006 path_relation；version 升 2）
- /Users/boyang/repo-quake/tests/test_ledger_check.py（新枚举用例）
- /Users/boyang/repo-quake/tests/run_tests.sh（末尾追加 factorial 物料测试调用）

只读参考（禁止修改）：
- /Users/boyang/repo-quake/targets/（greeting-agent 靶子本体；mutated copy 一律由生成器产出，不落在本目录）
- /Users/boyang/repo-quake/docs/、/Users/boyang/repo-quake/results/、/Users/boyang/repo-quake/runs/
- /Users/boyang/repo-quake/witness/ 既有脚本（eve_guard.py、run_matrix.sh 等，可参考复用逻辑但不改动）

## 验收标准（DoD）

1. `cd /Users/boyang/repo-quake && python3 bin/ledger-check ledger/ledger.json` exit 0，迁移后数据符合 v1.1 枚举。
2. `cd /Users/boyang/repo-quake && bash tests/run_tests.sh` 全绿（含新枚举用例与 factorial 物料测试）。
3. `cd /Users/boyang/repo-quake && bash witness/factorial/run_factorial.sh --dry-run` 全绿：物料树完整、哈希登记可复算、五张卡字段机检通过、健康靶子 skill-guard 基线在案。
4. 脚本审计：`run_factorial.sh` 与 `gen_materials.sh` 不含任何宿主 CLI 调用（零 API 成本）；宿主调用入口预留但默认关闭并显式标注。
5. 预注册三文件无 TODO、无占位符；W1 卡标注阳性对照；每张卡含路径触达性推演。
6. `git status` 仅出现本任务声明的新建/修改文件。
7. 变体生成器产物不写入 `targets/` 原靶目录（staging 在 /tmp 哈希路径）。

## 上游任务产出

- `feat/flaw-ledger-schema` 分支的台账体系（`ledger/SCHEMA.md` v1、`bin/ledger-check`、30 条 entries）——本任务 S0 在其上做 v1.1 演进。Owner 应已提交该分支。

## 硬停止条件（命中任一即停并上报，不硬试、不回滚）

1. 同一处修改尝试超过 3 次仍未通过；
2. 需要改动上述清单之外的文件；
3. 测试/构建失败原因超出本任务描述范围；
4. 认为验收标准或任务范围本身有误、互斥或已过时（例如认为某伤口类的 path_relation 归类不成立，或 greeting-agent 结构不足以承载某类伤口）。

## 只读约束

TASK 文件与本文件整体（含 front matter 状态头）对你只读；状态头由 Owner 维护。
对验收标准有异议时，命中硬停止条件 4，停下上报，不得修改。

## 过程记录

- 每完成一个 step、或命中硬停止条件时，向 `/Users/boyang/repo-quake/prompts/TASK-factorial-probes.status.md` 追加一行：
  `YYYY-MM-DD HH:mm | step N | done/blocked | 证据（命令+结果 / 文件路径） | 下一步`
- 只追加，不修改已有行。中断续跑时，先读该 status 文件再继续干活。
- status 文件为协议约定写入，不计入「涉及文件」清单之外的改动。

## 上报格式

停止或完成时输出：当前状态（done / stopped）、已改动文件列表、关键 diff 摘要、自测命令与结果、已知风险 / 卡点描述，并附 status 文件绝对路径（未写过程记录视为未完成）。
