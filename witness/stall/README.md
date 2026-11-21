# witness/stall：依赖卡住时，CLI 在等什么、等多久

要回答的问题：一个交互式 CLI 依赖的东西接了连接却不回答，或者回答得很慢时，它会不会把输入框、启动、退出或者一次工具调用一起卡住；能不能自己划出等待的上限；等待期间屏幕上说没说在等什么。

依赖包括模型网关、MCP 服务器、本机记忆服务、遥测收集端、语言服务器。

这是 repo-quake 第 6 期的装置。起点是 2026-11-21 对照 Codex CLI 卡顿根因时写的探针（metacodes 工作区 `.verify/codex-lag-check/probe/lagprobe.py`）。那批运行是试跑，不计数，卡片里写明了。

## 文件

| 文件 | 作用 |
|---|---|
| `fakes.py` | 只监听回环地址的假服务器，和带时间戳的伪终端驱动。假服务器有三种：`Gateway`（Anthropic Messages 网关，`/v1/models` 和账号 key 列表都可以按参数拖延或永不回答，`/v1/messages` 按脚本回放流式回答，可以带 tool_use）；`Silent`（接受 TCP 连接、读走数据、从不回答）；`ClassicMcp`（带 `MCP-Session-Id` 的 Streamable HTTP MCP 服务器，可以设成 DELETE 永不回答）。每个服务器都按单调时钟记下收到的请求，这就是故障的送达证明。`Pty` 在伪终端里启动被测程序，给每一块输出和每一次按键记下时刻，并像一个不支持 Kitty 键盘协议的终端那样回答 DA1 查询。 |
| `stall.py` | 执行器：`probe`、`matrix`、`summarize`、`egress`、`lsregister`、`export`。 |
| `srv/` | 被测程序会拉起的辅助进程：永不回答的 stdio MCP 服务器（`quiet_mcp.py`）、马上回答的 stdio MCP 服务器（`ok_mcp.py`）、从不发诊断的语言服务器（`quiet_lsp.py`）。每次运行前复制进这次运行自己的目录，改成不含故障类型的名字（`a.py`、`b.py`、`c.py`）。 |

测试在 `tests/test_stall.py`，`tests/run_tests.sh` 会自动发现它。校准用的假 TUI 在 `tests/fixtures/stall/fake_subject.py`：它按参数推迟画输入框，或者在草稿变成某个字符串时停住若干秒再回显。测试用它证明两把时钟读得回已知的延迟：一把是“启动到输入框”，一把是“输入线程被卡住时的回显延迟”。

开跑门槛直接用 `witness/stream-retry/card_gate.py`（见 `skills/repo-quake/references/experiment-card.md`“开跑门槛”）：卡片要通过校验、已经提交，计划和预算要覆盖这次矩阵。

## 一次运行做什么

1. **准备目录。** 每次运行在证据根下建一个新目录 `runs/<组>/run-<序号>-<随机号>/`，里面有新的 `home/`、`state/`、`work/`、`srv/`。
2. **起假服务器。** 端口用 0，也就是临时端口。服务器都是执行器进程里的线程，所以不存在“端口被别人占了、却误用了别人的服务器”这种情况。
3. **启动被测程序。** 用 `env -i` 白名单启动，套 `sandbox-exec`，配置文件只放行到 localhost 的出站连接。白名单包括：PATH、TERM、LANG、新的 HOME、`METASK_API_KEY=dummy`、`METACODES_KG_AUTOSTART=0`、`METACODES_JEV_URL=off`、`METACODES_NO_STARTUP_ANIMATION=1`、`RG_BIN`。各组自己的变量另加或去掉。命令行是 `--state-dir <run>/state --permission bypassPermissions --base-url <网关>`。
4. **核对执行的二进制。** 启动后用 `lsof` 轮询被测进程，最多 3 秒，直到它的可执行文件正是钉住的那个二进制。对不上就判 `invalid`。
5. **按组的脚本操作。** 见下表。所有等待都有上限，不会无限等。
6. **记录。** 下面这些留在证据根里，不公开：终端原始字节 `raw.bin`、每块的到达时刻 `raw-index.jsonl`、每次按键 `writes.jsonl`、被测程序的调试日志 `subject.log`。假服务器的请求记录和由这些得出的数字，写进 `record.json` 和 `runs.jsonl`。

## 各组：做什么、怎么判（冻结的 rubric）

时间都从 fork 被测程序那一刻算起。“输入框”指屏上出现空输入框的占位文字 `Try "fix typecheck errors"`。“一轮”指输入 `hi`、回车，网关回答 `pong-ok`。“退出”指 Ctrl+U、输入 `/exit`、回车，从回车算到进程结束。

**对照组（先跑，三组都过了才跑故障组；最后再跑一次健康对照）**

