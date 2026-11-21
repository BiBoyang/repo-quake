# repo-quake Phase 6 报告：依赖卡住时，metacodes 在哪里同步等、等多久（2026-11-21）

## 起因

2026-11-20，X 上有一条吐槽 Codex TUI 的推文：“启动卡、发消息卡、ESC 卡”。负责人据此整理了一份 Codex CLI 卡顿根因文档，列了四条：

1. skills 刷新在主循环里内联 await，冻住输入；
2. 启动时等全部 MCP 握手；
3. 退出时同步刷新遥测；
4. 执行命令前做 SHA256 校验。

第二天在 metacodes 上逐条对照：读源码，加上不计数的试跑。结论是：
- 这四条 metacodes 都没有原样照搬；
- 但同一类毛病换了地方出现了：**在不该等的地方同步等一个依赖，而且多数没有自己的时限**。

对照报告在 metacodes 工作区，不在本仓库。

## 这一期做了什么

把对照里实测到的现象，按 repo-quake 的证据标准重做：
- 实验卡在第一次计数运行前冻结；
- 被测用固定版本的发布构建：metacodes 0.13.1-dev+53b3e285，ReleaseSmall，sha256 `ab1f7bdf…af08`，每次启动都用 lsof 核对执行的二进制；
- 21 组，每组 3 次；故障组之前、之后都跑健康对照，另有两个阳性对照；
- 每个故障都由假服务器自己的请求记录证明确实送到了。

全部只连本机回环地址上的假服务器，没有调用任何模型，没有付费请求。被测用 `env -i` 白名单和临时 HOME 启动，`sandbox-exec` 只放行到 localhost 的连接；事后审计，沙箱拦下的外连是 0。

计数矩阵 2026-11-21 17:51–17:56 一次跑完：63 次运行，0 次 invalid，0 次补跑，每组的结果都和卡上的预测一致。

## 头条

| 卡住的依赖 | metacodes 怎么做 | x/N |
|---|---|---|
| 启动时的模型列表 `/v1/models`（本机没有缓存） | 同步等，自己没有时限：对方拖 5 s，输入框就在 5.05 s 出现；对方不回答，35 s 内都不出输入框（Ctrl+C 能退出）。有 24 h 缓存时不等，只在后台刷新 | 等 3/3，卡住 3/3，有缓存不等 3/3 |
| 启动时的本机记忆服务 TinyKG（只收不答） | 等满传输层的 35 s 时限才出输入框，等的时候屏上什么都没有，之后横幅才写 KG unavailable | 3/3（35.05 s） |
| 打出 `/model` 时拉 Metask 账号的 key 列表 | 在读键盘的那条线程上同步拉。对方拖 5 s，`/model` 之后打的字晚 4.59 s 才显示。对方不回答：不回显，Ctrl+C 连按两下无效，SIGTERM 之后要过 45.01 s 才被 45 秒看门狗（SIGALRM）结束 | 冻 3/3，冻到看门狗 3/3 |
| stdio MCP 服务器不回 initialize（启动超时配成 5 s） | 输入框不受影响（0.04–0.05 s）。第一条消息等满启动超时，在启动后 5.37–5.42 s 发出；等的时候 spinner 写着 Connecting to MCP servers；按 Esc 0.14 s 就取消 | 3/3，Esc 3/3 |
| HTTP MCP：退出时结束会话的 DELETE 不回 | 退出没有时限，`/exit` 之后 35 s 内都没退出；Ctrl+C 救不回来 | 3/3 |
| HTTPS MCP：TLS 握手卡住（启动超时配成 5 s） | 5 s 的启动超时不起作用：第一条消息 15 s 内都没发出；按 Esc 能取消这一轮，但 `/exit` 之后 35 s 内都没退出 | 3/3 |
| OTLP 遥测收集端只收不答（导出超时配成 2 s） | 退出等满导出超时，用 2.01–2.02 s | 3/3 |
| 语言服务器从不发诊断（PATH 上一个假 gopls） | 每次 Edit 等满写前 8 s、写后 6 s，一次 Edit 用 14.89–14.94 s；不开 LSP 时是 0.005–0.009 s | 3/3 |
| 无故障：真的 gopls v0.21.1 | 只有第一次 Edit 多等，0.57–0.80 s；第二次 0.004–0.005 s | 3/3 |
| 无故障：Bash 的固定开销 | 每个前台 Bash 至少 0.106–0.114 s。会写文件的命令前后各扫一遍工作区：1 个文件的仓库里比 `echo` 多 0.06–0.08 s；2 万个文件、git 索引过期的仓库里多 0.93–1.08 s | 3/3、3/3 |
| 对照 | 健康 C0 前后各 3/3（输入框 0.04–0.06 s，退出 0.010–0.013 s）；启动动画 3/3（1.54–1.56 s）；5 台 stdio MCP 的退出 3/3（1.03–1.05 s，正好每台 0.2 s）；key 列表马上回答时回显不慢 3/3；不开 LSP 时 Edit 不等 3/3 | |

