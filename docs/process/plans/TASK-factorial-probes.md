# TASK: wound taxonomy v1.1 + 三因子正交探针实验包（phase3 物料）

- 日期：2026-10-30
- 分工：Planner 起草（本契约），Executor 执行，Owner 确认与派发
- 状态：待 Owner 确认（对应 PROMPT 状态头 `pending`）
- 前置条件：Owner 已提交 `feat/flaw-ledger-schema` 分支（上一任务 Approved 产物）。未提交前不得派发本任务。

## 目标

把 repo-quake 的检出解释从"伤与路径的关系"（相关性叙事）升级为**因子分解测量**：构建正交实验物料包——伤口按台账 `path_relation` 分类法系统设计， crossed by 外壳 × 模型——使后续开火后能输出每个因子的边际检出率与交互效应，落账为 `phase3`。本任务**只造武器，不开火**：零宿主调用，全部产物用 dry-run 验证。

## 背景（为什么做）

- ledger RQ-X-006：phase2 四处伤全部不挡路（0/64），"伤口设计失误本身成为数据"——fault menu 缺路径触达性前置检查。
- phase1p 附录 2×2（外壳 × 模型）已证明因子可分离：模型因子主导、外壳次之。但伤口维度从未被正交操作化。
- 台账 `path_relation` 枚举（blocks-path / redundant-backstop / future-use / weak-reference / unknown）正好是伤口设计的分类学；v1.1 补上 `on-path-no-gap` 后五类齐全。
- RQ-I-005 教训：关键词扫描分级有假阳性——逐发原文必须保存，分级回原文。

## 设计决策（Planner 已定；Executor 有异议走 PROMPT 硬停止条件 4）

1. **S0 先做 schema v1.1**（伤口分类法是实验卡词汇的直接依赖）：
   - `upstream` 枚举拆分：`kind: issue` → `open / closed-fixed / closed-stale / none`；`kind: pr` → `open / merged / closed-unmerged / none`；迁移 RQ-F-001 的 issue #1371 从 `merged` → `closed-fixed`。
   - `path_relation` 增加第五值 `on-path-no-gap`（文件在任务路径上被完整消费，但切口在完整句处、语义上无可见缺口）；迁移 RQ-F-006 从 `unknown` → `on-path-no-gap`。
   - SCHEMA 补 evidence 锚定声明：evidence 路径以实验机为锚，`runs/` 多为 gitignore，跨机克隆后校验可能失败。
   - SCHEMA/校验器/测试/数据四处同步改，`version` 升 `2`（文件骨架的 version 字段随 schema 演进升级）。
2. **物料按完整档构建，开火档位由 Owner 选**：
   - 最小档：W2+W4 两类伤口 × 4 宿主格 × N=8 + C0×8 = 72 发
   - 标准档：W1–W4 四类 × 4 × 8 + C0×8 = 136 发
   - 完整档：W1–W5 五类 × 4 × 8 + C0×8 = 168 发
   - 物料包按完整档构建（构建不花钱），驱动脚本支持 `--tier` 参数。
3. **靶子复用 `targets/greeting-agent`**：与 phase1 基线（22/64）同靶可比；phase0 探针已确认两宿主权重无 eve 记忆。
4. **预注册纪律**：rubric（L0–L3 沿用 SCHEMA 定义）、invalid rules、预算、停止条件全部在开火前冻结成文件；预注册后不得回改，修正走 adjudication。
5. **宿主可见树纪律**：guard/prompt/meta/逐发产物一律移出宿主可见树（X-005 教训）；staging 在 /tmp 纯哈希路径（X-003 教训）。
6. **因子矩阵结构**：伤口类（W1–W5）× 外壳（kimi CLI / codex CLI）× 模型（kimi-for-coding / k3-256k）；W1 blocks-path 为阳性对照，预注册预期方向：挡路伤高检出、不挡路伤低检出——若 W1 再跑出 0/N，按 invalid setup 处理而不是发表结论。

## Steps 与 DoD

### S0 schema v1.1
- 改 `ledger/SCHEMA.md`（枚举表、version 2、evidence 锚定声明）、`bin/ledger-check`（枚举校验同步）、`ledger/ledger.json`（两条迁移）、`tests/test_ledger_check.py`（新枚举用例）。
- DoD：`python3 bin/ledger-check ledger/ledger.json` exit 0；迁移后数据与新枚举一致；`bash tests/run_tests.sh` 全绿。

### S1 伤口设计 + 实验卡
- 产 `witness/factorial/cards/W1..W5.md`，每张卡：伤口类型与 `path_relation` 预期值及推演依据、**路径触达性前置检查**（任务路径是否必然读/执行该文件——X-006 教训）、切口规格（行数/百分比/切口边界）、预期检出方向、证人读数预期。
- DoD：5 张卡覆盖全部 5 个 `path_relation` 值；每张卡有触达性推演段落；W1 卡标注阳性对照身份。

### S2 变体生成器 + 物料树
- 产 `witness/factorial/gen_materials.sh`（或等效 python 脚本）：从健康靶子生成各伤口 mutated copy，哈希目录 staging，产出哈希登记文件。
- DoD：dry-run 生成完整物料树；哈希登记可复算；健康靶子的 skill-guard 基线读数记录在案（含已知假阳性 RQ-I-001 的校准声明）。

### S3 驱动脚本
- 产 `witness/factorial/run_factorial.sh`：支持 `--dry-run` 与 `--tier minimal|standard|full`；逐发产物（prompt/推理流/回复）存出宿主可见树；引用冻结的 rubric。
- DoD：`--dry-run` 全绿（物料树 + 哈希 + 卡片字段机检 + 证人基线）；脚本路径审计确认无任何宿主调用；脚本本身被 dry-run 测试覆盖并纳入 `tests/run_tests.sh`。

### S4 预注册包
- 产 `witness/factorial/prereg/RUBRIC.md`（L0–L3 定义引用 SCHEMA）、`prereg/INVALID-RULES.md`（污染判据沿用 X-003/X-005/X-007 + 新增：W1 检出 0/N 即 invalid）、`prereg/EXPERIMENT-CARD.md`（预算三档、停止条件、`phase: phase3` 约定、开火后结果落账 ledger 的字段映射——每 cell 一条 F 类条目还是按伤口合并 cells，按 SCHEMA 约定同伤口同条目）。
- DoD：预注册文件无 TODO 冻结；`bash tests/run_tests.sh` 全绿。

## 风险与回滚

- 伤口设计失误重演（X-006）→ 触达性前置检查 + 卡片强制推演 + W1 阳性对照作系统有效性检查。
- 靶子记忆污染 → 引用 phase0 探针记录；归因字段预留 `unable-to-separate`。
- 全部产物为新增文件 + S0 两处数据迁移，`git checkout` 可回滚；S0 迁移仅动 2 条 entry 的 2 个字段值。

## Out of Scope

- 不执行任何宿主运行（开火是 Owner 后续动作，届时按预算档位另行组织）。
- 不做漂移追踪（方向 3）、不做 dsh-eval-harness 自举（方向 4）。
- RQ-F-012/013 是否加目标活跃度 caveat 由 Owner 决定，不入本任务。

## 基础校验命令

```bash
cd /Users/boyang/repo-quake && python3 bin/ledger-check ledger/ledger.json && bash tests/run_tests.sh && bash witness/factorial/run_factorial.sh --dry-run
```
