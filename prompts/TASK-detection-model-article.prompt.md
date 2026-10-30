---
task: /Users/boyang/repo-quake/plans/TASK-detection-model-article.md
status: done
from: Planner
to: Executor
created: 2026-10-30
---

# 任务：repo-quake 方法论文章 docs/detection-model.md

## 目标

写一篇方法论文章 `docs/detection-model.md`：论证 `Detection = reaches-the-eyes × willing-to-report × blocks-the-path` 是评测失效的统一解释框架，并把 Witness 原则递归应用到评测栈自身。成功标准：五节齐全、每个关键论点带出处、案例数字与 ledger 一致。**单文件交付，零 git 命令，零代码改动。**

## 并行隔离约束（重要——本任务与 factorial 任务在同一仓库并行）

另一 Executor 正在本仓库的 `witness/factorial/`、`ledger/`、`tests/` 上工作。你：
- 只新建 `/Users/boyang/repo-quake/docs/detection-model.md` 这一个文件；
- **不运行任何 git 写命令**（不 add / commit / checkout / branch / stash）；
- 开工前核对 `git branch --show-current` 输出为 `feat/flaw-ledger-schema`，不是则命中硬停止条件 4，停下上报。

## 开工方式

1. 先读任务契约 `/Users/boyang/repo-quake/plans/TASK-detection-model-article.md`——五节内容要求、ABC 论文事实、纪律全在里面，以契约为准。
2. 素材（只读）：`/Users/boyang/repo-quake/ledger/ledger.json`、`/Users/boyang/repo-quake/docs/eval-evidence-guide.md`、`/Users/boyang/repo-quake/docs/phase1-report.md`、`/Users/boyang/repo-quake/docs/phase1p-report.md`、`/Users/boyang/repo-quake/docs/phase2-report.md`、`/Users/boyang/repo-quake/README.md`、`/Users/boyang/repo-quake/plans/TASK-factorial-probes.md`。
3. 文风基准：`/Users/boyang/repo-quake/docs/phase1-report.md` 与 `docs/eval-evidence-guide.md`（结论前置、密度高、中文）。

## 涉及文件（绝对路径）

新建：
- /Users/boyang/repo-quake/docs/detection-model.md（唯一交付物）

协议文件（本任务自身记录）：
- /Users/boyang/repo-quake/plans/TASK-detection-model-article.md（只读契约）
- /Users/boyang/repo-quake/prompts/TASK-detection-model-article.status.md（过程记录，由你追加）

## 验收标准（DoD）

1. `docs/detection-model.md` 落盘，五节齐全（三因子模型 / 三因子重审已知失效 / 哨兵=故障-阻断转换器 / Witness 原则递归 / 防御面与进攻面）。
2. 每个关键论点带出处（ledger id 如 RQ-F-004 / docs 文件名 / arXiv:2507.02825）；案例数字与 ledger.json 与各期报告原句一致。
3. 术语与 docs/eval-evidence-guide.md 一致（三本账、五字段、挡路词汇）。
4. `git status --short` 仅新增 `docs/detection-model.md`；全程零 git 写命令。

## 上游任务产出

- 分支 `feat/flaw-ledger-schema` 上已提交的台账体系（ledger/SCHEMA.md、ledger/ledger.json 30 条）——文章引用其数据。

## 硬停止条件（命中任一即停并上报，不硬试、不回滚）

1. 同一处修改尝试超过 3 次仍未通过；
2. 需要改动上述清单之外的文件（含任何 git 写操作）；
3. 素材中找不到支撑某节论点的证据；
4. 认为验收标准或任务范围本身有误、互斥或已过时（含当前分支不符合隔离约束）。

## 只读约束

TASK 文件与本文件整体（含 front matter 状态头）对你只读；状态头由 Owner 维护。
对验收标准有异议时，命中硬停止条件 4，停下上报，不得修改。

## 过程记录

- 每完成一个 step、或命中硬停止条件时，向 `/Users/boyang/repo-quake/prompts/TASK-detection-model-article.status.md` 追加一行：
  `YYYY-MM-DD HH:mm | step N | done/blocked | 证据（命令+结果 / 文件路径） | 下一步`
- 只追加，不修改已有行。中断续跑时，先读该 status 文件再继续干活。
- status 文件为协议约定写入，不计入「涉及文件」清单之外的改动。

## 上报格式

停止或完成时输出：当前状态（done / stopped）、已改动文件列表、关键 diff 摘要、自测命令与结果、已知风险 / 卡点描述，并附 status 文件绝对路径（未写过程记录视为未完成）。