表里的判定标签只是判分笔记，台账只记五字段：detected、reported、contained、recovered（`ledger/SCHEMA.md`）。这一期怎么读，见“几个词”。样本小：3/3 的单侧 95% Wilson 下界只有 0.53，所以只说“稳定出现”，不说比率。

## 几个词

- **依赖卡住**：被测要用的东西接受了连接，却迟迟不回答，或者一直不回答。这一期造了两种：
  - 拖延回答：5 秒后才回；
  - 只收不答：读走请求，从不回答。
- **输入线程**：metacodes 等你打字时，读键盘、画输入框都由同一条线程做。这条线程被一个网络请求占住时，打的字不显示，Esc 和 Ctrl+C 也不起作用。原因是终端这时处在原始模式，Ctrl+C 只是一个等着被读的字节，不会变成中断信号。
- **缓存未命中**：metacodes 把上一次要到的模型列表存在本机，24 小时内有效。没有，或者过期了，叫未命中。
- **看门狗**：收到 SIGTERM 或 SIGHUP（关终端会发这个）后，metacodes 会定一个 45 秒的闹钟。45 秒内没退干净，闹钟一响，系统直接结束进程。
- **自己的时限**：被测自己给等待划的上限，比如 MCP 的启动超时。“依赖最后回答了”不算被测有时限。
- **detected / reported**：这一期里，detected 指被测自己给等待划了上限，reported 指等待期间屏幕上说了在等什么。
- **L0–L3**：
  - L0：没信号，也没上限；
  - L1：有上限但不说，或者说了一句泛泛的“忙”但没有上限；
  - L2：说了在等哪个依赖，但没有上限；
  - L3：说了在等什么，有上限，还能继续或者能被打断。

  完整的对应表在 `witness/stall/README.md`。

## 装置（`witness/stall/`）

- **伪终端驱动**（`fakes.Pty`）：给每一块输出、每一次按键记下单调时钟的时刻。它像一个不支持 Kitty 键盘协议的终端那样回答 DA1 查询。
- **假服务器**：
  - `Gateway`：Anthropic Messages 网关。`/v1/models` 和 key 列表可以拖延或永不回答；`/v1/messages` 按脚本回放，可以带 tool_use。
  - `Silent`：只收不答。
  - `ClassicMcp`：带会话的 Streamable HTTP MCP，DELETE 可以永不回答。

  它们都是执行器进程里的线程，监听回环地址的临时端口，按单调时钟记下收到的请求和连接，这就是送达证明。
- **辅助进程**：
  - 永不回答的 stdio MCP；
  - 马上回答的 stdio MCP；
  - 从不发诊断的语言服务器。

  每次运行前复制进那次运行自己的目录，改成 `a.py`、`b.py`、`c.py` 这种不含故障类型的名字。
- **判定**：冻结在 `stall.py` 里，规则写在 README（判定）。开跑门槛直接用 `card_gate.py`（当时在 `witness/stream-retry/`，2026-11-21 起在 `skills/repo-quake/scripts/`）：
  - 卡片要通过校验、已经提交；
  - 预算要覆盖这次矩阵；
  - 每一格不能超过计划次数。
- **时钟校准**：`tests/test_stall.py` 用一个假 TUI 校准两把时钟。
  - 启动推迟 1.0 s，读回 1.0–1.6 s；
  - 输入线程停 2.0 s，读回 1.6–2.5 s 的回显延迟。

  `bash tests/run_tests.sh` 全部通过。
- **三处故意配小的地方**，卡片里写明了：
  - MCP 启动超时配 5 s（默认 30 s）；
  - OTLP 导出超时配 2 s（默认 10 s）；
  - “一直卡住”的组只等 35 s，结论写成“35 s 内没有恢复”。

  默认值来自源码，也有试跑数字：默认 30 s 时第一条消息等了 29.28 s，默认 10 s 时退出用了 10.02 s。

## 逐组看

### 启动

- **`S-models-5s`**：
  - 输入框 5.053、5.045、5.049 s 出现；
  - `/v1/models` 请求在启动后 0.02–0.03 s 就发出了；
  - 也就是说，`App.init` 在缓存未命中时同步等它（`src/app.zig:1149-1155`，`loadModelCatalog` 在 `2494-2532`），请求本身没有任何时限（`src/client.zig:1606-1650`）。
