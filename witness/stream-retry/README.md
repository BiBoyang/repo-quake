# witness/stream-retry：流中途断开、自动重发之后的显示证人

要回答的问题：模型的流式回答断在中途、CLI 自动重发之后，**屏幕（或 stdout）上显示的，和对话里存下、下一轮要发给模型的，是否一致**。

这是 repo-quake 第 4 期的实验装置。起点是 2026-11-14/15 两轮横向实验的 `runner.py`、`mock.mjs`、`version_witness.py`，按 11-15 独立复验报告的返工清单（12 条）逐条修过后移植到这里。原来那份会原地改写证据的 `cleanup.py` 没有搬，换成了只改副本的 `export_public.py`。

## 文件

| 文件 | 作用 |
|---|---|
| `mock.mjs` | 本地 mock（只监听回环地址）。三种协议：Chat Completions、Responses、Anthropic Messages。故障形态 F0–F6、FLONG 都是参数；控制面要带令牌。每个请求的送达记录里有毫秒时间戳，以及续写还是重写的决定。 |
| `content.json` | 共享内容夹具，mock 和判定共用。P01–P24 与前两轮逐字相同；长回答完整形态是 L001–L200，半截是前 160 段。 |
| `grading.py` | 纯判定逻辑，不碰网络和终端。也负责请求体分析、会话文件分析，以及原始字节分析（去转义、备用屏幕、失败标记、提示原话、字节到时间的对齐）。 |
| `runner.py` | 矩阵执行器：`probe`、`matrix`、`regrade`、`summarize`、`egress`、`lsregister`。 |
| `skills/repo-quake/scripts/card_gate.py` | 不在本目录（2026-11-21 起和 `validate_card.py` 放在一起，第 6 期的 `stall.py` 也用它）。`matrix` 开跑前的门槛：实验卡要通过校验、已经提交，计划和预算要覆盖这次矩阵（见下文"开跑门槛"）。 |
| `rawtap.py` | 接在 `tmux pipe-pane` 上：把终端收到的原始字节写进 `raw.bin`，并给每一块记下收到的时刻（`raw-index.jsonl`）。 |
| `version_witness.py` | 前后各记一次版本和 sha256。对象是实际执行的文件：codex 要从 `codex.js` 追到它 execve 的原生二进制；运行 `codex.js` 的 node，以及 mock、夹具和装置本身，也都要算。 |
| `export_public.py` | 把要公开的证据复制一份、在副本上脱敏、扫描禁用串，再用 `skills/repo-quake/scripts/audit_artifacts.py` 审计。前后核对源目录的哈希清单，确认一个字节都没改。 |
| `summarize.py` | 从 `runs.jsonl` 生成 `summary.md`。 |

测试在 `tests/test_stream_retry.py`，已接入 `tests/run_tests.sh`。校准用的假 TUI 在 `tests/fixtures/stream-retry/fake_tui.py`，它有"收回半截""留着半截""完整回答渲染两遍"三种模式，用来证明证人能把这几种情况分开。

## 一次交互运行做什么