| 组 | 做什么 | 通过条件 |
|---|---|---|
| `C0-pre`、`C0-post` | 健康网关，跑一轮再退出 | 判 `healthy`。要同时满足：输入框 ≤ 2.0 s；回车后 ≤ 3.0 s 出现回答；退出 ≤ 1.0 s；恰好 1 次 `/v1/models` 请求、1 次 `/v1/messages` 请求。否则判 `control_failed` |
| `P-splash`（阳性，启动时钟） | 打开启动动画（已知 1.5 s） | 判 `startup_floor_seen`：输入框在 1.4–3.5 s 之间出现 |
| `P-stdio5-exit`（阳性，退出时钟） | 配 5 台马上回答的 stdio MCP 服务器，跑一轮再退出。已知每台关闭时固定睡 200 ms，逐台进行 | 判 `exit_paid_per_server`：退出在 0.95–2.0 s 之间 |

**故障组**

| 组 | 卡住的依赖 | 做什么 | 判定 |
|---|---|---|---|
| `S-models-5s` | `/v1/models` 5 s 后才回答，没有缓存 | 只看启动 | `startup_waited`：输入框在 5.0–7.0 s 之间出现；否则 `other` |
| `S-models-stall` | `/v1/models` 永不回答 | 等输入框最多 35 s，然后按一次 Ctrl+C | `startup_blocked`：35 s 内没出现输入框（另记 Ctrl+C 后多久退出） |
| `S-models-warm` | 先用健康网关启动一次，把缓存填上；再让 `/v1/models` 5 s 后才回答，第二次启动 | 只看第二次启动 | `no_wait`：输入框 < 2.0 s，并且网关收到了后台刷新请求 |
| `S-kg-stall` | 本机记忆服务（TinyKG）：用 `METACODES_KG_URL` 等三个变量指向一个只收不答的端口 | 等输入框最多 45 s | `startup_waited_kg`：输入框在 34.0–40.0 s 之间出现，并且那个端口确实被连过 |
| `K-keys-0s`（阴性） | 账号 key 列表马上回答（`METACODE_API_KEYS_URL` 指向网关） | 逐字打 `/mode`，0.4 s 后打 `l`，0.3 s 后打 ` zq`；记 `q` 敲下到 `zq` 上屏的时间 | `responsive`：< 0.5 s；否则 `control_failed` |
| `K-keys-5s` | key 列表 5 s 后才回答 | 同上 | `prompt_frozen`：回显延迟 ≥ 4.0 s |
| `K-keys-stall` | key 列表永不回答 | 同上；3 s 内没回显的话，连按两下 Ctrl+C，等 5 s；还活着就发 SIGTERM，最多等 60 s | `frozen_until_watchdog`：同时满足四条：没有回显；Ctrl+C 后 5 s 还活着；SIGTERM 后 44–50 s 才结束；结束它的信号是 SIGALRM |
| `M-stdio-stall` | 一台永不回答 initialize 的 stdio MCP 服务器，`startupTimeoutMs` 配 5000 | 输入框出现后发一轮；记网关收到 `/v1/messages` 的时刻（从启动算起，MCP 的启动超时也从启动算起） | `first_message_waited_timeout`：请求在启动后 5.0–8.0 s 之间到达，并且输入框 < 2.0 s（另记 spinner 有没有写 `Connecting to MCP servers`） |
| `M-stdio-stall-esc` | 同上 | 回车 1.5 s 后按 Esc | `interruptible`：Esc 后 ≤ 1.0 s 出现 `Interrupted`，之后 2 s 内网关没收到请求 |
| `M-http-delete-stall` | 一台 HTTP MCP 服务器，正常握手，只有结束会话的 DELETE 永不回答 | 跑一轮再退出，退出最多等 35 s；没退出的话连按两下 Ctrl+C，再等 5 s | `exit_blocked`：35 s 内没退出，并且服务器收到了 DELETE |
| `M-https-tls-stall` | 一个 `https://` 地址指向只收不答的端口（TLS 握手卡住），`startupTimeoutMs` 配 5000 | 发一轮，等 15 s；按 Esc；再退出，最多等 35 s | `unbounded`：15 s 内网关没收到请求，并且 35 s 内没退出 |
| `E-otlp-stall` | 遥测收集端只收不答，`OTEL_EXPORTER_OTLP_TIMEOUT=2000` | 跑一轮，0.2 s 后退出 | `exit_waited_export`：退出在 1.5–4.0 s 之间，并且收集端确实被连过 |
| `T-edit-silent-lsp` | PATH 最前面放一个从不发诊断的 `gopls` | 临时 git 仓库里有 `go.mod`、`main.go`；脚本化的回答先 Read 一次，再 Edit 一次；记两次模型请求之间的间隔 | `edit_waited_both_limits`：Edit 的间隔在 13.5–17.0 s 之间 |
| `T-edit-nolsp`（阴性） | 同上，但加 `--no-lsp` | 同上 | `no_wait`：Edit 的间隔 < 0.3 s；否则 `control_failed` |
| `T-edit-gopls` | 真的 gopls（版本和 sha256 记在 versions 里） | Read 一次，再 Edit 两次 | `first_edit_pays`：第一次 Edit ≥ 0.3 s，第二次 < 0.3 s |
| `T-bash-mixed-1` | 无（只量固定开销），1 个文件的 git 仓库 | 脚本化的回答依次跑 `echo`、`touch`、`echo`、`touch`、`echo`、`touch` | `floor_seen`：六次间隔里最小的 ≥ 0.10 s |
| `T-bash-mixed-20k` | 无，20,000 个文件的 git 仓库 | 同上 | `observation_paid`：`touch` 间隔的中位数减 `echo` 间隔的中位数 ≥ 0.15 s，并且 `echo` 最小间隔 ≥ 0.10 s |

