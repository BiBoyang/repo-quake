# repo-quake 缺陷台账（fault ledger）schema v1

台账文件：`ledger/ledger.json`。校验器：`bin/ledger-check`。

台账是 `docs/` 各期报告与 `docs/eval-evidence-guide.md` 的**结构化聚合层**：把散落在叙事里的
故障、仪器缺陷、实验效度事件各落成一条可校验的记录，让 x/N 数字可跨期累积、可比较、可追溯。
它不改写 `docs/` 原文，也不改写 `results/`、`runs/` 原始产物；每条记录都指回这些原始证据。

术语以 `docs/eval-evidence-guide.md` 为准：三本账（产品 / 夹具 / 判分器）、五字段观察
（detected / reported / contained / recovered / reverified）、挡路词汇
（Detection = reaches-the-eyes × willing-to-report × blocks-the-path）。台账不另造平行词汇。

## 文件骨架

```json
{"version": 1, "updated": "YYYY-MM-DD", "entries": [ ... ]}
```

- `version`：整数，当前为 `1`。
- `updated`：台账最近一次写入的日期。`upstream[].status` 等外部状态以该日期为准。
- `entries`：条目数组，按 `id` 追加，不重排。

## 三类条目（对齐"三本账"）

| `class` | 对应账本 | 收录什么 | id 前缀 |
|---|---|---|---|
| `target-finding` | 产品故障 | 预期故障已送达，目标产品行为违反合同；含各期每一格 fault cell 的宿主检出结果，以及实验中顺带发现的上游产品缺陷 | `RQ-F-` |
| `instrument-defect` | 判分器故障（含证人） | 证人、判分器、分级脚本、靶子自带校验器自身的缺陷：假阳性、盲区、合同之外的断言 | `RQ-I-` |
| `experiment-invalid` | 夹具故障与效度事件 | `invalid setup`、污染、隔离失误、变量未钉死、设计失误、发布链路的不确定提交；各期"诚实清单"全部入此类 | `RQ-X-` |

判定规则（按顺序问）：

1. 预期故障到底送达了没有？没送达（夹具构造错、参数漏传、路径泄漏、记忆污染无法分离）→ `experiment-invalid`。
2. 送达了，但异常结论来自证人 / grader 多加的条件或误读？→ `instrument-defect`，初判保留、另写 adjudication。
3. 送达了，证人在场，产品（或被测宿主）行为违反合同或未检出？→ `target-finding`。
4. 一个 finding 在完整产品和最小函数上各复现一次是两层证据，记**一条**，不记两条。
5. 阴性对照（C0）不是条目；它的无误报结果留在报告与 experiment card 里。
6. 同一期里不同宿主对同一处伤的结果，记在同一条目的 `cells` 里，不拆条目。

## 字段表（entry 顶层）

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `id` | string | 是 | `^RQ-[FIX]-\d{3}$`，字母与 `class` 对应，全局唯一，只增不改 |
| `created` | string | 是 | `YYYY-MM-DD`，条目**入账**日期（事件日期见 `phase` 与证据） |
| `phase` | string | 是 | `phase0` / `phase1` / `phase1p` / `phase2` / `e2e` / …；小写字母、数字、连字符 |
| `class` | string | 是 | `target-finding` / `instrument-defect` / `experiment-invalid` |
| `title` | string | 是 | 一行中文，含关键数字（x/N、行数、发次） |
| `status` | string | 是 | `open` / `reported` / `acknowledged` / `fixed` / `wontfix` / `superseded` / `n-a`；`experiment-invalid` 必须且只能用 `n-a` |
| `target` | object | F/I 类必填 | `{repo, artifact, version?}`，见下 |
| `fault` | object | F 类必填 | `{type, spec, delivery?, path_relation?}`，见下 |
| `cells` | array | 有宿主矩阵时必填 | `[{host, model?, runs, detected, levels?, notes?}]`，见下 |
| `attribution` | object | F 类必填 | `{primary_factor, explanation, confidence, caveats?}`，见下 |
| `observation` | object | 可选 | `{detected, reported?, contained?, recovered?, reverified?}`，全部 bool |
| `evidence` | array | 是，≥1 | 仓库根相对路径，校验器检查存在性 |
| `upstream` | array | 可选 | `[{kind, url, status}]`，见下 |
| `lesson` | string | 是 | 一行提炼，用自己的话，不抄报告原句 |

未列出的字段一律视为错误（防拼写错误）。需要新字段时先改本文件再改校验器，再改数据。

### `target`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `repo` | string | 是 | 上游仓库（`owner/name`）或本仓库内的靶子/工具路径（如 `targets/greeting-agent`、`BiBoyang/repo-quake`） |
| `artifact` | string | 是 | 被注入或出缺陷的具体文件、函数、字段 |
| `version` | string | 否 | 版本、commit、行数、分发变体等钉版信息 |

