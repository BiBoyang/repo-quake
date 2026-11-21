# repo-quake Phase 4 报告：回答断在一半、自动重发之后，屏幕和对话还一致吗（2026-11-14 → 11-16）

问题：模型的流式回答断在中途，CLI 自动重发之后，**屏幕上（或 stdout 里）显示的，和 CLI 存下来、下一轮要发给模型的对话，是否一致？**

被测：Claude Code 2.1.282、codex-cli 0.169.0、Kimi Code 2.5.3，交互（TUI）和非交互（`claude -p`、`codex exec`、`kimi -p`）两种模式。Kimi Code 的结果都是在 2.5.3 上测得的；2.6.0 已经发布，没有复测。全部只连本机回环地址上的 mock，没有调用任何付费模型。

数据来自三轮，另有一批探索性补跑，下文都用这些名字：
- **主矩阵（11-14）**：三个工具 × 两种模式 × 六种条件，每格 3 次，由另一个 agent 执行。
- **续写对照（11-15）**：只测 Kimi Code，把 mock 改成"会接着半截往下写"。
- **补测（11-15）**：只测 Claude Code 和 codex 的交互模式，用修好的装置 `witness/stream-retry/` 重跑，每格 3 次，共 36 次。
- **探索性补跑（11-16）**：只测 codex 交互，正式回答的每次请求都断（F1-always、F6-always 各 3 次，前后 F0 对照各 3 次），用补测的装置，没有预注册，见发现二末尾。

做补测的原因：11-15 的一次独立复验推翻了主矩阵对这两个工具的结论（见"更正"一节）。

## 头条结果（更正后）

| 工具 | 模式 | F1 断一次 | F6 断一次 | FLONG 断一次 | F1 每次都断 |
|---|---|---|---|---|---|
| Claude Code 2.1.282 | 交互 | retracted 3/3（补测） | retracted 3/3（补测） | retracted 3/3（补测） | 作废（旧 mock，见更正） |
| Claude Code 2.1.282 | `-p` | not shown 3/3 | not shown 3/3 | not shown 3/3 | reported failure 3/3 |
| codex 0.169.0 | 交互 | retracted 3/3（补测）¹ | retracted 3/3（补测）¹ | retracted 3/3（补测）¹ | reported failure 3/3¹ |
| codex 0.169.0 | `exec` | not shown 3/3 | not shown 3/3 | not shown 3/3 | reported failure 3/3 |
| Kimi Code 2.5.3 | 交互 | 重发带回半截 3/3² | **accepted partial 3/3** | 重发带回半截 3/3² | reported failure 3/3 |
| Kimi Code 2.5.3 | `-p` | 重发带回半截 3/3² | **accepted partial 3/3**（退出码 0） | 重发带回半截 3/3² | reported failure 3/3 |

这一期第一次用到的三种故障：
- **F1**：流到一半，TCP 连接正常关闭（FIN），没有任何结束信号；
- **F6**：只发一半内容，HTTP 正文却完整结束（分块编码的结束块照常发出），但没有任何结束事件、停止原因或 `[DONE]`；
- **FLONG**：先流出 160 段，超过一屏，再断开。

除 F1 每次都断外，每种故障都只打在正式回答的第一次请求上，之后的请求都正常。

表里的标签只是判分笔记，台账只记五个观察字段（`ledger/SCHEMA.md`）。对照 `fault-catalog.md` 的表：
- **not shown**：半截从没显示过，重发后只有一份完整回答；
- **retracted**：半截显示过、随后消失，重发不带半截，最后只剩一份完整回答；
- **accepted partial**：不重发、不提示，把半截当成完整回答；
- **reported failure**：恢复不了，但把错误告诉了用户。

