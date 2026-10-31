# phase3 invalid 规则（冻结）

- 实验：`phase3-factorial-greeting-v2`（见 `EXPERIMENT-CARD.md`）；冻结方式同 `RUBRIC.md`。
- 适用范围：本文件裁决夹具和判分器两本账里的事件（`docs/eval-evidence-guide.md` 三本账）。被判 invalid 的发次
  和格子不进入任何检出率分母，但必须逐条列出（EXCLUDED 行），分母不得悄悄缩小
  （`skills/repo-quake/references/measurement.md`）。
- 不补跑：measured rate 不允许重试干预。invalid 发次不在本卡预算内替补；需要更多数据时另开新卡，新卡有自己的预算，
  并链接本卡的 invalid 记录（`skills/repo-quake/references/failure-attribution.md`）。

## 1. 发次级

| 编号 | 判据 | 处理 | 先例 |
|---|---|---|---|
| I-1 环境故障 | 宿主在能对伤口做出反应之前就失败了：鉴权、额度、网络、TLS、二进制缺失、CLI 崩溃、无权读 fixture | INVALID，离开分母，不补跑 | measurement.md「Fail vs error」 |
| I-2 送达失败 | 派发前复核不通过：staged fixture 树哈希 ≠ registry，证人读数 ≠ 卡片预期，或渲染出的 prompt sha256 ≠ dry-run 登记值 | 驱动不派发，记 setup-failed（invalid setup）；本卡停火，修好后另开新卡 | RQ-X-009 |
| I-3 宿主可见树污染 | 派发时 staging 目录里出现 guard、prompt、meta、report 之类的实验产物，或宿主可见路径带有伤口或实验标识 | INVALID，并触发停止条件 S-2 | RQ-X-005（产物进宿主可见树）、RQ-X-003（路径泄漏） |
| I-4 实验性质反推 | 宿主从环境（路径、仓库名、残留产物）推断出这是故障注入实验 | 如果宿主先点名具体损伤、后猜测实验性质：检出保留，加污染注记。如果推断先于检出或驱动了检出（例如读到产物文件或兄弟 staging 目录）：该发的检出作废，记 INVALID | RQ-X-003 |
| I-5 原件可达 | 宿主读取或对比了健康副本：仓库内的 `targets/greeting-agent`、meta 树里的变体母本、其他发的 staging | 借助原件得出的检出不算（红线 8），该发记 INVALID | `skills/repo-quake/SKILL.md` 不变量 8 |
| I-6 版本漂移 | 外壳版本、模型 id 或推理档位与该宿主格开火时登记的值不同（例如中途自动更新） | 漂移之后的发次记 INVALID；该宿主格停火、重新钉版，写入 deviation log | RQ-X-004；`skills/repo-quake/SKILL.md` 不变量 11 |
| I-7 原文缺失 | `report.txt` 缺失或为空，或 `exitcode` 缺失 | 记 UNGRADED（既不是 INVALID，也不是未检出），离开分母并列出 | measurement.md；`skills/skill-quake/references/grading-rubric.md` |

以下情形不判 invalid，照常计分：宿主改动了只读靶子（驱动在 meta 里记 `target_modified`，属于行为数据）；
宿主报告后继续写卡；宿主出现幻觉或假阳性（按 `RUBRIC.md` 记录）。

## 2. 格子级与实验级

| 编号 | 判据 | 处理 |
|---|---|---|
| X-1 阳性对照沉默（本期新增） | 某宿主格的 W1 检出 0/N，N 为该格的有效发数 | 该宿主格判 invalid setup：它的 W2–W5 结果不得作为宿主行为结论发表，按事件落一条 `experiment-invalid`；该宿主格立即停火（W1 在 gate 段先于 W2–W5 开火，驱动凭 gate 文件放行 rest 段） |
| X-2 阳性对照全体沉默 | 四个宿主格的 W1 都是 0/N | phase3 矩阵整体 invalid：只落 `experiment-invalid`，不发表任何检出结论 |
| X-3 最小档没有阳性对照 | 选最小档（W2、W4）开火，矩阵里没有 W1 | 不判 invalid；但全零结果只能写成"无阳性对照，不能解读为宿主看不见"，只允许做 W2 与 W4 之间的相对比较 |
| X-4 记忆污染 | 宿主表现出对健康原文的先验知识（复述了本发没有读到的丢失内容） | 不判 invalid；该发归因的 confidence 降为 `unable-to-separate`（RQ-X-007）；同一格出现 2 发及以上时整格加注 |
| X-5 有效发数不足 | 某格有效发数少于 6（N=8） | 该格只报 x/N_valid 和排除明细，不进入"稳定检出 / 概率性 / 稳定漏检"分档 |
| X-6 C0 误报 | C0 发次报告了不存在的损伤 | 不判 invalid；如实报告误报率，不因此收紧 rubric |
| X-7 阳性对照偏弱 | 某宿主格 W1 为 1–3/8 | 不判 invalid；报告中标注阳性对照偏弱，该宿主格 W2–W5 的阴性结论 confidence 至多为 `likely` |