1. **启动 mock。** 端口用 0（临时端口），令牌和实例号由执行器生成。启动后核对三件事：就绪文件、`/health` 返回的实例号、`lsof` 查到的监听进程正是这个子进程。端口被占，或者对不上，就拒绝运行。
2. **启动被测程序。** 每次运行用一个新的临时 HOME，按工具预置好一次性对话框的答案。启动方式是 `env -i` 白名单加 `sandbox-exec`：只放行到 localhost 的出站连接，DNS 也走不通。tmux 用独立的 socket 和空配置，窗口默认 110×400，让整段对话都留在屏幕上。
3. **先接字节，再放行。** `pipe-pane` 先接上 `rawtap.py`，再放行程序启动，所以第一个字节也能记下来。
4. **按键闸门。** 输入框出现、屏上没有更新、迁移、信任、登录之类的提示，才能输入提示词。按回车前再验一次屏：要看到刚输入的文字，而且没有提示框。
5. **在 mock 上布置一次性故障。** 用三个条件钉住正式回答：请求体里要有本次的随机 mark；不是结构化输出请求（生成标题的辅助请求就是这种）；是流式请求。失败那一次的每个段落末尾，都追加一个只有它才有的标记（形如 `〔x1a2b3c〕`）。
6. **轮询截屏。** 默认每 30 ms 截一次。屏上第一次出现失败标记时，存下中途截图（`mid.txt`），带时间戳。半截第一段和重发的第一段同时在屏上时，存下重叠截图（`overlap.txt`）。FLONG 流到 L150 时，存下断开前的截图（`prefin.txt`）。
7. **何时结束。** 重发完成、完整回答的最后一段已在屏上，并且画面稳定 3 秒，就结束。如果故障之后，请求日志和画面都连续 60 秒没有变化，就判定为不重发（这个静默窗口不能短于 40 秒，因为实测的最大重发间隔是 33–40 秒）。
8. **最终截屏。** 截下最终画面。画面完整的判据是：横幅（工具名和版本）和本次 mark 都还在屏上。
9. **下一轮证人。** 再输入一句中性的话（"好的，谢谢。"），看客户端下一次请求的 assistant 历史里，半截还在不在。
10. **收尾和记录。** 退出被测程序。从请求体、会话文件、原始字节里提取证人，判定，然后写进 `record.json` 和 `runs.jsonl`。

非交互模式（`claude -p`、`codex exec`、`kimi -p`）走同一个 mock 和同一套判定。stdout 只追加不回退，所以 stdout 里出现过失败标记，就算显示过。

## 判定（冻结的 rubric，`grading.grade()`）

判定标签只是判分笔记，台账只记五个观察字段（`ledger/SCHEMA.md`）。下表对应 `skills/repo-quake/references/fault-catalog.md` §stream 的"重发后的显示结果"表。

**健康对照 F0-pre、F0-post 要逐项检查，不能默认判成 healthy。** 下面任何一项不满足，都判 `control_failed`：
- 恰好一个正式请求，它干净结束，而且有终止证人；
- 没有任何请求被注入了故障；
- 最终显示里，完整回答的每一段恰好出现一次，没有别的编号；
- 交互模式下画面完整；
- 最终画面和原始字节里都没有错误或重试提示；
- 非交互模式下退出码为 0。

**阳性对照 F0-tag。** 回答本身是健康的，只是前 12 段带了失败标记。要通过，必须同时满足三条：原始字节里有标记、有由标记触发的中途截图、最终画面上恰好 12 个标记。它证明了一件事：标记确实能穿过这个工具的渲染器，显示在屏幕上。所以"没看到标记"就等于"没显示半截"。这一格不过，该工具的故障格不跑。

**故障格（F1、F6、FLONG 的 once 形态），按顺序判：**

1. 一次性故障没有送到带 mark 的正式流式请求上，判 `n/a`。
2. 之后没有干净完成的重发：
   - 最终画面或原始字节里有错误或重试提示，判 `reported_failure`；
   - 只发过一个请求，最终显示是半截，也没有提示，判 `accepted_partial`；
   - 其余情况判 `n/a`。
3. 重发请求带着半截（assistant 历史里有半截编号或失败标记）：
   - mock 记录的决定是"续写"，而且最终显示里完整回答的每一段恰好一次、画面完整，判 `continued`；
   - mock 记录的决定是"重写"：最终显示里有重复，或者下一轮请求同时带着半截和完整回答，判 `duplicate`；否则判 `n/a`。这正是"服务端重写、客户端把半截藏起来"的情形，不能判成 `continued`。