### `fault`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 是 | 故障类型，短横线小写词。已用：`truncation`、`missing-reference`、`thrown-error`、`stale-reference`、`invalid-yaml-frontmatter`、`false-positive`、`validator-blind-spot`、`grader-over-constraint` |
| `spec` | string | 是 | 切口位置、行数/百分比、丢失内容、证人读数等精确描述 |
| `delivery` | string | 否 | 送达证明：怎么进 staging、哪个证人、是否隔离 |
| `path_relation` | string | 否 | 伤与任务路径的关系，见枚举 |

### `cells[]`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `host` | string | 是 | 外壳：`kimi`、`codex` 等 |
| `model` | string | 否 | 模型：`kimi-for-coding`、`k3-256k` 等；报告未写明时省略 |
| `runs` | int > 0 | 是 | 该格发数 N |
| `detected` | int ≥ 0 | 是 | 检出数 x，`detected ≤ runs`；检出 = 分级 L2 或 L3 |
| `levels` | string | 否 | 逐发分级，逗号分隔，段数 = `runs`，每段 `L0`–`L3`；给出时 L2/L3 段数必须等于 `detected` |
| `notes` | string | 否 | 该格的注记：假阳性、幻觉、污染、来源缺口 |

分级含义（沿用各期报告）：`L0` 无信号；`L1` 推理流察觉但最终回复未报告或含糊；`L2` 明确向用户报告；`L3` 报告并阻断任务要求修复。

### `attribution`

归因是**解释不是测量**，所以必须带 `confidence`。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `primary_factor` | string | 是 | `blocks-path` / `reaches-eyes` / `willing-to-report` / `witness`，见枚举 |
| `explanation` | string | 是 | 哪个因子、为什么，用证据说话 |
| `confidence` | string | 是 | `confirmed` / `likely` / `unable-to-separate` |
| `caveats` | string 或 string[] | 否 | 保留意见：未钉死的变量、无法分离的污染、样本量 |

### `observation`

五字段观察，全部 bool，`detected` 必填其余可选；只记报告里有证据的字段，没测的不写。

### `upstream[]`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `kind` | string | 是 | `issue` / `pr` |
| `url` | string | 是 | `http(s)://` 完整链接 |
| `status` | string | 是 | `open` / `merged` / `closed-unmerged` / `none`，以 `updated` 日期的只读查询为准 |

对 `kind: issue`：`open` = 未关闭；`merged` = 关联修复已合入并关闭；`closed-unmerged` = 未经修复关闭。没有上游动作时省略整个 `upstream`，不写 `none` 占位。

## 枚举释义

`status`

| 值 | 含义 |
|---|---|
| `open` | 已记录，尚未向上游或负责人提出（含不打算单独上报的测量性 finding） |
| `reported` | 已提 issue / PR，等待处理 |
| `acknowledged` | 上游已确认 |
| `fixed` | 已修复并合入或独立验证 |
| `wontfix` | 上游或负责人决定不修 |
| `superseded` | 原判定被后续 adjudication 或后续条目取代，原始输出保留 |
| `n-a` | 不适用，仅 `experiment-invalid` 使用 |

`fault.path_relation`（对应 phase2 报告的"为什么不挡路"）

| 值 | 含义 |
|---|---|
| `blocks-path` | 任务必经路径必然读到或执行到伤口，残缺产生可见异常 |
| `redundant-backstop` | 伤口在路径上，但同一信息有冗余来源兜底（目录/脚本/正文自描述、幸存的引用） |
| `future-use` | 伤口所在内容在本次任务路径之外：下次会话才需要，或只在未触发的条件分支里需要 |
| `weak-reference` | 伤口位于"详见 X"式弱引用的目标文件，宿主无需打开即可完成任务 |
| `unknown` | 未判定，或不属于以上任一类（原因写进 `attribution.explanation`） |

`attribution.primary_factor`

| 值 | 含义 |
|---|---|
| `blocks-path` | 结果主要由"伤是否挡路"解释 |
| `reaches-eyes` | 结果主要由"宿主有没有读到那个文件"解释（外壳供给） |
| `willing-to-report` | 结果主要由"读到后愿不愿意报 / 产品检测到后有没有报告"解释（模型或产品供给） |
| `witness` | 结果主要来自独立证人（机械证人、严格解析器、人工核对），而非宿主检出 |

`attribution.confidence`：`confirmed` 证据直接支持；`likely` 方向可信、强度待复核；`unable-to-separate` 存在无法分离的替代解释（如记忆代偿），如实标注。

## 约定

- `id` 只增不改；条目作废用 `status: superseded` 并保留原文。
- `evidence` 写仓库根相对路径，优先指向已入库的原始产物（`runs/*/grades.json`、`results/*.json`、deviation log）和报告；至少一条。
- `title` 与 `cells` 里的数字必须能在证据里找到原句；抽查方式是"报告数字 ↔ 台账数字"。
- 宁缺勿编：信息不足就省略可选字段，不猜。
- 跨期汇总示例：`python3 -c 'import json;d=json.load(open("ledger/ledger.json"));print(sum(c["detected"] for e in d["entries"] for c in e.get("cells",[])),"/",sum(c["runs"] for e in d["entries"] for c in e.get("cells",[])))'`