- **`S-models-stall`**：35 s 内都没出现输入框；按一次 Ctrl+C，进程 0.01 s 就退出了。这时终端还在正常模式，Ctrl+C 能变成中断信号。
- **`S-models-warm`**：
  - 先用健康网关启动一次，把缓存填上，第二次启动时输入框 0.040–0.045 s 出现；
  - 第二次启动照样发了 `/v1/models` 请求，那是后台刷新，不挡输入框；
  - 这一组证明：故障只在缓存未命中的路径上挡路。
- **`S-kg-stall`**：
  - 输入框 35.057、35.045、35.050 s 出现；
  - 假 KG 端口在启动后 0.02–0.03 s 被连上；
  - 35 s 正是 KG Web 传输的默认时限（`src/kg/transport.zig:22`）。`initKg`（`src/app.zig:4692-4740`）在 `App.init` 里同步运行，函数注释自己写着“P2 待办：移到后台线程（锁竞争最坏 35s）”；
  - 等的时候屏上什么都没有，之后横幅才写 `KG unavailable`（3/3）。

### 输入框

- **`K-keys-5s`**：
  - key 列表请求在 `l` 敲下后 0–6 ms 内发出；
  - `zq` 的回显晚了 4.589、4.592、4.596 s，也就是 5 s 减去从 `l` 到 `q` 的 0.4 s；
  - 代码路径：输入框的重画函数（`src/repl/loop.zig:1943-1951`）看到草稿是 `/model` 或 `/models`，就调 `ensureApiKeyCatalog`（`src/app.zig:2435-2462`），它在输入线程上发一个没有时限的 GET（`src/api/api_keys.zig:187-217`）。
- **`K-keys-stall`**：
  - 3/3 没有回显；
  - Ctrl+C 连按两下后，5 s 还活着；
  - SIGTERM 之后 45.012、45.014、45.012 s 才结束，结束它的信号是 SIGALRM（信号 14），也就是看门狗（`src/app.zig:5936, 5944-5955`）。
- **`K-keys-0s`（阴性对照）**：回显在按键后 1 ms 内出现，3/3。

### MCP

- **`M-stdio-stall`**：
  - 输入框 0.04–0.05 s 出现；
  - 回车后约 0.1 s，spinner 写出 `Connecting to MCP servers`；
  - 请求在启动后 5.372、5.370、5.419 s 发出，正好是配的 5 s 启动超时；
  - 启动超时从进程启动就开始算，所以从回车算只有 4.45 s 左右。
- **`M-stdio-stall-esc`**：Esc 后 0.142–0.145 s 显示 `Interrupted`，这一轮取消，之后网关没收到请求。
- **`M-http-delete-stall`**：
  - 握手、跑一轮都正常；
  - `/exit` 之后 DELETE 马上到了服务器，35 s 内进程都没退出；
  - Ctrl+C 连按两下，5 s 后还活着。

  代码：关闭时的 `deleteSession`（`src/mcp/transport_http.zig:421-434`）没有登记中断，也没有时限；`App.deinit` 逐台关闭（`src/app.zig:2378-2384`）。
- **`M-https-tls-stall`**：
  - 假端口在启动后 0.02–0.05 s 被连上，收到 1,609 字节的握手数据，从不回答；
  - 第一条消息 15 s 内没发出，而启动超时配的是 5 s；
  - Esc 0.14 s 取消这一轮；
  - `/exit` 之后 35 s 内没退出。

  代码：`openMethod` 先在 `client.request(...)` 里做 DNS、TCP、TLS，之后才 `registerMonitored` 登记中断和时限（`src/mcp/transport_http.zig:560-575`）。所以连接阶段不受启动超时和中断管；退出时 `cancelAndJoin` 要等这个卡住的线程。

### 退出

- **`E-otlp-stall`**：
  - 收集端在启动后约 1.8 s 被连上，也就是导出线程开始发这一轮的轨迹；
  - 退出用 2.010、2.012、2.021 s，等满导出超时（`src/telemetry/exporter.zig:128-133`，默认值在 `src/telemetry/config.zig:43`）。
- **`P-stdio5-exit`（阳性对照）**：
  - 5 台马上回答的 stdio MCP，退出用 1.045、1.032、1.029 s；
  - 原因是关闭 stdio 子进程时先 SIGTERM，再固定睡 200 ms（`src/platform/process.zig:452-469`），逐台进行；
  - 这一组既证明退出时钟量得准，本身也是一个固定开销：10 台 MCP 就是 2 秒。

