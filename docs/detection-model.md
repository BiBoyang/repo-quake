# repo-quake 检测模型：评测失效的三因子统一解释（2026-10-30）

**结论：** 评测栈上"该发现而没发现"，都能还原成一个因子为零：没读到、读到不报、伤不挡路。读到与愿意报看宿主，挡路归设计者，且挡路一成立就把另两个因子逼到 1——所以哨兵靠得住，宿主的警觉靠不住。把 Witness 原则递归到评测栈自身：每层声明都要由层外的专门仪器出证，出证失败按三本账入台账。

术语沿用 `docs/eval-evidence-guide.md`（三本账、五字段）与 `ledger/SCHEMA.md`（挡路词汇、`path_relation`）；"检出"指分级 L2/L3。

## 1. 三因子模型

**检出 = 读到（reaches-the-eyes，外壳供给）× 愿意报（willing-to-report，模型供给）× 伤挡路（blocks-the-path，任务结构供给）**

公式见 README 与 `skills/repo-quake/SKILL.md`，源自 `docs/phase1p-report.md` 统一结论。三个因子都在实测里单独把检出打到零：kimi CLI 不读、kimi-for-coding 读到不报（E3，下表），伤不挡路（E1 0/16、R1/R2 0/16、phase2 0/64）。E3（render_card.ts 截到 12/20 行）2×2 全表（RQ-F-004）：

