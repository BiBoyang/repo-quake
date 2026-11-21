# REVIEW: TASK-detection-model-article（2026-10-30）

- Reviewer: Planner
- Executor: Opus 5.5（Owner 外部派发，与 T1 同仓库并行）
- 分支: 开工时 `feat/flaw-ledger-schema`（18:42 核对）；T1 后续切到 `feat/factorial-probes`，未跟踪文件随树携带，文件集零重叠
- 结论: **Approved**

## 审计表（证据制，逐项）

| 检查项 | 结果 | 证据 |
|---|---|---|
| 契约哈希复核 | Done | TASK `c00bfb01…` / PROMPT `ef38df04…` 与派发留痕一致 |
| 隔离约束 | Done | status step 0 记录开工分支核对通过；全程仅只读 git 命令；本任务增量仅 `docs/detection-model.md` + status 文件 |
| 交付物 | Done | `docs/detection-model.md` 10,956 字节，五节齐全（三因子模型 / 重审已知失效 / 哨兵=故障-阻断转换器 / Witness 递归 / 防御面与进攻面），结论前置，文风对齐 docs/ 现有报告 |
| 数字对账（Planner 独立复算） | Done | blocks-path 24/24 ✓、其余四类 6/128 ✓（总口径 30/152，与文章口径一致，含无逐发的 kimik3 格）；917→663 字节级截获、skill-up #280/#281（reporting.md:77）、target-catalog 第 1/10 条先例均命中原文件 |
| 出处纪律 | Done | 逐节带 ledger id / docs 文件 / arXiv:2507.02825；ABC 事实与契约嵌入原句一致；术语沿用 evidence-guide，无平行词汇 |
| 占位与时效 | Done | 第 5 节 on-path-no-gap 标注 "schema v1.1 新增"（与已 Approved 的 T1 迁移一致）；预注册引用为计划性措辞（Owner 中途已确认篇幅"保持现状"） |

## 超出契约的增值（Planner 认可并记录）

1. 三点模型精确化：乘号指"可依赖的检出"；挡路是另两因子的开关（E2 8/8 vs E3 对照格 0/8 的同模型对照）；三因子只解释到五字段的 reported 为止（contained 另成一链）。
2. 第 3 节给出哨兵的形式化证明：构造性地把 (1,1,0) 故障的三个因子全部置 1；并推导哨兵自身三种失效各落一个零因子。
3. 第 5 节以三条可证伪推论收尾——"任一推论被推翻，就轮到三因子模型自己进台账"，方法论反身应用。

## Findings

- 无 Blocker / Major。
- [Minor·已关闭] 篇幅 10,956 字节超参考上限约 7%：Executor 判定再压将损失有出处实质内容，Owner 中途批复"保持现状"，关闭。
- [Minor·待 Owner 裁量] 第 3 节匿名案例"未进评测环节自动打满分"：7 份指定素材无原句，Executor 以 target-catalog 第 1/10 条 + fault-catalog presence verification 作同型先例锚定（合理，未触发硬停止）。**Planner 注：真实出处是 Owner 本人在本会话叙述的亲历事故（已归档 Obsidian 笔记讨论 H）。**两选项：(a) 维持现状匿名锚定（适合公开文章）；(b) 补一句"作者本人观察到的真实事故"。归 Owner 决定，不影响验收。
- [备注·处理得当] KernelBench 双读法（愿意报 0 或读到 0）文中已并注，对策相同，符合"宁存疑不硬编"原则。

## 残余风险

- 若 T1 的 schema v1.1 迁移被回滚（当前已 Approved，风险极低），第 5 节 `on-path-no-gap` 一句需同步。

## 变更摘要

新增 `docs/detection-model.md`（10,956 字节）与 `prompts/TASK-detection-model-article.status.md`（6 行，含 Owner 中途批复记录）；草稿与核对脚本在仓库外 /tmp，未污染仓库。