### 工具调用

- **`T-edit-silent-lsp`**：Edit 的间隔 14.892、14.911、14.939 s。

  来历：写前等 8 s、写后等 6 s（`src/lsp/service.zig:34-35`），按 150 ms 一步轮询还要多走一步。调用点在 `src/tools/edit.zig:367, 390, 450`。
- **`T-edit-gopls`**：
  - 第一次 Edit 0.682、0.570、0.804 s，付的是 gopls 启动和第一次诊断；
  - 第二次 0.004–0.005 s。
- **`T-edit-nolsp`（阴性对照）**：0.005–0.009 s。
- **`T-bash-mixed-1`**：
  - `echo` 每次 0.108–0.114 s：等命令结束的循环先睡 100 ms 再看（`src/tools/bash.zig:910-916`）；
  - `touch` 第一次 0.17–0.51 s，之后 0.166–0.195 s。
- **`T-bash-mixed-20k`**：
  - `echo` 每次 0.106–0.128 s；
  - `touch` 第一次 2.39–2.43 s，之后 0.85–1.19 s；
  - 中位数之差 0.925、1.081、0.976 s。

  会写文件的命令前后各拍一次工作区快照：`rg --files`、逐个 lstat、`git status`（`src/core/command_file_changes.zig:52-58, 771` 起）。

### 意外：索引过期时，每次观察都要重算整个工作树的哈希

`T-bash-mixed-20k` 的差值（约 1 s）比试跑时大得多：试跑时仓库是原地生成的，差值约 0.24 s。原因在夹具，但它暴露了一个真实的性能陷阱：

- **夹具的问题**：这一期每次运行的仓库，都是用 `cp -cR` 从模板复制出来的。复制出来的文件 inode、ctime 都变了，所以 git 索引里记的文件属性都过期了。
- **metacodes 的做法**：观察文件变化时跑的是 `git --no-optional-locks status --porcelain=v2 -z --untracked-files=all`。`--no-optional-locks` 不让 git 把刷新后的索引写回去，所以只要索引一直是过期的，每次观察都要把整个工作树重新算一遍哈希。
- **冻结后在模板的一份复制上核对过（不计数）**：
  - 刷新前两次 `git status` 用了 5.82 s 和 1.09 s；
  - `git update-index --refresh` 之后是 0.05 s 和 0.04 s。

现实里，索引过期的情况包括：复制或同步过的仓库、构建工具重写过大量文件的时间戳、挂载进容器的工作区。用户自己在这样的仓库里跑一次 `git status` 就会把索引刷新；但只要没人刷新，metacodes 里每一个会写文件的 Bash 命令都要多付这笔钱。判定 `observation_paid`（门槛 ≥ 0.15 s）不受夹具影响，但这一组的大小要按“索引过期”这个条件来读。偏离日志里记了这一条，台账见 RQ-X-016。

## 和 Codex 那份根因文档对照

| Codex 根因 | metacodes | 本期证据 |
|---|---|---|
| 1. 主循环内联等 skills 刷新，冻住输入 | 没有 skills 刷新这件事。但同型缺陷换了地方出现：打出 `/model` 时，输入线程同步等 key 列表 | `K-keys-5s`、`K-keys-stall` |
| 2. 启动时 join_all 等全部 MCP | MCP 不挡输入框，挡的是第一条消息，有上限、有提示、能 Esc。启动时另有两处同步等待：`/v1/models` 和 TinyKG；HTTPS 的握手阶段不受上限管 | `M-stdio-*`、`S-*`、`M-https-tls-stall` |
| 3. 退出时同步刷新遥测 | 遥测默认关；开了且收集端不回时，等满导出超时（Codex 新版是 0.5 s）。另有两处退出等待：HTTP MCP 的 DELETE 没有时限，stdio MCP 每台 0.2 s | `E-otlp-stall`、`M-http-delete-stall`、`P-stdio5-exit` |
| 4. 执行前 SHA256 | 默认路径上没有二进制哈希（沙箱默认关）。固定开销在别处：Bash 至少 0.1 s、工作区扫描、LSP 诊断等待 | `T-*` |

## 诚实清单

