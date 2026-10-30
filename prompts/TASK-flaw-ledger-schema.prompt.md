---
task: /Users/boyang/repo-quake/plans/TASK-flaw-ledger-schema.md
status: done
from: Planner
to: Executor
created: 2026-10-30
---

# 任务：repo-quake 缺陷台账 schema 与历史回填

## 目标

把 repo-quake 各期实验叙事中的故障、仪器缺陷、实验效度事件结构化为单一可校验台账 `ledger/ledger.json`，配套 schema 文档与校验器。成功标准：基础校验命令全绿，且历史报告里的每一处 x/N 数字都能在台账中找到对应条目。

## 开工方式

1. 先读任务契约 `/Users/boyang/repo-quake/plans/TASK-flaw-ledger-schema.md`——字段规范、三类条目判定规则、Steps 与 DoD 全在里面，以契约为准。
2. 术语基准（只读参考）：`/Users/boyang/repo-quake/docs/eval-evidence-guide.md`——三本账、五字段、挡路词汇的出处，台账用语必须与它一致。
3. 按 S1 → S2 → S3 顺序执行，每完成一个 step 按下方「过程记录」落一行。

## 涉及文件（绝对路径）

新建：
- /Users/boyang/repo-quake/ledger/SCHEMA.md
- /Users/boyang/repo-quake/ledger/ledger.json
- /Users/boyang/repo-quake/bin/ledger-check
- /Users/boyang/repo-quake/tests/test_ledger_check.py

修改：
- /Users/boyang/repo-quake/tests/run_tests.sh（末尾追加 ledger 测试调用）
- /Users/boyang/repo-quake/README.md（末尾追加 ≤10 行台账小节）

只读参考（禁止修改）：
- /Users/boyang/repo-quake/docs/（全部 phase 报告与 evidence guide）
- /Users/boyang/repo-quake/results/（原始实验产物，一律不改写）
- /Users/boyang/repo-quake/witness/ 与 /Users/boyang/repo-quake/bin/skill-guard

## 验收标准（DoD）

1. `cd /Users/boyang/repo-quake && python3 bin/ledger-check ledger/ledger.json` exit 0。
2. `cd /Users/boyang/repo-quake && bash tests/run_tests.sh` 全绿（含新增 ledger 测试）。
3. ledger 覆盖 phase0/1/1p/2 全部 fault cells、诚实清单与附赠发现；抽查 3 条做「报告数字 ↔ 台账数字」核对，把核对证据写进 status 文件。
4. `git status` 显示 docs/ 与 results/ 零改动，仅出现本任务声明的新建/修改文件。
5. 台账术语与 docs/eval-evidence-guide.md 一致（三本账、五字段、挡路词汇），schema 字段与 TASK 契约的字段表一致。
6. 零第三方依赖（python3 标准库）。

## 上游任务产出

无

## 硬停止条件（命中任一即停并上报，不硬试、不回滚）

1. 同一处修改尝试超过 3 次仍未通过；
2. 需要改动上述清单之外的文件；
3. 测试/构建失败原因超出本任务描述范围；
4. 认为验收标准或任务范围本身有误、互斥或已过时（例如认为 schema 字段设计不合理）。

## 只读约束

TASK 文件与本文件整体（含 front matter 状态头）对你只读；状态头由 Owner 维护。
对验收标准有异议时，命中硬停止条件 4，停下上报，不得修改。

## 过程记录

- 每完成一个 step、或命中硬停止条件时，向 `/Users/boyang/repo-quake/prompts/TASK-flaw-ledger-schema.status.md` 追加一行：
  `YYYY-MM-DD HH:mm | step N | done/blocked | 证据（命令+结果 / 文件路径） | 下一步`
- 只追加，不修改已有行。中断续跑时，先读该 status 文件再继续干活。
- status 文件为协议约定写入，不计入「涉及文件」清单之外的改动。

## 上报格式

停止或完成时输出：当前状态（done / stopped）、已改动文件列表、关键 diff 摘要、自测命令与结果、已知风险 / 卡点描述，并附 status 文件绝对路径（未写过程记录视为未完成）。
