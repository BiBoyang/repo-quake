# TASK: repo-quake 缺陷台账（fault ledger）schema 与历史回填

- 日期：2026-10-30
- 分工：Planner 起草（本契约），Executor 执行，Owner 确认与派发
- 状态：待 Owner 确认（对应 PROMPT 状态头 `pending`）

## 目标

把散落在 `docs/phase*-report.md` 与 `docs/eval-evidence-guide.md` 叙事里的故障、仪器缺陷、实验效度事件，结构化为单一可校验的台账 `ledger/ledger.json`，配套 schema 文档与校验器，使跨期实验结果可累积、可比较、可追溯。

## 背景（为什么做）

- 各期报告的 x/N 数字目前锁死在叙事文本里，无法跨期聚合与比较。
- `docs/eval-evidence-guide.md` 已确立"三本账"（产品故障 / 夹具故障 / 判分器故障）与五字段观察（detected / reported / contained / recovered / reverified），台账是这套词汇的数据落地形态——**台账术语必须与该指南一致，不得另造平行词汇**。
- 检测模型 `Detection = reaches-the-eyes × willing-to-report × blocks-the-path` 要求每条记录能回答"哪个因子解释了本次检测结果"。

## 设计决策（Planner 已定；Executor 有异议走 PROMPT 硬停止条件 4）

1. 三类条目 `class`：`target-finding`（产品故障）/ `instrument-defect`（证人或判分器自身缺陷，如 skill-guard 假阳性、quick_validate 盲区）/ `experiment-invalid`（夹具与效度事件，含各期"诚实清单"）。
2. id 规则：`RQ-F-NNN` / `RQ-I-NNN` / `RQ-X-NNN`，全局唯一，只增不改。
3. 归因字段 `attribution` 允许 `confidence: confirmed | likely | unable-to-separate`——归因是解释不是测量，必须允许带 caveat（如 phase2 的记忆污染无法分离）。
4. 字段允许 optional，校验器只强制核心字段——**宁缺勿编**。
5. 台账是新增聚合层：不改 `docs/` 原文，不改 `results/` 原始产物。

## 字段规范（v1）

entry 顶层字段：

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `id` | string | 是 | `^RQ-[FIX]-\d{3}$`，全局唯一 |
| `created` | string | 是 | `YYYY-MM-DD` |
| `phase` | string | 是 | `phase0` / `phase1` / `phase1p` / `phase2` / `e2e` / … |
| `class` | string | 是 | `target-finding` / `instrument-defect` / `experiment-invalid` |
| `title` | string | 是 | 一行中文 |
| `status` | string | 是 | `open` / `reported` / `acknowledged` / `fixed` / `wontfix` / `superseded` / `n-a`（experiment-invalid 用 `n-a`） |
| `target` | object | F/I 类必填 | `{repo, artifact, version?}` |
| `fault` | object | F 类必填 | `{type, spec, delivery?, path_relation?}`；`path_relation` ∈ `blocks-path` / `redundant-backstop` / `future-use` / `weak-reference` / `unknown`（对应 phase2 报告的四类"为什么不挡路"） |
| `cells` | array | 有宿主矩阵时必填 | `[{host, model?, runs:int>0, detected:int≥0, levels?: string, notes?}]`；`detected ≤ runs`；`levels` 为逗号分隔、段数 = runs |
| `attribution` | object | target-finding 必填 | `{primary_factor, explanation, confidence, caveats?}`；`primary_factor` ∈ `blocks-path` / `reaches-eyes` / `willing-to-report` / `witness`；`confidence` ∈ `confirmed` / `likely` / `unable-to-separate` |
| `observation` | object | 可选 | `{detected, reported?, contained?, recovered?, reverified?}`，bool |
| `evidence` | array | 是，≥1 | 仓库根相对路径，校验器检查存在性 |
| `upstream` | array | 可选 | `[{kind: issue\|pr, url, status: open\|merged\|closed-unmerged\|none}]` |
| `lesson` | string | 是 | 一行提炼，不抄报告原句 |

文件骨架：`{"version": 1, "updated": "YYYY-MM-DD", "entries": [...]}`

## Steps 与 DoD

### S1 schema 文档 + 首条真实条目
- 产 `ledger/SCHEMA.md`：字段表、三类条目判定规则、两个完整示例——一条 `target-finding` 用 e2e 缓存 case（tester-army/e2e#1371/#1372），一条 `instrument-defect` 用 phase2 报告的 skill-guard 假阳性。
- 产 `ledger/ledger.json`（version=1，entries 先含 e2e 首条）。
- DoD：SCHEMA.md 与 json 字段一一对应；e2e 条目 upstream 链接正确；evidence 路径真实存在。

### S2 校验器 + 测试
- 产 `bin/ledger-check`（python3 标准库，零三方依赖）：校验 JSON 合法、id 格式与唯一、枚举合法、`detected ≤ runs`、levels 段数 = runs、evidence 存在；错误输出可读、exit 1。
- 新增 `tests/test_ledger_check.py`（仿现有 `test_*.py` 风格：合法台账通过、被破坏的临时副本必败），并在 `tests/run_tests.sh` 末尾追加调用。
- DoD：`python3 bin/ledger-check ledger/ledger.json` exit 0；`bash tests/run_tests.sh` 全绿（含新测试）。

### S3 历史回填 + README
- 通读 `docs/phase0-notes.md`、`phase1-report.md`、`phase1p-report.md`、`phase2-report.md`、`phase2-notes.md`、`eval-evidence-guide.md`，回填全部历史条目（预计 10–20 条）。
- 各期"诚实清单"入 `experiment-invalid`；"附赠发现"入 `instrument-defect`。
- `README.md` 末尾加 ≤10 行"缺陷台账"小节：一句话定位 + 校验命令。
- DoD：校验器通过；抽 3 条在 status 文件记录"报告数字 ↔ 台账数字"核对证据；`git status` 显示 docs/ 与 results/ 零改动。

## 风险与回滚

- 归因主观性 → `confidence` + `caveats` 字段兜底，README 注明"归因是解释不是测量"。
- 历史信息不足 → optional 字段兜底，缺就缺，不编造。
- 回滚点：全部产物为新增文件，`git checkout` 即回滚；README 小节独立可删。

## 基础校验命令

```bash
cd /Users/boyang/repo-quake && python3 bin/ledger-check ledger/ledger.json && bash tests/run_tests.sh
```
