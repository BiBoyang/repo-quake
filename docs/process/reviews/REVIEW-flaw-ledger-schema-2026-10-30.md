# REVIEW: TASK-flaw-ledger-schema（2026-10-30）

- Reviewer: Planner
- Executor: Opus 5.5（Owner 外部派发）
- 分支: `feat/flaw-ledger-schema`（未提交）
- 结论: **Approved**

## 审计表（证据制，逐项）

| 检查项 | 结果 | 证据 |
|---|---|---|
| PROMPT 哈希复核 | Done | sha256 `5ecd2831…` 与派发留痕一致 |
| TASK 哈希复核 | Done | sha256 `9a4c95c3…` 与派发留痕一致 |
| status 文件存在与轨迹 | Done | `prompts/TASK-flaw-ledger-schema.status.md` 8 行，3 步 + 3 条抽查 |
| 改动范围 | Done | `git status` 仅声明文件；`docs/`、`results/` 零改动 |
| S1 SCHEMA + 首条 | Done | 字段表与契约一致；术语明文对齐 evidence-guide（三本账/五字段/挡路词汇） |
| S2 校验器 + 测试 | Done | 实跑 `python3 bin/ledger-check ledger/ledger.json` exit 0（OK 30 entries, 19 cells, 97 evidence paths）；`bash tests/run_tests.sh` ALL TESTS PASSED；stdlib-only（imports 核查）；未知字段报错、L2/L3 段数=detected 为契约外增强 |
| S3 回填 + README | Done | 30 条 = F13/I7/X10；README 恰 10 行 |
| DoD 数字对账（Planner 独立重算） | Done | `runs/phase1/grades.json` 按 host+model+run 序重算：E1/E2/E3 全部 7 个带逐发分级 cell 与台账逐发一致；E3 kimik3 格（1/8，无逐发）与声明一致；phase1 全口径 22/64 成立（含 phase1p 附录 kimik3 格） |
| DoD 抽查证据 | Done | status 文件含 3 条「报告数字 ↔ 台账数字」抽查记录 |
| 覆盖完整性 | Done | phase0（clone 失败 X-001）、phase1（E1/E2/E3 + 4 条 X）、phase1p（R1/R2/R3 + kimik3）、phase2（四格 + 2 上游文档缺陷 + 7 条 I + 6 条 X）、e2e（首条 fixed + 2 条 I + 2 条 X）；诚实清单与附赠发现全入账 |

## Findings（无 Blocker / Major）

- [Minor] `upstream.status` 枚举对 `kind: issue` 复用 `merged`（SCHEMA 已书面约定"关联修复已合入并关闭"）。语义可议，建议 v1.1 拆 issue/pr 两套枚举。Executor 已自行提出，Planner 同意。
- [Minor] `path_relation` 缺"文件在路径上被完整消费、但语义上不缺口"的值（RQ-F-006 记 `unknown` 并在 attribution.explanation 说明）。建议 v1.1 增加第五值（如 `on-path-no-gap`）。Executor 已自行提出，Planner 同意。
- [Minor] RQ-F-012/013（eval-guide 上游文档/YAML 缺陷）`status: reported`、upstream #16 `open`。与 Owner 对该项目活跃度的判断（疑似 KPI 项目）相符，建议下次 sweep 时按目标选择规则（willing-to-report=0 的目标降权）给这两条加 caveat 或重估 status。不阻塞。
- [行政] PROMPT 状态头仍为 `pending`（Owner 派发时未翻 `dispatched`）。状态头归 Owner 维护，验收关闭时请翻 `done`。

## 测试与验证意见

- 校验器与全量测试由 Planner 独立实跑通过，非仅采信 Executor 上报。
- 逐发对账由 Planner 独立重算（非采信 Executor 的"18 cell 全对账"声明），初查两处"不一致"均为 Reviewer 脚本自身缺陷（host 标签映射、run 序），修正后全一致。

## 残余风险

- `runs/` 原始产物多为 gitignore，台账 evidence 指向的本地文件不随库分发——符合本仓库"产物树与证人分离"哲学，但换机克隆后 `ledger-check` 会因证据缺失报错。SCHEMA 未显式声明这一点，v1.1 可补一句"evidence 路径以实验机为锚"。
- 归因字段主观性由 `confidence` 体系兜底，已如实标注 3 条 `unable-to-separate`、1 条 `likely`。

## 变更摘要

新增 `ledger/SCHEMA.md`、`ledger/ledger.json`（30 条）、`bin/ledger-check`、`tests/test_ledger_check.py`；修改 `tests/run_tests.sh`（+6 行）、`README.md`（+11 行，含空行）。