4. 重发请求不带半截：
   - 最终显示里还有失败标记，而且完整回答都在，判 `fork`；
   - 交互模式下画面不完整，判 `n/a`。原因是备用屏幕：截到的画面之外，排除不了还留着半截；
   - 最终显示里，完整回答不是每段恰好一次，判 `n/a`；
   - 显示过半截（有由失败标记触发的中途截图，或原始字节里有失败标记），判 `retracted`；
   - 原始字节里也没有失败标记，判 `not_shown`。没有原始字节证人时，判 `n/a`。

五字段映射：
- `not_shown`、`retracted`：detected、contained、recovered；
- `fork`：detected、recovered，contained ✗、reported ✗（最终画面上有提示时，reported 记为 ✓）；
- `continued`：detected、recovered、contained，但成立的前提是"服务端会续写"这个假设；
- `duplicate`：detected、recovered，contained ✗；
- `accepted_partial`：detected ✗、reported ✗；
- `reported_failure`：detected、reported，recovered ✗。

**另外记录（不改变判定）：**
- 中途截图早于重发开始多少毫秒，以及原始字节里失败标记写出的时刻；
- 失败的半截在屏上停留了多长时间（`tag_visible_ms`）；
- 重发期间半截和新回答同时在屏上（重叠截图）；
- 提示原话：从原始字节和逐次截屏里读，带时刻；
- 下一轮请求、会话文件里存了什么；
- 子进程里实际执行的二进制和它的 sha256。

## 复验返工清单 12 条：改在哪

| # | 问题 | 现在的做法 |
|---|---|---|
| 1 | 中途截图的触发和时间对齐 | 由只有失败那次才有的标记触发，每 30 ms 截一次。`mid.json` 记截图时刻，送达日志记每个请求的开始和结束时刻（毫秒，同一个时钟）。另有 `rawtap` 的字节时刻作为第二证人。 |
| 2 | regrade 把最终画面当成中途画面 | `load_observation()` 从各自的文件读：中途画面只读 `mid.txt`，而且要有 `mid.json` 写明是标记触发的；最终画面只读 `final-view.txt`。`regrade` 只追加 `regrade.jsonl`，不改 `runs.jsonl`。有测试覆盖。 |
| 3 | F0 被无条件判成 healthy | 逐项检查（见上），不满足判 `control_failed`；另有阳性对照 F0-tag。 |
| 4 | continued 的判定能被骗 | 要求完整回答的每一段恰好一次（FLONG 要求 L001–L200 全在），画面完整，而且 mock 记录的决定是"续写"。"服务端重写、客户端藏起半截"和"只剩 L161–L200"这两种情况都有对抗测试。 |
| 5 | 提示只看最终画面 | `pipe-pane` 的原始字节每次都录，去掉转义序列后提取提示原话，并对齐到时刻。逐次截屏里出现过的提示也记下来。 |
| 6 | 备用屏幕 | tmux 默认 110×400。画面完整的判据是横幅和 mark 都在最终画面上；FLONG 另截断开前一刻的画面，证明 160 段能同时留在屏上。 |
| 7 | 静默窗口 | 默认 60 秒，下限 40 秒（低于下限会报错），或者用客户端自己的结束状态（重发完成、画面稳定）。 |
| 8 | `stream:false` 消耗一次性故障 | 非流式请求不消耗一次性故障；"每次都断"的模式下，非流式请求也会失败（发完响应头就断开）。 |
| 9 | 控制面和端口 | `/__control` 和 `/__logs` 要带 `x-mock-token`（来自环境变量，不出现在命令行里）。端口默认用临时端口；指定的端口被占就拒绝运行。另外核对实例号和监听进程。 |
| 10 | 哈希的对象 | 哈希实际执行的原生二进制：codex 追到 vendor 目录下的 `codex`。运行时再用 `lsof` 对子进程核对一次。node、mock、夹具和装置本身也都算哈希。 |
| 11 | 原地脱敏 | 证据目录一个字节都不改。`export_public.py` 只在副本上脱敏，前后核对源目录的哈希清单，再跑 `audit_artifacts.py` 和禁用串扫描。 |
| 12 | 测试样例 | `tests/test_stream_retry.py` 包括：判定的对抗样例；mock 的集成测试（令牌、一次性故障、非流式请求、辅助请求、续写的三种分支、标记）；版本证人的 npm 布局；导出不改源目录；对假 TUI 的端到端校准。 |

