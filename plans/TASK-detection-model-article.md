# TASK: repo-quake 方法论文章 docs/detection-model.md（三因子统一解释）

- 日期：2026-10-30
- 分工：Planner 起草（本契约），Executor 执行，Owner 确认与派发
- 状态：待 Owner 确认（对应 PROMPT 状态头 `pending`）
- 仓库：/Users/boyang/repo-quake（分支 `feat/flaw-ledger-schema`，台账工作已提交并推送）

## 目标

产出方法论文章 `docs/detection-model.md`，论证 `Detection = reaches-the-eyes × willing-to-report × blocks-the-path` 是评测失效的统一解释框架，并把 Witness 原则递归应用到评测栈自身。**单文件交付，零 git 命令，零测试要求。**

## 内容要求（五节）

1. **三因子模型**：检出 = 读到（外壳供给）× 愿意报（模型供给）× 伤挡路（任务结构供给）。出处：README 检测模型、phase1p 报告"统一结论"节、ledger RQ-F-004 的 2×2 全表。
2. **用三因子重审已知评测失效**：表格化——τ-bench 空回复过判（blocks-path 0）、SWE-Lancer 测试 ZIP 可覆盖拿满分（blocks-path 0）、OSWorld XPath 失效低估 28%（reaches-eyes 0）、KernelBench 弱 fuzz 高估 31%（willing-to-report 0）；ABC 论文的 T/O/R 三类检查项 = 三因子的工程对策；本仓库 phase1–2 实测数据（引 ledger id）作为因子的直接测量：blocking 8/8、stealth 0/8、phase2 0/64。
3. **哨兵 = 故障-阻断转换器**：必过/必不过哨兵把本来不挡路的故障变成挡住发布路径的故障——这是哨兵有效性的证明而非直觉。案例：某评测管线"未进评测环节自动打满分"（reaches-eyes 1 × willing-to-report 1 × blocks-path 0 = 0），以及台账 X 类条目中的同类效度事件。
4. **Witness 原则递归**：评测栈六层的"声明 → 证据"主表（题目 / verifier / harness / judge / 报告 / 整栈），证据由专门的仪器生产；台账（ledger）与 evidence-guide 三本账是该原则的数据落地。
5. **防御面与进攻面**：ABC 检查表（审计时点、静态清单）vs repo-quake 注入器（运行时点、动态仪器）；phase3 正交探针（plans/TASK-factorial-probes.md）把三因子从解释变量变成可测变量。

## 纪律

- 提炼重写，不搬运原文；每个关键论点带出处（ledger id / docs 文件 / arXiv 编号）。
- 术语与 `docs/eval-evidence-guide.md` 一致（三本账、五字段、挡路词汇），不另造平行词汇。
- 文风对齐 `docs/` 现有中文报告：结论前置、密度高、无客套。
- 长度参考 4–10KB。

## ABC 论文事实（已核实，直接引用，无需外网）

- 标题《Establishing Best Practices for Building Rigorous Agentic Benchmarks》，arXiv:2507.02825（2025-07，Daniel Kang 等）。三类检查：Task Validity（T.1–T.10）/ Outcome Validity（O.a–O.i）/ Benchmark Reporting（R.1–R.13）。
- 案例：τ-bench 空回复通过"故意不可解"任务（airline 子集 38%）；SWE-Lancer 测试 ZIP 可列出可覆盖、相对偏差 100%；KernelBench fuzz 不变 tensor shape、高估 31%；OSWorld 选择器失效低估 28%；SWE-bench Verified top-50 中约 24% 不正确。
- 汇总：深审 10 个 benchmark，7 违反 task validity、7 违反 outcome validity、10/10 有报告问题、80% 不承认自身弱点；ABC 修复自家 CVE-Bench 砍掉 33% 绝对高估。

## Steps 与 DoD

### S1 通读素材
ledger/ledger.json、docs/eval-evidence-guide.md、docs/phase1-report.md、docs/phase1p-report.md、docs/phase2-report.md、README.md、plans/TASK-factorial-probes.md。
- DoD：引用的每个数字都能指回素材原句。

### S2 写作 docs/detection-model.md
- DoD：五节齐全；关键论点带出处；案例数字与 ledger/报告一致（可用 `python3 bin/ledger-check ledger/ledger.json` 与直接读取核对）；单文件交付。

## 基础校验

纯文档任务。唯一机械检查：

```bash
cd /Users/boyang/repo-quake && git status --short
# 预期：仅新增 docs/detection-model.md（当前分支必须为 feat/flaw-ledger-schema）
```

## 风险与回滚

- 单文件新增，回滚即删；当前分支已推送，与 factorial 任务（另一 Executor）并行的隔离约束见 PROMPT（只碰本文件、零 git 命令）。
