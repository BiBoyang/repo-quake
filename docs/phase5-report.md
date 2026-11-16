# repo-quake Phase 5 报告：用第 4 期的装置复测 metacodes、deepseek-harness，复查 9 月的交互附录和 skill-up 的修复（2026-11-16）

第 4 期造了一套"流断在中途、自动重发之后，屏幕和对话还一致吗"的装置（`witness/stream-retry/`）。这一期用它复测以前测过、但用的是旧方法的目标，按优先级分四块：

1. **metacodes**：从 upstream/main 现在的提交自己构建，测 TUI 和三种非交互输出。这一轮可以当作 TUI 改版前的基线。
2. **9 月截断矩阵的交互附录**：Claude Code 2.1.282、codex 0.169.0，长度截断（F4）和只有思考的截断（F5）。
3. **deepseek-harness**（下文简称 dsh）：9 月测的是 0.1.7-rc.2，这次测 0.2.2-rc.3，只测非交互。
4. **alibaba/skill-up**：复验两个已经合入的修复，看一个还开着的 issue 是否仍然复现。

全部只连本机回环地址上的 mock，或者完全不联网（skill-up 用的是不调用模型的假引擎）。没有调用任何付费模型。被测程序都用 `env -i` 白名单加临时 HOME 启动，`sandbox-exec` 只放行到 localhost 的连接。

## 头条

