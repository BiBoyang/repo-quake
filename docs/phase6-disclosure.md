# DISCLOSURE — phase6：依赖卡住时 metacodes 的同步等待（2026-11-21）

按 `skills/repo-quake/references/disclosure-template.md` 填写，配合 `docs/phase6-report.md`。

**估计还是官方测量。** 本期每个数字都属于（a）类：自己的运行里直接观察到的。没有官方或组织方的测量可以对照。

## 1. 接触面

- **碰过的：**
  - metacodes：在 metacodes 克隆的一个 detached worktree（upstream/main `53b3e285`）里，经全机重活锁用 `zig build -Doptimize=ReleaseSmall --prefix <仓库外目录>` 构建。克隆的检出、分支、文件都没有动；只 `git fetch upstream main` 更新了远端跟踪引用，用来核对跑矩阵时 main 有没有动过被测路径上的代码。
  - 本机已安装的 gopls v0.21.1、go、python3、git：只运行，没有改。
  - GitHub 上 metask-ai/metacodes 的 issue 列表、标签：只读查询。
- **没碰过的：**
  - 任何真实的模型端点、MCP 服务器、遥测收集端、记忆服务。被测只用 `METASK_API_KEY=dummy`，没有任何真实凭据。
  - 用户真实的 `~/.metacodes`、`~/.claude`、`~/.codex`：每次运行都是证据根里新建的临时 HOME、状态目录和工作目录。
  - 除上面的 7 个 issue 外，任何上游写入：没有发评论或 PR，没有指派、没有加标签以外的改动。
- **隔离：** `env -i` 白名单启动；`sandbox-exec` 配置只放行到 localhost 的出站连接（`loopback.sb`，sha256 见下表）；假服务器都是执行器进程里的线程，监听回环地址的临时端口。被测会拉起的辅助脚本，每次复制进那次运行自己的目录，改成不含故障类型的名字。
- **事后审计：** 沙箱拦下的外连、LaunchServices 登记，见第 4 节。

## 2. 哈希清单

| 对象 | sha256 / 版本 | 说明 |
|---|---|---|
| metacodes 0.13.1-dev+53b3e2857ae3 | `ab1f7bdf4c3e57168dce57ccfef0d981384994977f5d850c4006e3d64343af08` | upstream/main `53b3e2857ae3b8c539ab974a02652087e25cb6df`，zig 0.16.0，ReleaseSmall，layout development；每次启动 lsof 核对 66/66 一致（63 次运行，`S-models-warm` 每次启动两回） |
| ripgrep 15.2.0（构建时放在二进制旁边的那份，`RG_BIN`） | `a326a1fb48074202e9ad41e4cd1e389eeea372c8c6f7d7e80da81176d5d9430e` | 与 metacodes `--version` 里写的期望值相同 |
| gopls v0.21.1 | `6c4297a35573a2b7c4a2c1e63636bf5adb6c5ea35d2839971a73dbcda97d4b7c` | 只有 `T-edit-gopls` 用 |
| go 1.25.6 | `cd864b57eef970002eadd9d4f35ce4026265d3fe7f4c030a8b5d69373f9a4bc2` | gopls 调用 |
| python | 3.14.7 | 执行器与辅助进程 |
| `witness/stall/stall.py` | `2b816465ae85edd1d0dee0f161ac0ff2b2a70ea517f36466cec04968697f4317` | `frozen-sha256.txt`，矩阵前后一致 |
| `witness/stall/fakes.py` | `d4cf565d20b658e35f58cc71d96355dc99ea2a7c3e57cdacbe679a555b2981e6` | 同上 |
| `witness/stall/srv/quiet_mcp.py`、`ok_mcp.py`、`quiet_lsp.py` | `319721c5…688f`、`4199683d…4317`、`4aa72bfb…92d0` | 同上 |
| 沙箱配置 `loopback.sb` | `0e50c559fe8a054a0f02351576f95a568a773f013980bf2a68a730b527448852` | 只放行到 localhost 的出站连接 |
| 实验卡 | `752ef5374a0cad419a49504fb962209512a4407300e480700e8506f7cb78cb77` | 证据里的 `card-frozen.json` 与 `examples/` 里的逐字节相同 |
| 键入的提示词 | `8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4` | 每一轮都只打两个字节 `hi`；工具调用全部由脚本化的网关决定 |
| 卡片校验器 `validate_card.py` | `1ab2a829a294b3d14b98030b2e18ab404ddb279b9eb619e0719b7ce50baff0b7` | 记在 manifest 的 `accounting` 里 |

矩阵前后各记一次版本和哈希，被测二进制、ripgrep、证人文件都一致（`versions-before-*.json`、`versions-after-*.json`、`manifest-*.json` 的 `subject_sha256_unchanged`、`witness_unchanged` 都是 true）。

## 3. 预注册与偏离

**预注册。** 实验卡 `examples/experiment-card-phase6-metacodes-stall.json` 在第一次计数运行前冻结，提交为 `3ec9c31`。提交在本地分支 `feat/phase6-stall` 上，开跑时没有推送，所以执行器记了一条警告：冻结时间只由本地提交担保（`manifest-*.json` 的 `card.pushed`）。证人 `witness/stall` 在同一分支的 `a870152` 提交，开跑时的文件哈希写进了 `frozen-sha256.txt`。