## 校验器

```bash
python3 bin/ledger-check ledger/ledger.json          # 证据路径相对 ledger/ 的上一级（仓库根）
python3 bin/ledger-check path/to/copy.json --root .  # 显式指定仓库根
```

检查项：JSON 合法；骨架字段；每条必填字段与类型；未知字段；`id` 格式、字母与 `class` 一致、全局唯一；
各枚举合法；`experiment-invalid` ⇔ `status: n-a`；F/I 类带 `target`，F 类带 `fault` 与 `attribution`；
`cells` 的 `runs > 0`、`0 ≤ detected ≤ runs`、`levels` 段数 = `runs` 且 L2/L3 段数 = `detected`；
`evidence` 非空且每条路径存在；`upstream` 的 `kind`/`status` 枚举与 `http(s)://` 链接。
退出码：`0` 通过，`1` 校验失败（逐条可读错误），`2` 用法或文件读取错误。

## 示例一：`target-finding`（e2e 缓存写入合同，tester-army/e2e#1371 / #1372）

```json
{
  "id": "RQ-F-001",
  "created": "2026-10-30",
  "phase": "e2e",
  "class": "target-finding",
  "title": "e2e@0.21.3 缓存 store.write 抛错后 step.cache.write 结果丢失，未按 CacheWrite 合同给出 not-written",
  "status": "fixed",
  "target": {
    "repo": "tester-army/e2e",
    "artifact": "packages/e2e/src/cache/context.ts settleStagedTraces → report step.cache.write",
    "version": "e2e@0.21.3（npm 锁定）；main 69e123b1 源码核对"
  },
  "fault": {
    "type": "thrown-error",
    "spec": "T1：自定义 store 的 write 抛出 EACCES；对照 C0 返回 {bytes:128} → saved，C1 返回 undefined → not-written，T1 实际 null",
    "delivery": "直接调用 settleStagedTraces 的内存 store 探针，每格 1 次，store 调用日志记录 read→write；完整 runner + 自定义 store（semantic-commit F1）独立交叉",
    "path_relation": "blocks-path"
  },
  "attribution": {
    "primary_factor": "willing-to-report",
    "explanation": "异常被 catch 住（detected）且无重复副作用（contained），但 settlement 没有把 not-written 写回结果：缺的是报告通道，不是检测通道；路径必达，证人在场",
    "confidence": "confirmed",
    "caveats": [
      "每格 1 次确定性调用，不是统计样本",
      "main 只做源码核对，未构建执行；运行时结论限于 npm 0.21.3"
    ]
  },
  "observation": {"detected": true, "reported": false, "contained": true, "reverified": true},
  "evidence": [
    "runs/e2e-cache-write-contract-2026-10-25/report.md",
    "runs/e2e-cache-write-contract-2026-10-25/results/matrix.json",
    "runs/e2e-cache-write-contract-2026-10-25/disclosure.md",
    "runs/e2e-cache-write-contract-2026-10-25/upstream-repro/actual-output.txt",
    "runs/e2e-cache-write-contract-2026-10-25/pr-evidence/verification-summary.md",
    "runs/e2e-cache-write-contract-2026-10-25/pr-evidence/pr-status.md",
    "runs/e2e-semantic-commit-2026-10-25/report.md",
    "docs/eval-evidence-guide.md"
  ],
  "upstream": [
    {"kind": "issue", "url": "https://github.com/tester-army/e2e/issues/1371", "status": "merged"},
    {"kind": "pr", "url": "https://github.com/tester-army/e2e/pull/1372", "status": "merged"}
  ],
  "lesson": "业务成功、异常被吞、报告缺字段是三件事：正常返回、哨兵值、抛出各走一条路径分别验证，缺字段先查合同再定性"
}
```

## 示例二：`instrument-defect`（phase2 skill-guard 假阳性）

```json
{
  "id": "RQ-I-001",
  "created": "2026-10-30",
  "phase": "phase2",
  "class": "instrument-defect",
  "title": "skill-guard 无法区分真实引用与正文示例中的假想引用，pristine skill-creator 被判 9 个 error，真伤被淹没",
  "status": "open",
  "target": {"repo": "BiBoyang/repo-quake", "artifact": "bin/skill-guard"},
  "fault": {
    "type": "false-positive",
    "spec": "正文示例（references/schema.md、assets/font.ttf 等）被当作真实引用：健康态 FAIL 9 err，F1 9 err + 3 warn，F2 10 err（真伤是第 10 个），F4 11 err；对该靶子只能做与基线的 diff。2026-10-15 加入 strip_fences 跳过围栏内示例后，2026-10-30 对 vendor/skill-creator 仍复现 9 error（行内与表格示例未覆盖）"
  },
  "evidence": ["docs/phase2-notes.md", "docs/phase2-report.md", "bin/skill-guard", "vendor/skill-creator/SKILL.md"],
  "lesson": "证人也需要校准：有假阳性的证人只能做基线 diff，而且真伤会被淹没；示例识别要覆盖行内与表格，不只围栏"
}
```