| 被测 | 结论 | x/N |
|---|---|---|
| metacodes TUI（main 1707da0c） | 断流后自动重发一次；断掉那次已经显示的文字或思考**留在屏上**，重发的完整回答直接接在下面，中间没有任何提示。这是 [#465](https://github.com/metask-ai/metacodes/pull/465) 正文里写明并接受了的取舍，不是新缺陷。本期新增的是实测 15/15、只有思考时整段思考也留屏、屏上那段模型从没见过（存下的对话和下一轮请求里都没有）、原始字节里零提示 | fork 15/15 |
| metacodes `-p`、`--json` | 断掉那次从不打印；stdout 只有一份完整回答，退出码 0；stderr 每次都有一行 `[ERROR agent …] stream returned error … at turn 1`，尽管这一轮已经恢复 | not shown 30/30 |
| metacodes `--stream-json` | 断掉那次的文字和思考都流出来了，随后用 `output_segment_end … "disposition":"discarded"` 收回；没有重发事件 | retracted 15/15 |
| Claude Code 2.1.282（TUI 和 `-p`） | F4 带着第一次的回答续写，F5 从头重发；原始字节、最终画面、stderr 里都没有一句提示。9 月"用户侧零信号"仍成立，这次有字节级证据 | 12/12 无提示 |
| codex 0.169.0（TUI 和 `exec`） | **变了**：9 月 0.156.1 对 F4/F5 是 `Reconnecting... 1/5` 后重放；现在不重发，留一条常驻的 `Incomplete response returned, reason: max_output_tokens`，`exec` 退出码 1、stdout 为空 | 12/12 报错不重发 |
| dsh 0.2.2-rc.3（三种协议） | F1/F2/F3/F6 静默重发、恢复、退出码 0；F4/F5 仍是**光秃秃的退出码 1**：stderr 没有一句 dsh 的话，会话日志却记着 `max-tokens`。F6 是第一次测 | 36/36、18/18 |
| skill-up v0.15.0 | #253、#263 按 issue 原始复现确认已修；#280 仍复现（`validate` 照样说 valid）。#281 的构建用 `validate --skill` 报出 5 处问题，加 `--strict` 退出码 1 | 修 2/2，复现 1/1 |

表里的判定标签只是判分笔记，台账只记五个观察字段：detected（检出）、reported（告诉了用户）、contained（失败的那次没留在显示或对话里）、recovered（恢复出完整回答）、reverified（再验证），见 `ledger/SCHEMA.md`。

本期用到的几个故障形态，先用大白话说清：

- **F1**：回答流到一半，TCP 连接正常关闭，没有任何结束信号。
- **F6**：只发一半内容，HTTP 正文却完整结束，但没有结束事件。
- **FLONG**：先流出 160 段（超过一屏）再断开。
- **FTHINK**（本期新增）：先流一段思考（thinking），一个字的正文都还没有，就断开。这是 metacodes 在线上真正碰到的触发条件：推理模型总是先流思考。断法有两种：FTHINK1 是 FIN 断开，FTHINK6 是干净收尾但没有结束事件。重发那次是普通的健康回答。
- **F4**：完整回答之后又多出一段，然后以长度上限收尾（Anthropic 的 `max_tokens`、Responses 的 `response.incomplete`）。
- **F5**：只有思考、没有正文，然后以长度上限收尾。
- **F2**：内容发全了，但缺结束事件；**F3**：半截之后跟半个 SSE 事件，再 FIN。

"失败标记"是第 4 期的做法：失败那一次的每段末尾都追加一个只有它才有的标记（形如 `〔x1a2b3c〕`），屏上、stdout 里出现过它，就证明失败那次显示过。

## 第一部分：metacodes

### 被测和装置

- **版本**：`git worktree add --detach` 出 upstream/main `1707da0c676863f62d99d58b1e33d0956cf21d1d`（11-16 04:36Z，合并 #510），`zig build` 得到 `metacodes 0.12.1-dev+1707da0c6768`（zig 0.16.0，ReleaseSmall）。实际执行的二进制 sha256 `ee7718a91d7d3baa5288e9f54c8bdbaae0eae2720b4896818658be3bdad2cd64`，每次 TUI 运行用 `lsof` 核对，前后两次版本证人一致。用完 `git worktree remove` 删掉了，二进制另存在证据目录。`metacodes-zig` 本身的检出、分支和文件没有动。
- **指向 mock**：`--base-url http://127.0.0.1:<端口>/v1/messages`（metacodes 讲 Anthropic Messages），环境变量 `METASK_API_KEY=dummy METACODES_NO_PROBE=1 METACODES_KG_AUTOSTART=0`，另加 `METACODES_JEV_URL=off`（关掉默认的 Jev 查询；沙箱本来也会拦）。metacodes 启动时不查更新（更新是显式的 `update` 子命令）。矩阵期间沙箱拦下的外连：0 次。
- **四种模式**：TUI（tmux 110×400）、`-p`、`-p --json`、`-p --stream-json`。
- **怎么读三种非交互输出**：`-p` 读 stdout；`--json` 读结果行的 `text`；`--stream-json` 按协议读：每行 `text`/`thinking` 归到它到达时开着的那个输出段，被标成 `discarded` 的段整段丢掉（思考一起丢），剩下的就是消费者该显示的。stdout 里只要出现过失败标记，就算"显示过"（stdout 只追加不回退）。
- **条件**：F0 前、F0-tag（文字的阳性对照）、F0T-tag（思考的阳性对照，见下）、F1、F6、FLONG、FTHINK1、FTHINK6、F0 后，每格 3 次，共 108 次。
- **F0T-tag** 是本期加的阳性对照：一个健康回答，先流一段完整的、带失败标记的思考，再给出完整正文。它回答"这个模式到底显示不显示思考"：TUI 和 `--stream-json` 显示（3/3），`-p` 和 `--json` 从不显示（3/3，记为 `thinking_hidden`，这是结果，不是失败）。所以 `-p`、`--json` 下 FTHINK 的"没显示"是结构性的，不是撤回得好。

### 结果

| 模式 | F0 前/后 | F0-tag | F0T-tag | F1 | F6 | FLONG | FTHINK1 | FTHINK6 | 五字段（故障格） |
|---|---|---|---|---|---|---|---|---|---|
| TUI | healthy 6/6 | 3/3 | 显示 3/3 | fork 3/3 | fork 3/3 | fork 3/3 | fork 3/3 | fork 3/3 | detected ✓、recovered ✓、contained ✗、reported ✗ |
| `-p` | healthy 6/6 | 3/3 | 不显示 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | detected ✓、contained ✓、recovered ✓、reported ✓（只在 stderr） |
| `--json` | healthy 6/6 | 3/3 | 不显示 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | not shown 3/3 | 同上 |
| `--stream-json` | healthy 6/6 | 3/3 | 显示 3/3 | retracted 3/3 | retracted 3/3 | retracted 3/3 | retracted 3/3 | retracted 3/3 | detected ✓、contained ✓（按协议）、recovered ✓、reported ✓（只在 stderr） |

**TUI 的细节（15 次故障运行，每次都一样）：**
- 断开到重发开始 583–643 ms（代码里的重发退避是 500 ms）。
- 失败标记由中途截图截到：F1、F6 早于重发开始 816–882 ms；FTHINK 707–746 ms；FLONG 约 24.7 s（边流边显示）。
- 失败那次从没被收回：最终画面上，F1、F6 是 12 个标记，FLONG 160 个，FTHINK 是 6 段思考（R01–R06）。重发的完整回答紧接在下面。
- 原始字节里没有任何提示，一次都没有。读码：TUI 的重发提示从第 3 次才显示（`src/repl/tui/tui_backend.zig` 的 `.retry_notice`，`attempt < 3` 直接返回），输出段的开始和结束事件在 TUI 里是空操作（同文件 `.output_segment_begin, .output_segment_end => {}`），思考和正文用同一个渲染路径。
- 存下的对话（`transcript.jsonl`）和下一轮请求里都**没有**失败那次：标记 0/15，下一轮请求只带重发那份完整回答。屏上留着的文字和思考，模型从没见过。
- TUI 没有切备用屏幕（原始字节里没有 `ESC[?1049h`），FLONG 断开前一刻 150 段、横幅和提示词同屏（3/3）。

**非交互的细节（45 次故障运行）：**
- 退出码都是 0，都只发了 2 个正式请求（断掉的一次加重发一次）。
- stderr 每次都有一行红色的 `[ERROR agent req=…] stream returned error RequestFailed at turn 1`（F1、FLONG、FTHINK1）或 `… StreamIncomplete at turn 1`（F6、FTHINK6）。这一轮其实已经恢复了，这行字却写着 ERROR。
- `--json` 的结果行是 `stop_reason: end_turn`、`text_kind: final`、`continuations: 0`，不提重发；但 `input_tokens` 是 48（健康时 24），也就是断掉那次的用量算进去了。
- `--stream-json`：段 0 是 `discarded`，F1/F6 里装着 12 段正文，FLONG 160 段，FTHINK 里是 6 行思考、0 行正文；段 1 是 `final`。没有落在段外的行，也没有重发事件，最后 `run_end … end_turn`。

**和以前的结论对照：这是 #465 写明的取舍。** 11-12/13 的流中断笔记写过"TUI 有可见输出后断流只发 1 个请求"；那是 #465 之前。[#465](https://github.com/metask-ai/metacodes/pull/465)（修 #461，wayfind 写，2026-11-13 由 BiBoyang 合入）之后，每个请求默认重发一次（`STREAM_RETRIES_PER_REQUEST = 1`），已有可见输出也重发。它的正文在"Things a reviewer may want to weigh"里写明了 TUI 的后果："The partial text stays in scrollback, followed by the retried answer."，并说 TUI 在第 3 次之前照旧不显示 `retry_notice`。所以"重发成功，但屏上留着断掉那次"是合入时就写明、接受了的取舍，不是新缺陷。

第 5 期在这个取舍上新增的是四点：
- **实测**：#465 的正文只描述了行为；本期是 15/15 的计数，外加 11-13 在 06ea8075 上的那次单次观察。
- **只有思考时也留屏**：#465 正文说的是 partial text；FTHINK 显示，断掉那次一个字正文都没有、只有思考时，整段思考同样留在屏上（6/6）。#465 的测试只检查了思考不进历史，没有检查屏上。
- **屏上那段模型从没见过**：存下的对话（`transcript.jsonl`）和下一轮请求里都没有它（15/15）。用户看到的上文，和模型下一轮拿到的上文不一致。
- **原始字节里零提示**：不只最终画面上没有，终端收到的字节里也没有（15/15），符合正文说的"第 3 次之前不显示"。

要不要据此提一个 enhancement（标出被丢弃的那次、第一次重发也给提示），由负责人定；草稿见文末。

**不测的：** 网页端（`--web`/`serve`）和 AgentCore C ABI 宿主，这套装置驱动不了（它只会开 tmux 和读 stdout），记 N/A。11-13 的读码笔记说网页端收到 `discarded` 后只在控制台打 `unhandled event`、半截留在页面上；本期没有复测。

## 第二部分：9 月截断矩阵交互附录的复查

9 月那张附录（`interactive-appendix/APPENDIX.md`，12 次）是在备用屏幕盲区下测的：只看最终画面，0.4 秒轮询抓瞬态提示，没有原始字节。它的两句结论这次要验：①"交互和非交互没有差别"；②Claude Code 对 F4/F5 是"用户侧零信号"。

这次用第 4 期装置：失败标记、原始字节、110×400 窗口、会话文件。为了回答①，在同一版本、同一 mock 上加测了非交互（`claude -p`、`codex exec`），这超出了任务原定的范围，记在偏离日志里。每格 3 次，加 F0 前后对照和 F0-tag 阳性对照，共 60 次，前后版本一致。

| 宿主 | F4（长度截断） | F5（只有思考） | 提示 | 五字段 |
|---|---|---|---|---|
| Claude Code TUI | 续写 3/3：带着第一次的回答，再加一条用户消息 `Output token limit hit. Resume directly — no apology…` | 从头重发 3/3 | 无（原始字节、最终画面都没有），6/6 | F4：detected ✓、reported ✗；F5：detected ✓、reported ✗、recovered ✓、contained ✓ |
| `claude -p` | 续写 3/3 | 从头重发 3/3 | 无，6/6（stderr 只有一条每次都有的模型目录警告，F0 也有） | 同上 |
| codex TUI | 不重发 3/3 | 不重发 3/3 | 常驻：`■ Incomplete response returned, reason: max_output_tokens`，6/6 | detected ✓、reported ✓、recovered ✗ |
| `codex exec` | 不重发 3/3 | 不重发 3/3 | `ERROR: Incomplete response returned, reason: max_output_tokens`（两行），退出码 1，stdout 为空，6/6 | 同上 |

**① "交互和非交互没有差别"：仍然成立**（就检测、重发和提示而言）。两个工具在两种模式下发的请求、带的内容、给的提示完全一样。显示上有一处差别，9 月也有：F4 时 Claude Code TUI 把两次都留在屏上（第一次的 P01–P24 加溢出段，下面是续写的回答），`-p` 只打印最后一条消息。

**② Claude Code "用户侧零信号"：仍然成立，这次是字节级证据。** 12 次 F4/F5 里，原始字节、最终画面、stderr 都没有任何提示。机器那边记得清楚：会话文件里第一次是 `stop_reason: max_tokens`。另外两个细节：
- F5 失败那次的思考在 TUI 里显示了 216–254 ms，然后被收掉；会话文件仍保留着那段思考（6 个标记），重发请求没带它。
- F4 续写之后，下一轮请求带着第一次被截断的回答（3/3），这符合续写的语义。

**codex：9 月的结论不再成立。** 0.156.1 对 `response.incomplete` 是"检出、重试、恢复"，文案却是 `Reconnecting... 1/5`（把长度截断说成连接问题）。0.169.0 改成了"检出、如实报告、不重试"：提示原话说出了真正的原因（`max_output_tokens`），而且常驻在最终画面上；但不再恢复。TUI 里 F4 的回答留在屏上，下一轮请求也带着它（3/3）；F5 的推理摘要显示 128–139 ms 后被收掉。

**待验证的观察（不是已确认的缺陷，没有报上游）：** `claude -p` 在 max_tokens 续写之后只打印最后一条消息。本期 mock 对续写请求总是从头重写，所以 stdout 看起来是一份完整回答。如果真实服务端是接着写（续写的本意），`-p` 的 stdout 很可能只剩后半截，而退出码是 0、没有提示。要验证，需要在回答中途给长度截断（P01–P12 后 `max_tokens`），并让 mock 对"续写请求"只回剩下的部分。本期没做。

## 第三部分：deepseek-harness 0.2.2-rc.3

### 被测和装置

- **版本**：npm 包 `@deepseek-ai/dsh@0.2.2-rc.3`（dist-tag `next`；GitHub 标签 `dsh-v0.2.2-rc.3`，11-13 发布，发布页没有附件）。经用户同意，用 `npm install --ignore-scripts` 装进证据目录里的隔离前缀：676 个包，压缩包约 307 MB，装好后 `node_modules` 1.4 GB；5 个包的安装脚本没有运行。安装树 95,730 个文件，矩阵前后的哈希清单摘要一致（`3de4349a…`）。
- **指向 mock**：9 月那篇《给流式协议造故障》第 2 节的做法：每次运行一个新的 `DSH_HOME`，在 home 层的 `cordis.patch.yml` 里把默认模型指到 pi-ai 适配器下的 mock 路由，`api` 选协议（`openai-completions`、`openai-responses`、`anthropic-messages`）。`DSH_TELEMETRY_DISABLED=1`。矩阵期间沙箱拦下的外连：0 次。
- **一个夹具坑**：dsh 会用第一条用户消息另发一个生成标题的请求，它是纯文本、不是结构化输出，又带着本次的随机标记，旧 mock 会把它当正式回答、让它吃掉一次性故障。本期给 mock 加了 `aux_match`：被测声明自己辅助请求的特征串（这里是标题请求的系统提示词开头），mock 就把它当辅助请求。72 次里标题请求都被正确识别。
- **三种协议都测**：任务没指定协议；9 月是三行，为了逐行对比。共 72 次，前后版本一致。

### 结果

| 协议 | F0 前/后 | F1 | F2 | F3 | F6（首次） | F4 | F5 |
|---|---|---|---|---|---|---|---|
| Chat Completions | healthy 6/6 | 静默重发 3/3 | 静默重发 3/3 | 静默重发 3/3 | 静默重发 3/3 | 退出码 1、无诊断 3/3 | 退出码 1、无诊断 3/3 |
| Responses | healthy 6/6 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| Anthropic Messages | healthy 6/6 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |

五字段：F1/F2/F3/F6 是 detected ✓、contained ✓、recovered ✓、reported ✗（stdout 只有一份完整回答，stderr 为空，退出码 0）。F4/F5 是 detected ✓、reported ✗：
- F4：stdout 打印了第一次的全部内容（P01–P24 加溢出段），然后退出码 1，stderr 为空。
- F5：stdout 只有一个换行，stderr 只有 `dsh: reasoning:` 下流出的那段思考，然后退出码 1。
- 会话日志（`session.v4.jsonl.zstd`）两种都记着 `turn/end` 的 `reason.kind: max-tokens`。

**和 9 月对照。** 9 月的发现是"机器那边记得清清楚楚，用户只拿到一个光秃秃的 exit 1"（当时唯一的失败痕迹是 pnpm 包装器打的 `[ELIFECYCLE] Command failed with exit code 1.`，直接跑 dsh 的用户连这行都看不到）。0.2.2-rc.3 直接跑 npm 装的 dsh，仍然如此，三种协议 18/18。这和 0.2.2-rc.3 headless README 的"Exit mapping"一致：最后一个 `turn/end` 是 completed 才退出 0，其他结果都退出 1，只有 `error` 原因才在 stderr 打 `dsh: <code>: <message>`。`max-tokens` 属于"其他结果"，所以退出 1 却一句话都不说。缺的是一行给人看的说明，不是检测。F1–F3 和 9 月一样是静默重发；F6 是第一次测，同样静默重发。

**上游相近的讨论。** deepseek-harness 关了 issue（`hasIssuesEnabled=false`），CONTRIBUTING.md 写明 bug 在 GitHub Discussions 报。已有三条相近的讨论，都没覆盖"退出码 1、stderr 没有诊断"这一点：
- [#12347](https://github.com/deepseek-ai/deepseek-harness/discussions/12347)（General，0.2.1-rc.2）：headless 下一步只有思考就撞上长度上限，最终答案为空、stderr 为空，原帖说退出"看起来正常"，没写退出码；它看的是 JSON 事件日志。原帖期望里也提到"至少以显式错误或非零退出码结束"。本期 0.2.2-rc.3（npm CLI、默认输出）测到的是退出码 1。这个差别来自版本、来自输出模式，还是来自 PyPI SDK 包装，没有核实：没跑 0.2.1-rc.2；0.2.1-rc.2 到 0.2.2-rc.3 之间的升级指南里没有提到退出码映射的变化。
- [#11298](https://github.com/deepseek-ai/deepseek-harness/discussions/11298)（General，0.1.2-rc.1）：max-tokens 走正常完成路径，turn 被标成完成，界面显示"完成"。
- [#10743](https://github.com/deepseek-ai/deepseek-harness/discussions/10743)（Ideas，0.2.1-rc.2）：长度截断后自动续写的需求，界面只有一个手动 Continue 按钮。

## 第四部分：skill-up 修复复验

- **版本**：v0.15.0（11-09 发布的最新版）。经用户同意，用本地克隆里已有的 v0.15.0 源码构建（`git archive` 到证据目录，`go build`）；只下载了一个缺的 Go 模块 `github.com/openai/openai-go/v3 v3.86.0`（2,356,710 字节，proxy.golang.org，go.sum 校验），它进了本机的 Go 模块缓存。二进制 sha256 `031e5cfd…`，版本字符串是 `dev`（没注入 ldflags）。上游 main 在 v0.15.0 之后还有提交，没测。
- 全部用不调用模型的假引擎（`custom` 引擎、`local` 传输、几行 shell 脚本），`env -i` 临时 HOME，沙箱只放行 localhost。

| issue | 原始复现 | v0.15.0 结果 |
|---|---|---|
| [#253](https://github.com/alibaba/skill-up/issues/253)（[#257](https://github.com/alibaba/skill-up/pull/257) 已合） | 原帖的 Go 片段：对符号链接的 skill 目录调 `agent.ListSkillFiles` | 结果是 `[. SKILL.md references references/a.md]`，和带结尾斜杠时一样（修前只有 `["."]`）。端到端：通过符号链接路径跑 `skill-up run`，假引擎在工作区里看到 `SKILL.md`、`references/a.md`，用例 PASS。上游为此加的 3 个回归测试也都通过 |
| [#263](https://github.com/alibaba/skill-up/issues/263)（[#265](https://github.com/alibaba/skill-up/pull/265) 已合） | 原帖的端到端：引擎在子进程结束后才写 `${output_file}`，用例超时设 3 秒 | 3 秒时被杀；`outputs/agent/run/session-result.json` 存在，`exit_code: 124`，stderr 写明是"截止时间到了、引擎还没写结果"的合成产物（修前这里只有输入文件）。上游 6 个超时相关测试也都通过 |
| [#280](https://github.com/alibaba/skill-up/issues/280)（[#281](https://github.com/alibaba/skill-up/pull/281) 未合） | 一个受损的 skill：frontmatter 的 name/description 为空，正文引用的 `references/format-rules.md`、`assets/template.md`、`scripts/check.sh` 都不存在，结尾截断在半句 | **仍复现**：`skill-up validate evals/eval.yaml` 输出 `✓ eval.yaml is valid`，退出码 0；`validate --skill` 是未知参数 |

**#281 对同一个夹具**（用本地 PR 分支 8c9e12b 构建，它就是 PR 当前的 head）：`validate --skill <dir>` 报出 5 处问题（name、description 为空，三个引用不存在），退出码 0，并提示加 `--strict`；加 `--strict` 后退出码 1。半句截断本身查不出来，这是 #281 正文里写明的范围（没有基线就无法静态判断内容截断）。按 #281 的设计，`validate <eval.yaml>` 仍然不查 skill 内容。

台账：RQ-F-021（#253）、RQ-F-022（#263）记为 fixed，RQ-F-023（#280）仍为 reported。

## 装置改动（`witness/stream-retry/`）

- **适配器**：`Metacodes`（TUI 和 `-p`）、`MetacodesJson`、`MetacodesStreamJson`；`Dsh`、`DshResponses`、`DshAnthropic`。
- **mock**：新增 FTHINK1、FTHINK6、F0T 三种形态（Anthropic、Chat Completions、Responses 三种方言都有）；F5 的思考也带失败标记；新增 `aux_match`。
- **判定**（`grading.py`）：
  - 思考的阳性对照（`thinking_hidden` 是一种结果）；
  - 非交互的"显示"按模式读：结果行、按协议丢弃 `discarded` 段；stdout 里出现过标记就算显示过；
  - F4/F5 走单独的判定 `_grade_signal`：有没有跟进请求、带没带第一次、提示在哪；提示用更宽的词表（加了 token、limit、incomplete、截断等词），在第 4 期这两个二进制的 36 次运行上校准过，没有多抓一行；
  - 第 4 期的判定只在 fork 上记 `reported`，本期所有重发分支的判定都记 `reported`，另记 `notice_where`（final、raw-only、none）；
  - 被测自己固定 UI 里含提示词的行可以按工具排除：metacodes 空输入框写着 `Try "fix typecheck errors"`，含 "error"，不排除的话每个健康对照都会被判失败。
- **会话文件**：能读 zstd 压缩的 dsh 会话日志、metacodes 的 `blocks`、Anthropic 的 thinking 块，停止原因认 dsh 的 `reason.kind`。
- **测试**：`tests/test_stream_retry.py` 从 52 个增加到 76 个；`bash tests/run_tests.sh` 全部通过（unittest 124 个，另校验三张第 5 期实验卡）。三个矩阵跑完后，用最终版的判定代码从证据文件重判（`runner.py regrade`），240/240 结果不变。试跑里发现的 mock 崩溃（codex 的标题请求走 `/v1/responses`，结构化输出没有思考字段）有回归测试，并做了变异检查：把修复改回去，测试失败；从副本还原后 `cmp` 一致。

## 诚实清单

- **试跑。** 冻结前的试跑都没计入：metacodes 每格 1 次共 24 次，附录 13 次（其中 codex 交互那轮因 mock 崩溃中断），dsh 24 次加手工几次。三张实验卡里的预测参考了试跑，卡里写明了。
- **超出任务的加测。** metacodes 加了 F0-tag 和 F0T-tag 两个阳性对照；附录加了 F0-tag 和两种非交互宿主；dsh 三种协议都测。都记在各自的偏离日志里。
- **`reported` 的口径变了。** 和第 4 期比，本期在 not shown、retracted 上也记 `reported`。第 4 期已发布的数字不受影响（判定标签没变）。
- **FTHINK 的重发没有思考。** 真实的推理模型重发时会再想一遍。本期的重发是普通回答，所以只回答"断掉那次的思考去哪了"。
- **mock 对续写总是从头重写。** Claude Code 的 F4 续写因此在 TUI 里显示两份、在 `-p` 里看起来完整；这两个现象都依赖这个假设（见"待验证的观察"）。
- **dsh 没跑安装脚本**（用户选择）。被测启动和回答都正常，但需要那 5 个脚本的代码路径（例如 node-pty 的本地构建）不在本期覆盖内。
- **skill-up 测的是 v0.15.0 源码自建的二进制**，不是官方发布包；上游 main 更新的提交没测。下载的那个 Go 模块留在了本机 Go 缓存里。
- **tmux 不是真终端；沙箱让被测离线。** 外连拦截：metacodes 0、dsh 0、Claude Code 0、codex 55（都是启动时的域名解析）。
- **LaunchServices**：每个矩阵之后都查了，只有用户自己 `Applications/` 下那一份 Claude Code URL Handler。
- **一次只跑一个执行者。** 三个矩阵依次跑，中间没有并行的被测运行。npm 安装和 Go 构建在矩阵之间做。

## 还没做的、要你定的

- **metacodes TUI 留屏**：#465 已写明这是取舍，是否在它之上开一个 enhancement（标出被丢弃的那次、第一次重发也给提示）由负责人定，指派也由负责人定（TUI 归他本人管）。enhancement 草稿在工作区根目录 `metacodes-issue-draft-tui-retry-fork-2026-11-16.md`，没有发。
- **dsh 的"光秃秃的退出码 1"**：上游关了 issue，按 CONTRIBUTING 走 Discussions；相近的 #12347、#11298、#10743 没覆盖这一点。发不发由负责人定。Discussion 草稿（General 分类，标题带 `[Bug]`）是 `dsh-issue-draft-length-stop-bare-exit-2026-11-16.md`，没有发。按 posting gate，第三方的发现要先在上游报过，本报告才能公开。
- **#12347 那边的退出码**：要核实"0.2.1-rc.2 退出看起来正常、0.2.2-rc.3 退出码 1"是不是版本差别，需要另装 0.2.1-rc.2 跑一次；要下载，没做。
- **Claude `-p` 续写后只打印最后一条消息**：要不要补一个"回答中途长度截断 + 续写分支 mock"的小实验来验证。
- **推送**：repo-quake 的改动只在本地分支 `feat/phase5-stream-retest` 提交，没有推送。
- skill-up #280 和 #281 的状态没有变化，不需要动作；#281 对这个夹具的结果可以补进 PR 讨论，要不要补由你定。

## 证据

- 公开副本（`export_public.py` 导出、`audit_artifacts.py` 审计通过）：`runs/phase5-metacodes-2026-11-16/`、`runs/phase5-appendix-f4f5-2026-11-16/`、`runs/phase5-dsh-2026-11-16/`。请求体、会话文件、终端原始字节没有公开（见各目录的 `EXPORT.md`）。
- 实验卡（冻结）：`examples/experiment-card-phase5-metacodes.json`、`examples/experiment-card-phase5-appendix-f4f5.json`、`examples/experiment-card-phase5-dsh.json`。
- 装置与测试：`witness/stream-retry/`、`tests/test_stream_retry.py`。
- 披露：`docs/phase5-disclosure.md`。
- 台账：`ledger/ledger.json` 的 RQ-F-018 至 RQ-F-024、RQ-I-011、RQ-I-012、RQ-X-015。