¹ codex 在重发过程中，会把失败的半截和从头重写的新回答同时留在屏上，重发完成时才收成一份；重试次数用完时，几次尝试的半截首尾相接、一直留在最终画面上（11-16 探索性补跑 6/6）。见发现二；两点都已补到上游 [openai/codex#47538](https://github.com/openai/codex/issues/47538)。

² Kimi Code 重发时会把半截带回去。最终显示取决于服务端怎么处理：
- 服务端从头重写：屏上半截和完整回答各一份（主矩阵，12/12）；
- 服务端接着写：屏上恰好一份（续写对照，12/12）。

真实接口属于哪一种，这一期没有测。所以这一条是待验证的观察，不是已确认的缺陷（见"待验证的观察"一节）。

前后两轮 F0 对照：主矩阵 6 组都一致；补测 Claude Code 和 codex 的 F0-pre、F0-post 各 3/3 healthy。补测还多了一格阳性对照 F0-tag：回答本身是健康的，只是前 12 段带有失败标记。两个工具都是 3/3：标记确实能穿过各自的渲染器显示到屏上。所以"屏上没看到标记"可以当成"没显示半截"。

## 两个发现和一个待验证的观察

### 发现一：Kimi Code 遇到没有停止原因的流，当成正常结束（F6），已提上游 issue

已提 issue：[MoonshotAI/kimi-code#4964](https://github.com/MoonshotAI/kimi-code/issues/4964)（2026-11-15）。以下结果都是在 Kimi Code 2.5.3 上测得的；2.6.0 已经发布，没有复测，issue 里也写明了这一点。

F6 下，Kimi Code 在交互和 `-p` 两种模式里都是 3/3 只发了 1 个请求：
- 屏上只有 P01 到 P12，没有任何提示；
- `-p` 的退出码是 0；
- 会话里记着 `"finishReason":"end_turn"` 和 `turn.ended` 的 `"reason":"completed"`。

流从头到尾没有给出任何停止原因，所以这个 `end_turn` 是客户端自己补出来的。补出来的停止原因，同时绕过了截断触发的恢复路径：
- 半截没有重发；
- 半截还作为完整的 assistant 消息，进了后面每一轮的上下文。

issue 里的最小复现（单文件 Python mock 加一份配置）在干净环境里跑通过。

同一个 F6，另外两个工具都识别为断流并重发：
- codex 给出 "Stream disconnected before completion: stream closed before response.completed"；
- Claude Code 给出 "Connection closed before the response finished · Retrying in 1s · attempt 1/1"。

相邻的 #4012 讲的是带了 `finish_reason: "length"`、却仍按成功结束的情形，覆盖不了"根本没有停止原因"。

### 待验证的观察：Kimi Code 重发时把半截带回去，但没带 `partial` 标记

**这一条不是已确认的缺陷，也没有报上游。**客户端这边的行为测到了，后果却取决于没测过的真实服务端。结果同样来自 Kimi Code 2.5.3，2.6.0 没有复测。

F1 和 FLONG 下，两种模式加起来 12/12：Kimi Code 重发时，都把半截作为最后一条 role=assistant 的消息带回去。这条消息只有 role 和 content 两个字段，没有 `partial`。

Kimi 平台的 Partial Mode 文档写的是：要让模型从给定文本接着写，最后那条 assistant 消息必须带 `partial=True`，返回的只是续写部分。不带这个标记时服务端会怎么做，文档没写。所以最终结果取决于一个没有写进文档的服务端行为：
- **服务端从头重写：**屏上半截紧跟着一份完整回答，下一轮的上下文里也是两份。这是主矩阵的 mock，12/12，原来记作 `ghost`，这里改记为"重写分支：duplicate"。
- **服务端接着写：**屏上 P01–P24（或 L001–L200）每段恰好一次，会话里是拆成两段的一份完整回答。这是续写对照的 mock，12/12。

真实接口属于哪一支，要调用真实接口才能知道，这一期按约束没有做。在验证之前，只能说这一条"可能"让屏上和对话都重复。五字段里能确定的只有 detected ✓、recovered ✓；contained 取决于服务端，不记。

附带一个旁证。归档版 kimi-cli 1.52.0（11-14 试测，N=1）：
- 重发请求和第一次完全相同（都是 49,096 字节），不带半截；
- `context.jsonl` 里只有一份完整回答；
- stdout 却是 P01–P12 后面紧接着 P01–P24。

这是一个 fork：屏上留着半截，对话里没有。N=1，只证明它存在过。

### 发现二：Claude Code 和 codex 最终都只剩一份完整回答，但过程不同（补测）

补测的 18 次故障运行全部判为 retracted，每格 3/3。每一次都满足这四条：
- 半截确实显示过：屏上第一次出现失败标记时，就截下了中途截图；而且原始字节里也有这个标记；
- 最终画面完整：窗口 110×400，横幅和本次提示词都在最终画面上；
- 最终画面上，完整回答的每一段恰好出现一次；
- 重发请求、下一轮请求、会话文件里，都没有失败的半截。

两个工具收掉半截的方式不一样（时间都由同一个时钟记录，毫秒）：

| | Claude Code 2.1.282 | codex 0.169.0 |
|---|---|---|
| 半截在屏上停留 | F1、F6：138–188 ms；FLONG：约 24.2 s（边流边显示） | F1、F6：1,035–1,116 ms；FLONG：约 55.5 s |
| 半截何时消失 | 连接断开后 7–76 ms，在重发开始之前 | 重发流结束时（F1、F6 在重发结束前后 26 ms 内；FLONG 早约 0.25 s） |
| 重发期间 | 屏上只有新回答 | **失败的半截和从头重写的新回答同时在屏上**：在同一个消息块里，新回答的 P01、P02…紧跟在旧的 P12 下面往下流；重叠截图截到了全部 12（或 160）段带标记的半截，加上第二份 P01（或 L001）。FLONG 要这样持续约 31 秒 |
| 提示（原始字节，相对断开时刻） | F1、FLONG：`API error · Retrying in 1s · attempt 1/10`（+5 至 +36 ms）；F6：`Connection closed before the response finished · Retrying in 1s · attempt 1/1`（+5 至 +17 ms） | `Reconnecting... 1/5` 和 `Stream disconnected before completion: …`（F1、FLONG 是 `Transport error: network error: error decoding response body`，F6 是 `stream closed before response.completed`），+4 至 +49 ms |
| 提示在屏上停留（逐次截屏） | 478–635 ms | 215–387 ms |
| 提示留在最终画面上 | 否，0/9 | 否，0/9 |
| 断开到重发 | 0.53–0.62 s（提示写的是 "in 1s"） | 0.19–0.23 s |

非交互模式下（主矩阵，18/18），半截从没打印到 stdout，stdout 恰好一份完整回答：输出是等完整回答才写出的。两个工具在这里的差别是提示：
- codex `exec` 每次都在 stderr 写 `ERROR: Reconnecting... 1/5`（9/9）；
- Claude Code `-p` 不给任何提示（stdout 和 stderr 都没有，9/9），退出码 0。用户不会知道中间断过一次。

**重试次数用完时（codex，11-16 探索性补跑，没有预注册）。**补测只测了"断一次"。主矩阵里 codex 交互 F1-always 的最终画面上有两份以上的 P01–P12，但那是 35 行窗口，数不清总份数。为了在补充上游证据之前测准，11-16 用补测的装置对 codex 0.169.0 另跑了 F1-always、F6-always 各 3 次，前后 F0 对照 healthy 6/6：
- codex 一共发 6 次正式请求（第一次，加上 `Reconnecting... 1/5` 到 `5/5`），每次的 P01–P12 都接在同一条消息后面。报错 `■ stream disconnected before completion: …` 之后也不收，最终画面上 6 份首尾相接，6/6；
- 会话文件里这一轮没有 assistant 记录（0 条），下一轮不会带上它。错的只是显示，但会一直留在屏上；
- 原因在源码里（rust-v0.169.0）：收到"要重试"的错误时，TUI 只改状态栏，不清掉已经流出的文字，重发的片段接着往后追加。重发成功时以完成的消息为准，收成一份；失败收尾时没有完成的消息可依，拼接的流就原样留下。这段代码在今天的 main 上没变。

上游：[openai/codex#47538](https://github.com/openai/codex/issues/47538)（9-23 开）就是这个问题。原帖在 0.156.1 上只看了重发完成后的画面，没复现出来。codex 的贡献规则不收外部 PR，要求已有 issue 就把新信息补在原帖下，所以没有新开 issue，而是 11-16 在原帖下补了两种情况的数据、源码位置和最小复现（[评论](https://github.com/openai/codex/issues/47538#issuecomment-6905066983)，读回逐字一致）。最小复现对 0.169.0 实测过：只断一次时，两份同屏约 6 秒后收成一份；每次都断时，每重发一次多一份，最后 6 份留在屏上。证据：`runs/phase4-codex-retries-exhausted-2026-11-16/`。

## 更正：哪些数字改了、为什么

这些更正来自 11-15 的独立复验（一个只读的子 agent），以及本期补测。主矩阵的原始汇总保留不动，这里只列改了什么。

1. **Claude Code、codex 非交互，F1、F6、FLONG（18 次）。**原来判 retracted 3/3 × 6 格，现在改成 **not shown 18/18**。原来的"中途截图"是用【P01】触发的，而重发的回答也有【P01】，所以截到的是重发的内容。半截其实从没打印过：stdout 是只追加的，如果打印过，P01–P12 会出现两次，或者会有 L 编号。实际一次都没有。
2. **Claude Code、codex 交互，F1、F6、FLONG（18 次）。**原来判 retracted 3/3 × 6 格，但主矩阵的证据只撑得住其中 3 次（Claude Code 的 FLONG）。原因有四个：
   - 中途截图由两次尝试都会输出的编号触发：Claude Code 有 6 张截图是在重发开始之后才截的，其中 5 张已经能看到 P13 以后的段落；
   - codex 的 9 张截图，那 35 行从 P01 开始，提示词已经滚出屏幕，排除不了屏幕上方还留着半截；
   - 两个工具都开着备用屏幕，tmux 抓到的"整段历史"和当前那 35 行逐字节相同；
   - 重新判分的脚本把最终画面当成中途画面传了进去，"中途看到过半截"这一条从来没有真正检查过。

   **补测结果是 retracted 18/18**，而且补上了过程差异（发现二）。结论方向没变，但现在每一次都有证据。
3. **Kimi Code，F1、FLONG（12 次）。**原来判 `ghost` 3/3 × 4 格。现在改记为"重发带回半截 12/12；重写分支 duplicate 12/12，续写分支 continued 12/12"。原来那个"重复"，有一部分是 mock 只会从头重写造成的；这一条现在写成待验证的观察（见上文）。
4. **Claude Code 交互，F1 每次都断。**原来判 n/a 3/3，汇总里还写着"非流式也断开"。现在**作废**。这一格跑在旧 mock 上：Claude Code 流式重试用完、改发非流式请求时，旧 mock 给了完整回答，界面上显示并存下了 P01–P24。另外，它的第 1 次落在端口冲突的时间窗里（08:35:39Z），也没有筛掉。
5. **提示。**原来汇总写"Claude Code 交互：无提示"，这是错的。重试提示只停留 0.48–0.64 秒，最终画面上看不到，但原始字节里有。补测 9/9 次都有，原话见上表。主矩阵里 codex 交互的中途截图也拍到了 "Stream disconnected"。Kimi Code 的提示是 "Retrying (2/10) · APIConnectionError"。
6. **FLONG"断开前一刻"。**原来那张表是在 35 行窗口里截的：Claude Code 是 30/30，codex 是 27/27，最终 0/0。它说明不了屏幕以外有什么：Claude Code 唯一的那个 `ESC[2J` 是启动时清屏用的。补测用 400 行窗口，6/6 次断开前截图里，150 段、横幅和提示词同时在屏上，最终 L001–L200 恰好一次。备用屏幕开启的位置，Claude Code 在第 593 字节，codex 在第 69 字节，和复验一致。
7. **哈希。**
   - 主矩阵记的 codex sha256 是 npm 启动壳 `codex.js` 的。补测改为记它实际执行的原生二进制 `739cda86…`，每次运行都用 `lsof` 核对，18/18 一致；
   - 主矩阵没记 mock 的哈希，前后还用过两个版本（`a207fda8…`、`4482f1d9…`）。补测冻结的 mock 是 `e7fef77a…`。
8. **实验卡和偏离。**主矩阵的卡写的 `max_runs` 是 108，实际跑了约 210 次，偏离日志里也没有记。另外，FLONG 补跑那一轮（10:05–10:10Z）之后，没有再跑 F0。补测的卡写的 `max_runs` 是 48，实际 36 次，没有补跑。冻结前的 17 次试跑单独列出，不计入。
9. **"每次都断"要多久。**以下是 N=1 的观察，次数按正式请求计，交互模式下另有一个生成标题的请求。
   - Claude Code：先流式重试 11 次，再非流式重试 11 次，最后一个请求分别在第 370 秒和第 355 秒；
   - codex：6 次，约 9 秒；
   - Kimi Code：10 次，约 148 秒。

   两次尝试之间，最长隔了 33–40 秒。原来"30 秒没有新请求就判为不重发"的静默窗口太短，补测改为 60 秒，下限 40 秒。

## 装置：这次怎么看见的

装置在 `witness/stream-retry/`。复验返工清单 12 条、各自改在哪里，见它的 `README.md`。要点：

- **失败标记。**失败那一次的每个段落末尾，都追加一个只有它才有的标记（形如 `〔x1a2b3c〕`）。中途截图由它触发，每 30 ms 截一次屏，截下的时刻和 mock 送达日志用同一个时钟。原始字节由 `pipe-pane` 接到 `rawtap.py`，每一块都记下收到的时刻，所以标记、提示第一次到达终端的时刻也能对上。
- **窗口和完整性。**tmux 窗口开到 110×400，整段对话都留在备用屏幕上。最终画面要横幅和本次提示词都在，才算完整；不完整就只能判 n/a。
- **对照要验证，不能默认。**健康对照要逐项检查，不满足判 `control_failed`。这一条在冻结前就起了作用：试跑时 codex 的 F0 被判失败，查下来是新 mock 的毛病。codex 收到 `response.completed` 就挂断，mock 把这记成了"客户端中途断开"。修好之后才冻结。
- **对抗测试。**"服务端重写、客户端藏起半截"不能判成 continued；"FLONG 最终只剩 L161–L200"也不能判成 continued。都有测试覆盖。另有一个假 TUI，有收回、保留、渲染两遍三种模式，端到端校准整条证人链。对判分规则做了五处变异检查，每处都有测试能抓到。
- **隔离。**`env -i` 白名单，每次运行一个新的临时 HOME，`sandbox-exec` 只放行 localhost 出站，tmux 用独立的服务器。Claude Code 关掉了 deep link 注册（`disableDeepLinkRegistration`）。

## 诚实清单

- **冻结前试跑过 17 次**（Claude Code 8 次，codex 9 次，每格 1–2 次）。用的是中间版本的装置，用来校准窗口高度、截图间隔和 mock。卡里的结论参考了试跑。试跑中的故障格全部判 retracted，和正式结果一致；它们不计入 x/N，证据留在本地。
- **测试和矩阵同时跑过。**正式矩阵运行期间（15:06–15:17Z），本机运行过多次 `tests/test_stream_retry.py`，其中包括一个假 TUI 的端到端测试。它用自己的 mock、端口和 tmux 服务器，和矩阵互不相通，但会争用 CPU，毫秒级的时间数字可能因此略有偏移。判定不依赖这些时间，时间只作为另外的观察记录。
- **tmux 不是真终端。**渲染节奏可能和 iTerm2、Terminal.app 不同。codex 的"重叠"在真终端里会持续多久，没有测。
- **沙箱下工具处于离线状态。**codex 在 `check_for_update_on_startup=false` 下，每次启动仍会做大约 3 次域名解析：矩阵期间共 60 次，全部被沙箱拦下，去向不明。Claude Code 0 次。这些都不影响 mock 连接，但联网时客户端的行为可能不同。
- **11-16 的探索性补跑没有预注册。**它是在看到主矩阵的旧线索和上游评论的预测之后才跑的，结论方向事先已有预期。它不进实验卡的 x/N，单独列出；前后 F0 对照、版本和二进制核对、隔离与补测相同。
- **续写分支对 Claude Code、codex 不适用。**它们的重发都不带半截（18/18），mock 用的是重写分支。
- **下一轮证人多发了一个请求。**每次运行在最终截屏之后，再发一句"好的，谢谢。"，用来看下一次请求里带了什么。这不影响判定，但每次运行因此多一个请求。
- **主矩阵和续写对照的污染。**
  - 端口冲突：UTC 08:24–08:36，同一台机器上另一个执行者占用了相同端口。受影响的非交互批次已整批作废重跑，但 Claude Code 交互 F1 每次都断的第 1 次没有筛掉。
  - 隔离不完整：Claude Code 在 LaunchServices 里注册了自己临时 HOME 里的 URL Handler，11-15 已注销。Kimi Code 设置了 `auto_install=false`，仍拉取了 25 次更新清单；它的临时 HOME 里还多出一个 `fd`。
  - 原地改写：`cleanup.py` 原地改写了证据，主矩阵 1387 个文件，续写对照 41 个。所以这两轮的原始证据不再是原样，本报告只用复验核对过的数字。
  - 补测的证据目录一个字节都没改，公开副本由 `export_public.py` 导出。

## 还没做的

- Kimi Code 没有用新装置补测（失败标记、原始字节、400 行窗口）。它的数字来自主矩阵和续写对照，按复验更正。F6 的结论另有 #4964 的最小复现支撑。Kimi Code 2.6.0 已经发布，没有测。
- 待验证的观察（Kimi Code 不带 `partial` 标记）那一条，真实服务端分支没有测：要调用真实接口，按约束不做。
- **posting gate**（`skills/repo-quake/references/reporting.md`）：
  - 发现一已有上游 issue #4964；
  - Kimi Code 不带 `partial` 标记那一条，按决定不报上游，本报告写成待验证的观察；
  - 发现二里 codex 的"重叠"和重试用完时的拼接，11-16 补在上游 [openai/codex#47538](https://github.com/openai/codex/issues/47538) 下（[评论](https://github.com/openai/codex/issues/47538#issuecomment-6905066983)，读回逐字一致），没有新开 issue；
  - 本报告和这一期的提交随 repo-quake v0.2.0 一起推送（2026-11-16）。本文件在推送前定稿，推送后的本地与远端 SHA 核对不在这里，按 `reporting.md` 在推送之后单独做。

## 证据

- 实验卡（冻结）：`cards/phase4-stream-retry.json`
- 补测公开副本：`runs/phase4-stream-retry-2026-11-15/`。包括 `summary.md`、逐次 `record.json`、截屏、原始字节分析和送达日志；请求体、会话文件和原始字节没有公开（见该目录的 `EXPORT.md`）。
- 探索性补跑公开副本：`runs/phase4-codex-retries-exhausted-2026-11-16/`。逐次份数在 `retries-exhausted-counts.json`；`upstream-repro/` 里是最小复现、发出的评论原文和最小复现的截屏。
- 装置与测试：`witness/stream-retry/`、`tests/test_stream_retry.py`
- 披露文件：`docs/phase4-disclosure.md`
- 执行提示词模板：`plans/TASK-stream-retry-display.md`
- 台账：`ledger/ledger.json` 的 RQ-F-014 至 RQ-F-017、RQ-I-009、RQ-I-010、RQ-X-011 至 RQ-X-014