## 用法

```bash
OUT=<证据目录，放在公开仓库之外>
PE="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:<claude 所在目录>"
python3 witness/stream-retry/runner.py probe  --out "$OUT" --tools claude codex \
  --bin claude=<claude 路径> --bin codex=<codex 路径> --path-env "$PE"
python3 witness/stream-retry/runner.py matrix --out "$OUT" --tools claude codex --runs 3 \
  --bin claude=<claude 路径> --bin codex=<codex 路径> \
  --expect claude=<版本> --expect codex=<版本> --path-env "$PE" --card <实验卡路径>
python3 witness/stream-retry/runner.py summarize --out "$OUT"
python3 witness/stream-retry/runner.py lsregister --out "$OUT"
python3 witness/stream-retry/export_public.py --src "$OUT" --dst runs/<本期目录>
```

### 开跑门槛（`skills/repo-quake/scripts/card_gate.py`）

`matrix` 必须二选一：`--card <实验卡>`，或者 `--exploratory "<理由>"`。两个都不给，或者两个都给，直接拒绝，什么都不写。带卡时，开跑前依次检查：

1. **卡本身**：通过 `validate_card.py`，被 git 跟踪，而且没有未提交的改动。manifest 里记下最后一次改动这张卡的 commit、提交时间，以及这个 commit 是否已经在上游分支上。没推送也能跑，但会在 stderr 警告：commit 时间是自己填的，只有推送才留下实验者改不了的时间。
2. **范围**：`--tools` 的每个名字都要是卡里某个 `hosts[].name`，每个条件都要是某个 `arms[].id`；同一个工具跑的模式数（交互、非交互）不能超过卡里同名 host 的个数。
3. **总预算**：同一个证据目录下、同一张卡（按 sha256 认）之前所有 manifest 的派发数，加上这次最多派发的次数，不能超过 `budget.max_runs`。这一条没有开关：要多跑，就冻结一张新卡。
4. **单格计划**：每一格（工具 × 模式 × 条件）累计次数不能超过卡里的计划次数。判为 `invalid` 的运行，每次可以补跑一次，补跑次数最多是 `sampling.invalid_reruns`（默认 1）乘以计划次数。超出时必须带 `--deviation "<理由>"`，理由会写进 manifest。这样补测是记录在案的偏离，不会悄悄发生。

计数写在 manifest 的 `dispatched` 和 `invalid` 里。每次运行开始前先加一，所以中途死掉的进程也照样记账。门槛出现之前写的旧 manifest 没有计数，按它整个计划算。`--exploratory` 不查卡，但 manifest 会记下 `preregistered: false` 和理由，`summary.md` 也会标成"未预注册"。

## 已知盲区

- **原始字节证明的是"写到了终端"，不是"人看得见多久"。** 如果一次写入在同一帧里就被覆盖，它照样会被算作显示过。停留多久，要看由标记触发的截图和 `tag_visible_ms`；短于截图间隔（约 30–60 ms）的停留截不到。
- **画面完整的判据是"横幅和 mark 都在"。** 如果一个应用会省略对话中间的部分，这个判据就会被骗。本期两个工具的截图里都没有这种省略。
- **mock 的续写是对服务端行为的假设。** 默认用重写（`restart`），续写分支要另外跑。
- **tmux 不是真终端。** 渲染节奏和真实终端（iTerm2、Terminal.app）可能不同。
- **沙箱下工具处于离线状态。** 一个联网时行为不同的客户端（例如会做更新检查），在这里表现的是离线时的行为。
- **只看最终状态。** 判定按最终状态做；中途的重叠作为另外的观察单独记录。

## 第 5 期新增（2026-11-16）