- **试跑和冒烟。** 冻结前一共 46 + 23 次，都没计入；卡上的预测参考了它们，卡里写明了。冒烟时发现并改好三处证人的错：MCP 等待的起点、夹具 git 的后台打包、SIGSTOP 阳性对照。详见披露的第 3 节。
- **配小的超时、截断的等待。** 见“装置”。“没有时限”这个结论来自源码；矩阵能证明的是“配的时限没起作用”“35 s 内没有恢复”。
- **夹具的索引过期。** 见上一节。
- **伪终端不是真终端。** 只回答 DA1，被测用老式键盘编码。`/model` 那一格试跑时在 tmux 3.5a 里截屏复核过一次：打完 `/model abc` 2 s 后，屏上还停在 `❯ /mode`，8.11 s 后才出现。
- **故障只有两种形态：** 接了连接却不回、回得慢。丢 SYN、路由黑洞、DNS 卡住在回环上造不出来。DNS 那条读的是 Zig 0.16 标准库的源码：macOS 上用阻塞的 `getaddrinfo`，取消不了。
- **只测了交互式 TUI，只在 macOS 上。** `-p`、`serve`、`--web` 和 C ABI 宿主没测。
- **并行。** 等待型的组 5 个一起跑。这台机器上同时还有别的会话在跑构建和测试套件，负载 5–7。亚秒级判定的组（K-keys-0s、T-*）在等待组之后单独跑。
- **没测的源码结论。** 下面三条只读了代码，没有放进矩阵：
  - 生成期的 KG 召回不看 Esc（`src/kg/client.zig:3074` 只把中断接到命令行子进程那条路径）；
  - `/models` 里选中一个 key 时，在输入线程上同步重新探测 `/v1/models`（`src/app.zig:3751-3780`）；
  - Metask 设备会话每次启动都同步拉模型目录、不走缓存（`src/app.zig:1084-1125`）。
- **被测路径在跑矩阵时没变。** 跑矩阵时 upstream/main 是 `de9193ac`。从 53b3e285 到它，这些路径上的文件只有 `src/repl/loop.zig` 改过，改的是粘贴处理（#649/#650、#657），不在本期测的代码路径上。

## 上游与还没做的

- **metacodes 的 issue 已提（2026-11-21，不指派）**：
  - [#666](https://github.com/metask-ai/metacodes/issues/666)：启动时等 `/v1/models`；
  - [#667](https://github.com/metask-ai/metacodes/issues/667)：TinyKG 35 s；
  - [#668](https://github.com/metask-ai/metacodes/issues/668)：`/model` 冻住输入框；
  - [#669](https://github.com/metask-ai/metacodes/issues/669)：LSP 诊断等待；
  - [#670](https://github.com/metask-ai/metacodes/issues/670)：Bash 固定开销和索引过期；
  - [#671](https://github.com/metask-ai/metacodes/issues/671)：HTTP MCP 的 DELETE 和 HTTPS 握手；
  - [#672](https://github.com/metask-ai/metacodes/issues/672)：OTLP 退出等待。

  这 7 个都读回核对过：标题、正文与草稿逐字一致，标签正确，没有指派。正文里的复现步骤不依赖本仓库，也不依赖本机路径（posting gate：公开的仓库要先于引用它的 issue；这里反过来，issue 不引用本仓库）。台账 RQ-F-025 至 RQ-F-031 已改成 reported。RQ-F-032（第一条消息等 MCP）是有意的取舍，没有单独上报；关闭时每台 200 ms 的固定睡眠写进了 #671 的附带建议。
- **推送。** 2026-11-21 经负责人同意，master 快进到本期的提交，然后推送。本文件在推送前定稿，推送后的本地与远端 SHA 核对不在这里，按 `reporting.md` 在推送之后单独做。实验卡是在开跑之后才推送的，所以冻结时间只由本地提交担保：`manifest` 里 `card.pushed` 是 null。
- **跨程序附录**（以后再说）：用同样的假服务器，跑 Claude Code 和 codex 的几种通用场景：挂住的 stdio MCP、不回的 DELETE、握手卡住、不回的收集端、每次工具调用的固定开销。

## 证据

- 公开副本（`stall.py export` 导出，`audit_artifacts.py` 审计通过）：`runs/phase6-metacodes-stall-2026-11-21/`。终端原始字节、调试日志、临时 HOME 没有公开，见那里的 `EXPORT.md`。
- 实验卡（冻结）：`examples/experiment-card-phase6-metacodes-stall.json`（sha256 `752ef537…cb77`，与证据里的 `card-frozen.json` 逐字节相同）。
- 装置与测试：`witness/stall/`、`tests/test_stall.py`、`tests/fixtures/stall/fake_subject.py`。
- 方法：`skills/repo-quake/references/fault-catalog.md` 新增 §stall。
- 披露：`docs/phase6-disclosure.md`。
- 台账：`ledger/ledger.json` 的 RQ-F-025 至 RQ-F-032、RQ-X-016。
