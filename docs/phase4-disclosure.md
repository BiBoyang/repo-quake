# DISCLOSURE — phase4：流中途断开、自动重发之后的显示（2026-11-14 → 11-16）

按 `skills/repo-quake/references/disclosure-template.md` 填写，配合 `docs/phase4-report.md`。

测的是什么：Claude Code 2.1.282、codex-cli 0.169.0、Kimi Code 2.5.3，在模型的流式回答断在中途、自动重发之后，显示的内容和存下来的对话是否一致。全部只连本机回环地址上的 mock。

**估计还是官方测量。**本期每个数字都属于（a）类：自己的运行里直接观察到的。没有官方或组织方的测量可以对照。只有一处有意空着：Kimi Code 重发带回半截之后，真实服务端是续写还是重写。这需要调用真实接口，没有测。报告里的两种结果都是 mock 分支下的观察，不代表真实服务端。

## 1. 接触面

- **碰过的：**
  - 本机已安装的三个 CLI。Kimi Code 只在主矩阵和续写对照里用过。
  - 本机回环地址上自己启动的 mock。
  - Kimi 平台 Partial Mode 的公开文档：只读了；它是有版权的页面，本仓库只引用、不收录。
  - MoonshotAI/kimi-code 的 issue #4964：由负责人提交，本期只做了只读回读。
  - openai/codex 的 issue [#47538](https://github.com/openai/codex/issues/47538)：11-16 经负责人同意，用其账号补了一条评论（见第 7 节），之后只读回读。codex 仓库 `rust-v0.169.0` 标签和 main 上的几个源码文件：只读。
- **没碰过的：**
  - 任何真实的模型端点。没有付费调用：补测时沙箱拦下了所有非回环出站连接；另外两轮用 `env -i` 配临时 HOME，没有任何凭据。
  - 任何账号或凭据。
  - 用户真实的 `~/.claude`、`~/.codex`、`~/.kimi-code`：只读，从没改过。
- **隔离（补测）：**
  - `env -i` 白名单，每次运行一个新的临时 HOME，一次性对话框的答案预先写好；
  - `sandbox-exec` 只放行到 localhost 的出站连接，DNS 也解析不了；
  - tmux 用独立的服务器和空配置；
  - 关掉了更新检查和 Claude Code 的 deep link 注册（`disableDeepLinkRegistration: "disable"`）。
- **隔离强度为什么够：**被测程序最坏能做到的事，前两轮都真实发生过：在 LaunchServices 里注册应用、拉取更新清单、往 HOME 里下载文件（见第 4 节）。补测针对这些逐条设了防，并做了事后审计：
  - LaunchServices 里只剩用户自己 `Applications/` 下那一份 Claude Code URL Handler；
  - 沙箱拦下 60 次外连，全部来自 codex 的域名解析，每次启动大约 3 次；Claude Code 0 次。
  - 11-16 探索性补跑（只有 codex）用同样的隔离：沙箱拦下 58 次，全部是 codex 的域名解析；LaunchServices 仍只有用户自己那一份。

## 2. 哈希清单

| 对象 | sha256 / 版本 | 说明 |
|---|---|---|
| Claude Code 2.1.282 | `fcfd837103965c64de34a6b9b94370d77a347ea71819715a27d5f0ef01775ea4` | 启动文件是符号链接，指向这个原生二进制；补测每次运行都用 `lsof` 核对，18/18 一致 |
| codex-cli 0.169.0 启动壳 `codex.js` | `e14fc83739c13c1074b12bd1acce4010c893c7f6fbfc1593b4a31d74cabb57af` | 主矩阵只记了这一个 |
| codex-cli 0.169.0 原生二进制 | `739cda86e15d30a6e2b40cf8dcbbfb988aaf48b305b27065573bb8e9fd41d002` | `codex.js` execve 的对象；补测每次运行用 `lsof` 核对，18/18 一致 |
| Kimi Code 2.5.3 | `70c39581c5f3d045aa64f47374c0c2fd6f8e45013ffd51fd38ac32c4e6122ce8` | 续写对照前后一致；Kimi Code 的结果都来自 2.5.3，2.6.0 已发布，没有复测 |
| node（运行 `codex.js` 和 mock） | v25.4.0，`d8c9ba1203a4026fb18277599eb5ed328d48bb7feae9c26cd4b80d9bf68b85cf` | |
| tmux | 3.5a | |
| `witness/stream-retry/mock.mjs` | `e7fef77a7d9d37f87a4b9a0d139ce6bcc4eefb7416f12cdda9c73ee51e142171` | 补测时冻结。主矩阵前后用过两个没记哈希的 mock 版本（`a207fda8…`、`4482f1d9…`） |
| `content.json`（段落夹具） | `1e7aa28970310b2c2388e8bf4d33ce57c74190dee0d0e79d5bc10c8e70dfe763` | P01–P24 与前两轮逐字相同 |
| `runner.py` | `e507c4b8fb5c9882207e19b0fc4896cbd4447fe1dbe926c68bb41388f1738410` | 冻结 |
| `grading.py` | `506b8d112f11be4c6d773193910373ef1e85a33cda9bbb398be89cb2dbb0f8b9` | 冻结；变异检查后用副本恢复，`cmp` 一致 |
| `rawtap.py` | `dadfc1666abe8b4bccf794e1d0a90899dfb40a311f0ab0f3e033b14180091750` | 冻结 |
| `version_witness.py` | `c7db93d903d63c077a22e590c5955e4e1d587f9f4f77fff24a61c146e14e97b1` | 冻结 |
| 实验卡 `examples/experiment-card-phase4-stream-retry.json` | `66fcde0a3c5741cb66719fd1fa13a98fa39ebb3ffef6c33d718b231fbb037562` | 证据目录里的冻结副本，与仓库里的逐字节相同 |
| 提示词模板 | `2294655f1a14a801b1ad597692250341b2d915a70b486e383ac11153f89cfb65` | 跟进那一轮的提示词是 `2377dffeecfdc44ba3259a34b1ab2c66b2afa6f1bbe7fe4d27397ebe2c1ee113` |

补测前后各记了一次版本和哈希，三个工具、node 和装置文件都一致（`runs/phase4-stream-retry-2026-11-15/versions-before-*.json` 和 `versions-after-*.json`）。

11-16 探索性补跑：装置文件的哈希和上表相同（`runner.py`、`grading.py`、`mock.mjs`、`content.json`、`rawtap.py`、`version_witness.py`）。codex 原生二进制每次运行用 `lsof` 核对，12/12 一致；前后版本和哈希一致（`runs/phase4-codex-retries-exhausted-2026-11-16/versions-*.json`）。评论里附的最小复现 `retry_dup_mock.py` 是 `8eb5350eca2532b49972b14efbd4edbfa775eef9e2ede26084190e228e1613ca`，发出的评论正文是 `d5ed8e88f4423c403ce6883ccd86099055c771f7d7a081b5f2483d887d0a353e`。

## 3. 预注册与偏离

**预注册。**
- 补测的预注册是三样东西：实验卡（在第一次计数运行前冻结，15:06Z）、`witness/stream-retry/README.md` 的判定规则、装置文件的哈希。
- phase 3 的披露文件承诺过"phase 4 会有预注册"：补测做到了。主矩阵有卡，但超出预算，也没有偏离日志（见下）。

**补测的偏离日志。**
- 计数矩阵运行期间：无，0 次补跑，0 次无效。
- 冻结前的试跑：17 次，每格 1–2 次（Claude Code 8 次，codex 9 次），不计入。试跑期间改过这些：
  - tmux 配置（`set -g window-size manual` 会让 tmux 3.5a 崩溃）；
  - 截图间隔：从 150 ms 改成 30 ms，因为 Claude Code 的半截只在屏上停留 140–190 ms，150 ms 截不到；
  - 加了 `rawtap.py` 的字节时刻；
  - 加了重叠截图；
  - 修了 mock 的一个毛病：codex 收到 `response.completed` 后立刻挂断，被记成了"客户端中途断开"。这个毛病是健康对照判失败时暴露出来的。
- 卡里的结论参考了试跑。
- 矩阵结束后又改过：
  - `export_public.py`：替换规则改成最长的先替换；代码里的禁用串只留通用模式（本机用户路径、邮箱、身份类字段名、请求体结构），项目内部名字放进仓库外的私有清单，用 `--deny-file` 传入。公开副本用最终版重新导出，源目录的哈希清单摘要和第一次导出相同（`c860d01d…`）；
  - `summarize.py`；
  - `tests/test_stream_retry.py`：补了两个测试。一个是变异检查发现"画面不完整"这条规则原来没有测试单独兜住；另一个覆盖"请求体或私有词混进副本就导出失败"。

  这些都不影响已产生的数据，`regrade` 从证据文件重判，36/36 结果不变。

**11-16 探索性补跑（没有预注册）。**
- 内容：codex 0.169.0 交互，F0-pre、F1-always、F6-always、F0-post 各 3 次，共 12 次；装置和补测相同，没有改任何文件。时间 2026-11-16 01:33–01:41Z。
- 为什么跑：主矩阵里 codex 交互 F1-always 的最终画面上有两份以上的 P01–P12，但 35 行窗口数不清总份数；上游 #47538 的一条评论按源码预测了"重试用完时拼接留屏"。要在补充上游证据之前测准。
- 没有预注册：是看到线索和预测之后才跑的，方向事先已有预期。它不进实验卡的 x/N，在报告、台账里单独列出（RQ-F-017、RQ-X-014）。
- 0 次无效、0 次补跑；对照 F0 前后 healthy 6/6。
- 另用最小复现对 0.169.0 各跑 1 次（只断一次、每次都断）。驱动脚本在仓库外，同样是 `env -i`、一次性 HOME、只放行 localhost 的沙箱，发键前验屏；截屏和时间线在 `runs/phase4-codex-retries-exhausted-2026-11-16/upstream-repro/`。

**主矩阵的偏离（由 11-15 复验整理）。**
- 卡上写的 `max_runs` 是 108，实际约 210 次，没有记偏离；
- 端口冲突的时间窗里，有一次运行没有筛掉；
- Claude Code 交互的"每次都断"跑在旧 mock 上；
- FLONG 补跑之后没有再跑 F0；
- "不重发"的静默窗口只有 30 秒，比实测的最大重发间隔（33–40 秒）还短，但在所有有效运行里一次都没有触发；
- mock 的哈希没有记录。

**更正的来龙去脉。**主矩阵的原始汇总保留不动，更正写在报告"更正"一节。补测是一张新卡（新 id、新预算），不是在主矩阵上改数字。

## 4. 完整性声明

1. **补测没有在判分开始后删格、选格或改标签。**36/36 都判了分。`regrade` 按各自的文件重建中途画面、最终画面和原始字节，重判结果和记录完全一致。
2. **环境失败。**补测是 0 次。主矩阵的非交互批次因端口冲突整批作废、重跑，作废的数据单独归档。
3. **污染登记。**
   - 补测矩阵运行期间，本机同时运行过测试（其中有假 TUI 的端到端测试，用它自己的 mock、端口和 tmux 服务器），可能争用 CPU，影响毫秒级的时间数字；判定不依赖这些时间。
   - 冻结前的试跑参考了结论。
   - 11-16 探索性补跑期间，本机没有同时跑测试或别的被测程序；最小复现是补跑结束之后才跑的。
   - 沙箱让被测程序处于离线状态。
   - 主矩阵和续写对照：
     - UTC 08:24–08:36，另一个执行者占用了相同端口；
     - Claude Code 在 LaunchServices 里注册了临时 HOME 里的 URL Handler（11-15 已注销）；
     - Kimi Code 设置了 `auto_install=false`，仍拉取了 25 次更新清单，临时 HOME 里还多出一个 `fd`；
     - `cleanup.py` 原地改写了证据：主矩阵 1387 个文件，续写对照 41 个。这两轮的原始证据因此不再是原样，报告只引用复验核对过的数字。
4. **写报告时已知的证人盲区。**
   - 原始字节只能证明"写到了终端"，证明不了"人看得见多久"；停留时间短于截图间隔（约 30–60 ms）就截不到。
   - "画面完整"用的是"横幅和本次提示词都在"，一个会省略对话中间部分的应用能骗过它；本期两个工具都没有这种省略。
   - tmux 不是真终端。
   - 续写分支对 Claude Code、codex 没有跑到，因为它们的重发都不带半截。
   - Kimi Code 没有用新证人补测。

## 7. Posting gate 记录

- [x] 第三方发现先开上游：Kimi Code 的发现一已提 [MoonshotAI/kimi-code#4964](https://github.com/MoonshotAI/kimi-code/issues/4964)，2026-11-15 14:29Z 由负责人提交，只读回读状态是 OPEN，标题与草稿一致。
- [x] Kimi Code 重发不带 `partial` 标记那一条：按负责人的决定不报上游，报告里写成"待验证的观察"，不当成已确认的缺陷（真实服务端的行为没有测）。
- [x] 发现二里 codex 的"重叠"，连同 11-16 测到的"重试用完时拼接留屏"，补在上游 [openai/codex#47538](https://github.com/openai/codex/issues/47538) 下：[评论](https://github.com/openai/codex/issues/47538#issuecomment-6905066983)，2026-11-16 01:47Z，经负责人同意用其账号发出。读回核对：作者正确，正文与本地文件逐字一致（8089 字节），帖子仍是 OPEN，同一账号在帖子里只有这一条评论。没有新开 issue：#47538 就是同一个问题，codex 的贡献规则要求已有 issue 就把新信息补在原帖下。
- [x] 每个数字都对照了一手来源：
  - 补测数字来自 `runs.jsonl`、逐次 `record.json` 和送达日志；
  - 主矩阵和续写对照的数字由复验对照过，本期又抽查了四项：Kimi Code 重发带半截 12/12 加 12/12；F6 是 3+3 次单请求；非交互 18 次一次都没打印过半截；前后 F0。
- [x] 最显眼的结论做过端到端复核。"Claude Code、codex 收回了半截"原是主矩阵的头条，复验发现证据撑不住，补测用失败标记重新测过，结论成立，并补上了过程差异。
- [x] 每个数字旁边都写了样本量和保留意见。
- [x] 污染登记看过，受影响的格都注明了，没有藏。
- [x] 公开复现在干净环境里跑过：#4964 正文里的最小复现，11-15 已在本机用一次性 HOME 跑通（记录在复验报告里）；#47538 评论里的最小复现，11-16 对 codex 0.169.0 两种模式各跑通 1 次（见 `runs/phase4-codex-retries-exhausted-2026-11-16/upstream-repro/`）。
- [ ] 公开写入去重、回读，远端 SHA 核对：#4964、#47538 的评论都已回读。本期提交随 repo-quake v0.2.0 一起推送（2026-11-16）；本文件在推送前定稿，所以推送后的本地与远端 SHA 核对不在这里，按 `reporting.md` 在推送之后单独做。
- 仓库或材料要先于引用它的 issue 公开：不适用。#4964 和 #47538 的评论都自带复现，没有引用本仓库。