**冻结前的试跑（不计入）：**
- 2026-11-21 16:30–17:05，用同一提交的 Debug 构建和一个更早的探针，共 46 次。结果写在 metacodes 工作区的对照报告里。
- 2026-11-21 17:4x，用本期证人对 Debug 构建做冒烟，共 23 次。冒烟里发现三处证人自己的错，都在冻结前改好：
  1. MCP 那组的等待原先从回车算起，但 metacodes 的 MCP 启动超时从进程启动就开始计时，所以测出来少了 0.6 s。改成从启动算。
  2. 2 万文件的夹具仓库，在 git 提交后被后台自动打包；复制夹具时，对象目录正好被删掉，`cp` 失败。夹具改成 `gc.auto=0`。
  3. 原定的输入框阳性对照，做法是在打字时用 SIGSTOP 把被测停住 3 秒。这条行不通：metacodes 收到 SIGCONT 后会重新进入原始模式，把停住期间打的字全部丢掉，这是 #326 的做法。改用“5 台 stdio MCP 的退出耗时”当退出时钟的阳性对照，回显时钟改由 `tests/test_stall.py` 的假 TUI 校准。

**偏离日志：**
- 计数矩阵：一次调用（`manifest-20261121T175104-87852.json`），21 组 × 3 次 = 63 次；0 次 invalid，0 次补跑；没有用 `--deviation`。
- 卡片提交 `3ec9c31` 开跑时没有推送，冻结时间只由本地提交担保。
- 夹具性质，不是偏离，但影响数字的大小：`T-bash-mixed-20k` 的仓库用 `cp -cR` 从模板复制，git 索引里记的文件属性因此全部过期。metacodes 观察文件变化时用 `git --no-optional-locks status`，刷新后的索引不写回，所以每次观察都要把整个工作树重算一遍哈希。冻结后在模板的一份复制上核对过（不计数）：刷新前 5.82 s、1.09 s，刷新后 0.05 s、0.04 s。判定不受影响，大小要按“索引过期”来读，记为 RQ-X-016。

## 4. 完整性声明

1. **没有选格、删格、改判定。** 63 次计数运行全部当场按冻结的判定代码判分，结果写进 `runs.jsonl` 和逐次 `record.json`。判定逻辑嵌在每组的操作里，所以本期没有像第 5 期那样做事后重判，靠的是证人文件前后哈希一致。
2. **环境失败：0 次。**
3. **污染登记：**
   - 冻结前的试跑和冒烟参考了预测和判定窗口，卡里写明了；
   - 等待型的组 5 个并行，机器上同时还有别的会话在跑构建和测试，亚秒级判定的组单独跑；
   - 夹具的索引过期，见上；
   - 沙箱让被测处于离线状态；
   - 被测以实验者的用户身份运行，能读证据根，但它只按脚本化网关的工具调用行事，读写的只是它自己的工作目录。
4. **写报告时已知的证人盲区：**
   - 伪终端只回答 DA1；
   - 时钟读的是字节到达的时刻，不是屏幕画完的时刻；
   - 只造了“接了连接不回”“回得慢”两种卡法；
   - 超时配小、等待截断在 35 s；
   - 只测交互式 TUI；
   - 只在 macOS 上测过。

   详见 `witness/stall/README.md` 和实验卡的 `blind_spots`。
5. **事后审计：**
   - 沙箱拦下的外连：`log show` 在 17:50:50–17:56:30 的窗口里是 0 次（`egress.json`）；
   - LaunchServices 里，证据根下的登记是 0 条（`lsregister.json`）。

## 7. Posting gate 记录

- [x] 上游先开环：2026-11-21 经负责人同意（“提吧，不指派”），在 metask-ai/metacodes 提了 [#666](https://github.com/metask-ai/metacodes/issues/666)–[#672](https://github.com/metask-ai/metacodes/issues/672)，作者 BiBoyang，都没有指派。提之前查过重：标题关键词搜索，加上最近 12 个 issue，都没有重复。提之后逐个读回：标题、正文与草稿逐字一致，标签正确。其中 #671 那次提交前的查重请求遇到网络超时，事后列出最近的 issue 核对过，每个标题只出现一次。正文不引用本仓库，复现步骤是自带的几段 Python。
- [x] 每个数字都对照了一手来源：`runs.jsonl`、逐次 `record.json`、假服务器的事件、manifest。
- [x] 最显眼的结论端到端复核过。“打出 `/model` 冻住输入框，只能靠看门狗结束”在三处都站得住：试跑（伪终端、tmux 截屏）、冒烟、计数矩阵。代码路径也逐行核对过。
- [x] 每个数字旁边都写了 x/N 和条件，包括配小的超时、35 s 截断、索引过期。
- [x] 污染登记已复核，受影响的格子都标了。
- [x] 公开副本用 `witness/stall/stall.py export` 导出：源目录导出前后哈希清单一致，禁用串扫描和 `audit_artifacts.py` 都通过。
- [ ] 推送与远端 SHA 核对：2026-11-21 经负责人同意，本期提交快进到 master 后推送（“快进推到 master”）。本文件在推送前定稿，推送后的本地与远端 SHA 核对不在这里，按 `reporting.md` 在推送之后单独做。