`invalid`（不进任何分母）的情况：
- 按组要求必须出现的输入框没出现；
- 钉住的二进制不是被测进程的可执行文件；
- 故障没送到，也就是假服务器没收到应收的请求或连接；
- 脚本化的工具调用没有跑完；
- 执行器异常。

每个 invalid 最多补跑一次。

## 五字段和等级（冻结）

台账只记五字段里有证据的那几个（`ledger/SCHEMA.md`）。这一期这样读：

- **detected**：产品自己给等待划了上限，也就是它自己的超时到点了，或者它不等这个依赖了。等到依赖自己回答、或者一直等下去，都不算。
- **reported**：等待**期间**屏幕上说了在等什么。事后才出现的提示不算。
- **contained**：等待没有挡住与它无关的操作，比如输入框照常可用。
- **recovered**：这次运行之后，会话或进程正常结束、可以继续用。

等级沿用 `SKILL.md` 的 L0–L3，按卡住的依赖来读：
- L0：没有任何信号，也没有上限；
- L1：有上限，但等待期间什么都不说；或者有一个泛泛的“忙”的信号，却没有上限；
- L2：说出了在等哪个依赖，但没有上限；
- L3：说出了在等什么，并且有上限、能继续，或者能被打断。

| 判定 | detected | reported | contained | recovered | 等级 |
|---|---|---|---|---|---|
| `startup_waited` | 否 | 否 | 否 | 是 | L0 |
| `startup_blocked` | 否 | 否 | 否 | 否 | L0 |
| `startup_waited_kg` | 是 | 否 | 否 | 是 | L1 |
| `prompt_frozen` | 否 | 否 | 否 | 是 | L0 |
| `frozen_until_watchdog` | 否 | 否 | 否 | 否 | L0 |
| `first_message_waited_timeout` | 是 | 是 | 是 | 是 | L3 |
| `interruptible` | 是 | 是 | 是 | 是 | L3 |
| `exit_blocked` | 否 | 否 | 否 | 否 | L0 |
| `unbounded` | 否 | 是 | 否 | 否 | L1 |
| `exit_waited_export` | 是 | 否 | 否 | 是 | L1 |
| `edit_waited_both_limits` | 是 | 否 | 否 | 是 | L1 |

对照组的判定（`healthy`、`startup_floor_seen`、`exit_paid_per_server`、`responsive`、`no_wait`）和只量固定开销的判定（`first_edit_pays`、`floor_seen`、`observation_paid`），不进五字段。

## 证人看不到的（盲区）

- **伪终端不是真终端。** 驱动只回答 DA1，所以被测程序用的是老式键盘编码。在真终端里，启动时的终端探测会更快结束，键盘协议也可能不同。`/model` 那一格另外在 tmux 3.5a 里截屏复核过一次（试跑，不计数）。
- **“出现在终端字节里”不等于“人看得见”。** 时钟读的是字节到达的时刻，不是屏幕重画完成的时刻。
- **假服务器只模拟“接了连接却不回”和“回得慢”两种卡法。** 没测“连接被丢弃”（SYN 无应答）和 DNS 卡住：这两种在回环上造不出来。DNS 那一条只读了代码。
- **网关永远马上回答 `/v1/messages`。** 真实服务端的流式时序不在这里。
- **调大超时、调小上限都有改变结论的风险。** 卡片里写了每处为什么这样配：MCP 启动超时和 OTLP 超时配小了，默认值来自代码；“一直卡住”的组只等 35 s，结论写成“35 s 内没有恢复”。
- **只测了交互式 TUI。** `-p`、`serve`、`--web` 和 C ABI 宿主没测。
- **只在 macOS 上测过。**

## 怎么跑

```bash
python3 witness/stall/stall.py probe  --out EVIDENCE --bin BIN --rg RG --gopls GOPLS
python3 witness/stall/stall.py matrix --out EVIDENCE --bin BIN --rg RG --gopls GOPLS \
    --card examples/experiment-card-phase6-metacodes-stall.json --runs 3 --parallel 5
python3 witness/stall/stall.py summarize --out EVIDENCE
python3 witness/stall/stall.py egress --out EVIDENCE --start "…" --end "…"
python3 witness/stall/stall.py lsregister --out EVIDENCE
python3 witness/stall/stall.py export --src EVIDENCE --dst runs/<phase-dir>
```

`EVIDENCE` 放在仓库外面，`export` 只把可公开的部分复制进仓库，在副本上脱敏，再用 `skills/repo-quake/scripts/audit_artifacts.py` 审计。
