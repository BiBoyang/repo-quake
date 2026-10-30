# REVIEW: TASK-factorial-probes（2026-10-30）

- Reviewer: Planner
- Executor: Opus 5.5（Owner 外部派发）
- 分支: `feat/factorial-probes`（基于 feat/flaw-ledger-schema，未提交）
- 结论: **Approved**

## 审计表（证据制，逐项）

| 检查项 | 结果 | 证据 |
|---|---|---|
| TASK/PROMPT 哈希复核 | Done | sha256 `32ad0367…`/`c04ffdbc…` 与派发留痕一致 |
| status 文件轨迹 | Done | `prompts/TASK-factorial-probes.status.md` S0–S4 每步 + final + 批准后补丁（19:07）共 10+ 行，含自抓自修 1 处审计缺陷的记录 |
| S0 schema v1.1 迁移 | Done | ledger.json 实际 diff 恰 4 行（version 1→2、#1371 merged→closed-fixed、RQ-F-006 unknown→on-path-no-gap、explanation 同步句）；SCHEMA 升 v1.1 带版本沿革；upstream 枚举拆分与第五值落 SCHEMA |
| S1 实验卡 | Done（抽查） | cards/W1.md frontmatter 标注 `role: positive-control`、`path_relation: blocks-path`；五卡齐（W1–W5 覆盖全枚举） |
| S2/S3 物料与驱动 | Done（实跑） | `run_factorial.sh --dry-run` DRY-RUN GREEN（materials/registry/cards/witness/prompt/plan/runs/audit 八段 + prereg 段 S4 后转 ok）；`--fire` 直接 exit 3 且不建目录（开火闸门有效）；HOST_ENTRY=disabled + dispatch_host 桩 |
| S4 预注册包 | Done | RUBRIC/INVALID-RULES/EXPERIMENT-CARD 三文件（17 条冻结哈希、planned_runs=168、W1 gate、停止条件）；占位词扫描 0 命中 |
| 基础校验（Planner 实跑） | Done | `ledger-check` exit 0（OK 30 entries, 19 cells, 97 evidence paths）；`run_tests.sh` ALL TESTS PASSED（48 tests，含 [ledger-check] 与 [factorial-dry-run]） |
| 宿主调用审计 | Done | 脚本中 kimi/codex 字样仅为标签与检测正则（148–150 行是"审计宿主调用"的正则，不是调用）；--fire 默认拒绝 |
| 改动范围 | Done | `git diff -- targets` 为空；改动 = 声明的 5 改 + 11 新 + status；T3 的 4 个未跟踪文件属并行任务，未触碰 |

## Findings

- 无 Blocker / Major。
- [Minor] RQ-F-006 的 explanation 句在批准后补丁中改写为「schema v1.1 为此新增 on-path-no-gap（v1 时记 unknown）」——说明与字段值一致、v1 历史保留，处理正确；该补丁本身即本单审批后的残留修正，已验证。
- [备注] 并行 T3（detection-model-article）的 4 个文件出现在同一工作树（docs/detection-model.md 等）；其契约要求开工时分支为 feat/flaw-ledger-schema，而当前树在 feat/factorial-probes——分支切换与两任务开工的时序需待 T3 上报核对。文件集零重叠，不影响本单验收。

## 残余风险

- 开火是 Owner 专属动作：--fire 有三重闸门（DRY-RUN GREEN 前置、W1 gate、预算/不重发），但真实宿主矩阵的预算档位（72/136/168 发）仍未拍板。
- prereg 冻结哈希不含 ledger.json（正确：台账是活文档），17 条冻结覆盖物料与卡片。

## 变更摘要

5 改（ledger/SCHEMA.md、ledger/ledger.json、bin/ledger-check、tests/run_tests.sh、tests/test_ledger_check.py）+ 11 新（witness/factorial/ 物料树：cards×5、gen_materials.sh、run_factorial.sh、prereg×3、tests/test_factorial_materials.py 等）。