第 5 期用这套装置复测 metacodes、deepseek-harness，复查 9 月交互附录，见 `docs/phase5-report.md`。改动：

| 改动 | 在哪 | 为什么 |
|---|---|---|
| 被测适配器 `metacodes`（TUI 和 `-p`）、`metacodes-json`、`metacodes-sjson`；`dsh-cc`、`dsh-resp`、`dsh-anth` | `runner.py` | metacodes 讲 Anthropic Messages（`--base-url …/v1/messages`）；dsh 每次运行一个新的 `DSH_HOME`，home 层 `cordis.patch.yml` 把默认模型指到 pi-ai 的 mock 路由，`api` 选协议 |
| 新故障 FTHINK1、FTHINK6：只流一段思考（R01–R06，带失败标记），一个字的正文都没有就断开（FIN／干净收尾无终止事件）；F0T：健康回答前先有一段完整、带签名、带标记的思考 | `mock.mjs`（三种方言） | 推理模型先流思考，线上的断流几乎都断在思考里；F0T 是思考的阳性对照 |
| 思考的阳性对照判 `tag_visible` 或 `thinking_hidden`（这个模式从不显示思考，是结果不是失败） | `grading.py` | 否则"没看到思考的标记"说明不了"撤回了" |
| 非交互输出按模式读：`--json` 读结果行的 `text`；`--stream-json` 按协议把 `text`/`thinking` 行归到当时开着的段，`discarded` 段整段丢掉；stdout 里出现过失败标记就算显示过（`emitted`） | `grading.display_of()`，`load_observation()` 从 `stdout.txt` 重新推导 | 结构化输出的"显示"是消费者读到的东西，不是原样的 stdout |
| `reported` 记在所有重发分支的判定上，另记 `checks.notice_where`（final、raw-only、none） | `grading._result()` | 第 4 期只在 fork 上记；要区分"一闪而过""常驻""没有" |
| F4、F5（一次性）走 `_grade_signal`：有没有跟进请求、带没带第一次（`length_continued` / `length_retried`）、提示在哪；提示词表加宽（`SIGNAL_RE`：token、limit、incomplete、truncat、continu、resum、截断、不完整、续写、上限），只用于 F4/F5 | `grading.py` | 长度截断不是断线，客户端的措辞会围绕 token、上限、续写；宽词表在第 4 期 36 次运行上校准过，没有多抓一行 |
| 被测自己固定 UI 里含提示词的行可以排除（`Tool.chrome_re`，随运行记录，regrade 照用） | `runner.py`、`grading.notices(ignore=)` | metacodes 空输入框写着 `Try "fix typecheck errors"`，不排除的话每个健康对照都判失败（试跑发现） |
| mock 的 `aux_match`：被测声明自己辅助请求的特征串，命中的请求记 `aux`、不吃一次性故障 | `mock.mjs`、`Tool.aux_markers` | dsh 的标题请求是纯文本，又带着本次的随机标记 |
| 会话文件：zstd 压缩的 dsh v4 日志、metacodes 的 `blocks`、thinking 块；停止原因认 dsh 的 `reason.kind` | `grading.read_session_text()`、`content_text()`、`stop_reasons_in_file()` | 新被测的存储格式 |

试跑发现、冻结前修好的两处装置缺陷（台账 RQ-I-011、RQ-I-012）：
- codex 的标题请求走 `/v1/responses` 的结构化输出，新加的思考字段在那条路径上没有默认值，mock 崩溃；有回归测试，做过变异检查。
- metacodes 空输入框那行被当成错误提示，见上表。

新的已知盲区：
- FTHINK 的重发是普通回答，没有思考；真实的推理模型会再想一遍。
- `--stream-json` 的读法假设消费者按协议归段；不按协议的消费者看到的是 `emitted`。
- F4 的续写分支没有建模：mock 对续写请求总是从头写，所以"续写之后显示什么"只是 restart 分支下的观察。