| 模型 \ 外壳 | kimi CLI | codex CLI |
|---|---|---|
| kimi-for-coding | 0/8（7/8 未打开 tools/*.ts） | 0/8（读完不报，L1×2） |
| k3-256k | 1/8（guard.json 残留污染，RQ-X-005） | 5/8 |

模型因子主导、外壳次之；推理档位未对齐（RQ-X-004），置信度只到 `likely`。三点精确化：

1. **乘号说的是可依赖的检出。** 任一因子为 0，检出要么归零（E1、R1/R2、phase2），要么沦为看宿主脸色（E3 四格 0/8～5/8）。
2. **挡路是另两个因子的开关。** 挡路时路径逼着读、残缺逼着说：同是 kimi-for-coding，挡路的 E2（kimi 外壳）8/8（RQ-F-003），不挡路且已读到的 E3 对照格（codex 外壳）0/8。不挡路时只剩宿主自愿的读到 × 愿意报；伤若无签名（完整句切口），连这条也断：R2 的残缺 rules.md 原样进了 system prompt（917→663 字符，字节级截获），宿主看不到不存在的段落（RQ-F-006）——读到文件 ≠ 读到伤。
3. **三因子只解释到 reported。** 五字段里 L1 = detected 未 reported，即愿意报为 0 的现场；contained 另成一链：E2 16/16 报告后照常产出残缺卡片（RQ-F-003）；e2e 缓存写失败 detected、contained 却未 reported（RQ-F-001）。

SKILL.md 要求每个因子被强制、被测量或作为混杂如实记录；第 3、4、5 节依次对应强制、记录、测量。

## 2. 用三因子重审已知评测失效

换成 verifier 或发布门当检测者，三因子照样成立。ABC 论文（*Establishing Best Practices for Building Rigorous Agentic Benchmarks*，arXiv:2507.02825，2025-07）的案例各落一个零因子：

| 案例 | 偏差 | 零因子 | 机制 |
|---|---|---|---|
| τ-bench：空回复通过"故意不可解"任务（airline 子集 38%） | 高估 | 伤挡路 | 什么都不做即满足判定 |
| SWE-Lancer：测试 ZIP 可列出、可覆盖，拿满分 | 高估（相对偏差 100%） | 伤挡路 | 门在被测者手里，改测试即绕路 |
| OSWorld：XPath 选择器失效 | 低估 28% | 读到 | 看不到真实页面状态，按"没找到"判错 |
| KernelBench：fuzz 不变 tensor shape | 高估 31% | 愿意报 | kernel 执行了，判据无区分力，形状相关的错全放行 |

（KernelBench 也可读作读到 0，对策相同。）推论：**零因子决定失明，默认值决定偏差方向**——缺证据时默认"过"就高估，默认"不过"就低估（OSWorld）。

ABC 按审计对象分类、三因子按供给方分类，类别层面对应（条目层面多对多）：Task Validity（T.1–T.10）审任务结构，守挡路；Outcome Validity（O.a–O.i）审判定，修 verifier 的读到与愿意报；Benchmark Reporting（R.1–R.13）管报告层自己的愿意报。深审 10 个 benchmark：7 个违反 task validity、7 个违反 outcome validity、10/10 有报告问题、80% 不承认自身弱点——末项正是报告者"看见了不说"。另：SWE-bench Verified top-50 中约 24% 不正确；ABC 修复自家 CVE-Bench，砍掉 33% 的绝对高估。

本仓库 phase1–2 是三因子的直接测量：

- blocking 8/8：E2 两宿主各 8/8（RQ-F-003），R3 8/8（RQ-F-007）。
- stealth 0/8：E1 两宿主各 0/8（RQ-F-002），R1、R2 各 0/8（RQ-F-005/006）。
- phase2 0/64：四处伤全不挡路（RQ-F-008～011；设计失误另记 RQ-X-006）。
- 按 `path_relation` 聚合台账 19 个 cell：blocks-path 24/24，其余四类 6/128，6 发全出自 E3 的两个 k3-256k 格——不挡路、伤带语法签名、外壳去读、模型肯报的窄路。

## 3. 哨兵 = 故障-阻断转换器

案例：某评测管线"未进评测环节自动打满分"——读到 1 × 愿意报 1 × 伤挡路 0 = 0。异常没藏起来，只是没有东西站在它和发布之间。本仓库靶点目录有同型先例：skill-up 从软链目录装了零个文件却记"skill installed"，零用例跑完报绿（`skills/repo-quake/references/target-catalog.md` 第 1、10 条）。

**证明。** 设管线故障 f 为 (1, 1, 0)。放入必不过哨兵 s（已知坏样本，"不过"的预期开跑前冻结），以"哨兵全部符合预期"作发布门：s 走真实候选的同一路径，f 作用于它（读到 1）；实际判定与冻结预期机械比对，无人裁量（愿意报 1）；不符即门关（挡路 1）。f 的检出由 0 变 1，且是确定性的：三个因子全由构造给出，不依赖任何人的警觉。同一推导给出哨兵的三种失效：

- **走旁路 → 读到 0。** 要做 presence verification：凭安装文件、加载日志证明干预进了被测系统，不凭退出码（同目录 `fault-catalog.md`）。
- **不符只打 warning → 挡路 0。** 哨兵沦为又一行没人读的日志；反制是计数为零一律硬错误，除非明示理由（target-catalog 第 10 条）。
- **只放一种 → 漏一个方向。** 必不过抓"默认过"（自动满分、τ-bench、SWE-Lancer、KernelBench），必过抓"默认不过"（OSWorld），所以成对放。各期 C0（必过）与 R3 式阳性对照（必不过，RQ-F-007）就是实验管线自己的一对哨兵。

台账 X 类的同类效度事件都是"早有规则、规则不挡路"，修法都是把规则接上路径：

- RQ-X-003：红线 7 早已成文，staging 根目录照样对宿主可见，4 发反推出实验性质。
- RQ-X-005：guard.json 回归进宿主可见树；教训"隔离规则要进校验器，不只进文档"就是转换器的定义。
- RQ-X-006：phase2 无本轮阳性对照，0/64 只能事后认定为设计失误；phase3 计划把"W1（blocks-path）检出 0/N 即 invalid"写进预注册（`plans/TASK-factorial-probes.md`）。
- RQ-X-009：夹具漏传 `{retryable}`，目标错误变成 `TypeError`；送达证明充当 harness 层哨兵，把假 finding 拦在 issue 之前（`invalid setup`，另开新卡）。

产品侧同理：RQ-F-001 的修复 PR 先证明新测试在 main 上失败（`docs/eval-evidence-guide.md`），把"测试照绿、报告缺字段"钉成 CI 上的必不过哨兵。

## 4. Witness 原则递归

repo-quake 第二定律：每份证据都要有自己的证人——故障要送达证明，检出要阳性对照，阴性结论要字节级证据，最惊人的结论复核前只是嫌疑（`skills/repo-quake/SKILL.md`、README）。递归到评测栈：每层声明都由**层外**的专门仪器出证；SWE-Lancer 的测试可被被测者改写，就是证据由被证者自产。

| 层 | 声明 | 证据（专门仪器） | 实例 |
|---|---|---|---|
| 题目 | 做不到就过不了 | 路径触达性前置检查；阳性对照 | RQ-X-006；phase3 W1 |
| verifier | 读到真实结果，判据有区分力 | 独立证人交叉读数（guard、严格 YAML 解析）；成对哨兵 | RQ-I-002/003/004（quick_validate 三盲区）；RQ-F-013 |
| harness（夹具与运行器，非宿主外壳） | 声明的故障已送达，隔离成立 | 送达证明；字节级截获；哈希 staging | RQ-X-009；RQ-F-006；RQ-X-003/005 |
| judge | 分级守冻结合同 | 逐发原文；初判保留、另写 adjudication | RQ-I-007（多要求 mode=missed）；RQ-I-005（关键词扫描假阳性） |
| 报告 | 数字有出处，局限已承认，公开状态已读回 | 台账 + `bin/ledger-check`；诚实清单；写后读回 | RQ-F-012（三处失效核成一处）；RQ-X-010 |
| 整栈 | 管线能得出对的结论 | 端到端 C0 + 阳性对照；能推翻解释的追加格 | RQ-F-007；RQ-F-004（同模型对照改写解释） |

证人本身也被测——skill-guard 对 pristine skill-creator 报 9 个 error（RQ-I-001），宽松解析放行了严格解析器拒绝的 frontmatter（RQ-I-006）；递归止于确定性、可复算、盲区已登记的仪器。

三本账是这张表的存储格式（`ledger/SCHEMA.md`）：题目与 harness 层出证失败落 RQ-X（夹具与效度），verifier 与 judge 层落 RQ-I（判分器含证人），被测目标行为落 RQ-F（产品）；报告层的证人是台账加校验器（当前 30 条、19 个 cell、97 条 evidence 路径逐条查存在）。归因明写"解释不是测量"、须带 confidence——第 5 节要拆的正是这个限制。

## 5. 防御面与进攻面

ABC 与 repo-quake 打同一组因子，站位相反：

| | ABC 检查表（审计时，静态清单） | repo-quake 注入器（运行时，动态仪器） |
|---|---|---|
| 产出 | 违规项（10 个中 7 违反 T、7 违反 O） | 每格检出率与归因（24/24 对 6/128） |
| 盲区 | 打勾 ≠ 运行时因子为 1：有校验器也放行空串（RQ-I-002） | 只测注入过的故障族；伤口设计会失误（RQ-X-006） |

两面互为输入：清单告诉注入器先打哪里，注入结果回流成清单条目——phase2 的 0/64 给 fault menu 补了路径触达性前置检查（RQ-X-006），零检出的考官矩阵催生了把完整性检查放进 CLI 层的上游提案（skill-up #280/#281，`skills/repo-quake/references/reporting.md`）。

phase3 正交探针按 `plans/TASK-factorial-probes.md` 设计，把三因子从解释变量变成可测变量：伤口按 `path_relation` 五类（W1–W5，W1 = blocks-path 阳性对照）操纵挡路，外壳（kimi CLI / codex CLI）操纵读到，模型（kimi-for-coding / k3-256k）操纵愿意报，正交交叉，输出边际检出率与交互效应；物料按 72 / 136 / 168 发三档构建，开火前冻结预注册，本轮零宿主调用。可证伪推论：W1 各格接近满检出、与外壳和模型无关；非挡路伤只在"外壳会读 × 模型肯报"的格里有检出；无签名的 `on-path-no-gap`（schema v1.1 新增）各格接近 0。任一推论被推翻，就轮到三因子模型自己进台账。
