# DISCLOSURE — phase5：用第 4 期装置复测 metacodes、deepseek-harness，复查 9 月交互附录与 skill-up 修复（2026-11-16）

按 `skills/repo-quake/references/disclosure-template.md` 填写，配合 `docs/phase5-report.md`。

**估计还是官方测量。**本期每个数字都属于（a）类：自己的运行里直接观察到的。没有官方或组织方的测量可以对照。有意空着的：真实服务端对"续写请求"是接着写还是从头写（mock 总是从头写），这需要调用真实接口，没有测。

## 1. 接触面

- **碰过的：**
  - metacodes：从 `metacodes-zig` 克隆 `git worktree add --detach` 出 upstream/main 1707da0c，构建后删掉 worktree；克隆本身的检出、分支、文件没有动（只 `git fetch upstream main` 更新了远端跟踪引用，没有新提交）。
  - 本机已安装的 Claude Code 2.1.282、codex-cli 0.169.0：只运行，没有改。
  - deepseek-harness：经用户同意，从 registry.npmmirror.com 用 `npm install --ignore-scripts` 把 `@deepseek-ai/dsh@0.2.2-rc.3` 装进证据目录里的隔离前缀，npm 缓存也放在那里。没有全局安装。
  - skill-up：用本地克隆里已有的 v0.15.0 和 #281 head（8c9e12b）源码，`git archive` 到证据目录后构建；经用户同意，从 proxy.golang.org 下载了一个缺的 Go 模块（`github.com/openai/openai-go/v3 v3.86.0`，2,356,710 字节），它进了本机的 Go 模块缓存。
  - GitHub 上 alibaba/skill-up 的 issue、PR、发布页，deepseek-ai/deepseek-harness 的发布页，npm 的包元数据：只读查询。
  - 报告写完后补查（只读）：metask-ai/metacodes 的 PR #465 正文；deepseek-ai/deepseek-harness 的仓库设置（issue 已关、Discussions 开着）、CONTRIBUTING.md、Discussions #12347、#11298、#10743 和近期讨论的标题。
  - 上游写入只有一次：2026-11-16 10:14:53Z 经负责人同意，在 deepseek-ai/deepseek-harness 的 Discussions（Ideas 分类）发了 [#13496](https://github.com/deepseek-ai/deepseek-harness/discussions/13496)，作者 BiBoyang，由派出本会话的会话发出；本会话只读回读，标题和正文与草稿逐字一致。
- **没碰过的：**
  - 任何真实的模型端点。没有付费调用，也没有任何凭据：metacodes 用 `METASK_API_KEY=dummy`，dsh 用 `MOCK_API_KEY=mock`，Claude Code、codex 用 `mock`。
  - 用户真实的 `~/.claude`、`~/.codex`、`~/.metacodes`、`~/.skill-up`、dsh 的默认 home：每次运行都是新的临时 HOME。
  - 除上面那一次 Discussion 之外的任何上游写入：没有发 issue、评论或 PR。
- **隔离：**`env -i` 白名单、每次运行一个新的临时 HOME（dsh 另有新的 `DSH_HOME`）、`sandbox-exec` 只放行到 localhost 的出站连接、tmux 用独立的服务器和空配置；Claude Code 关掉自动更新和 deep link 注册，codex 关掉启动时查更新，metacodes 关掉 Jev 查询（它启动时不查更新），dsh 关掉遥测。
- **事后审计：**
  - 沙箱拦下的外连：metacodes 矩阵 0 次；附录矩阵 55 次，全部是 codex 启动时的域名解析，Claude Code 0 次；dsh 矩阵 0 次。
  - LaunchServices：每个矩阵之后都查过，`lsregister -dump | grep "Claude Code URL Handler"` 只有用户自己 `Applications/` 下那一份。

## 2. 哈希清单

| 对象 | sha256 / 版本 | 说明 |
|---|---|---|
| metacodes 0.12.1-dev+1707da0c6768 | `ee7718a91d7d3baa5288e9f54c8bdbaae0eae2720b4896818658be3bdad2cd64` | upstream/main `1707da0c676863f62d99d58b1e33d0956cf21d1d`，zig 0.16.0，ReleaseSmall；TUI 每次运行 `lsof` 核对 27/27 一致 |
| Claude Code 2.1.282 | `fcfd837103965c64de34a6b9b94370d77a347ea71819715a27d5f0ef01775ea4` | 与第 4 期相同；附录 TUI 每次运行 `lsof` 核对 15/15 一致 |
| codex-cli 0.169.0 原生二进制 | `739cda86e15d30a6e2b40cf8dcbbfb988aaf48b305b27065573bb8e9fd41d002` | 与第 4 期相同；附录 TUI 每次运行 `lsof` 核对 15/15 一致 |
| `@deepseek-ai/dsh` 0.2.2-rc.3 启动文件 `lib/bin.js` | `36f86742e0c3cc1c3b2dbaa6582ee00b0c37bc4f5a190f7531b5303bf3efb6d9` | 安装树 95,730 个文件，哈希清单摘要矩阵前后都是 `3de4349a87d2d4748114a77cf56e51e1ff947d9e3e5e7c95cd0c8305aa8777fa` |
| skill-up v0.15.0（源码自建） | `031e5cfda329b27cd1a409b275a490aae62f38c1ca7d822a0a6d017f580f702a` | tag 对应提交 `bce6f1cb9a5d688a753a862620bd7dc33d3389ca`；版本字符串 `dev` |
| skill-up #281 head（源码自建） | `ff6aff9ed005d0f784b45060ac01da3229f65b3329f71dc990a8d759ffbd5bd7` | 提交 `8c9e12b8b862c85d07e167c2157e092e32fb1501`，与 PR 当前 head 一致 |
| node | v25.4.0，`d8c9ba1203a4026fb18277599eb5ed328d48bb7feae9c26cd4b80d9bf68b85cf` | 运行 mock 与 dsh |
| tmux | 3.5a | |
| `mock.mjs` | metacodes 与附录：`d9115c9385ccc48a3dfe7bc54d68eff6faf994bab5a6a004dc9a948a1bef7ac8`；dsh：`49440ba1a9daf4922d77d9a613a94f8f28211f53ab78f626c896e0c7adaf6485` | dsh 那一版加了 `aux_match` |
| `runner.py` | metacodes 与附录：`0bd3acf518be7e0b5cf6f068d6445cef604fd8417eec959696d869512692d471`；dsh：`d9e312344eaf9caee070ff6091dd6913634f41a0327c274faa01730ea3f7511b` | dsh 那一版加了 dsh 适配器、会话日志的 zstd 读取 |
| `grading.py` | metacodes 与附录：`1cc52258b4c28563a4d48a442cbd5a3850a3fdc0fec1cddeed83fa1565b7608e`；dsh：`cd9b4f7a6d74fc509c566dd8fce71cec9562f3a13d593b70cd90957fa2e99eee` | dsh 那一版加了 dsh 停止原因与 zstd 读取 |
| `content.json`、`rawtap.py`、`version_witness.py` | `1e7aa289…`、`dadfc166…`、`c7db93d9…` | 与第 4 期相同 |
| 实验卡 | metacodes `32f1bc2846dfc2303c47a712df44b3fec9c3c2619f61a7ed477cb6da9725eb98`；附录 `0e860304892e99adf72377d92e96778bda5d5e4b06820a860aad301418edb196`；dsh `41d9989a08fbd0a6108086c946498df44146637f2dcd04a9cf067c07f882da7d` | 每张卡在第一次计数运行前冻结；证据目录里的冻结副本与仓库 `examples/` 里的逐字节相同 |
| 提示词 | `2294655f1a14a801b1ad597692250341b2d915a70b486e383ac11153f89cfb65` | 跟进那一轮 `2377dffeecfdc44ba3259a34b1ab2c66b2afa6f1bbe7fe4d27397ebe2c1ee113` |

每个矩阵前后各记一次版本和哈希（被测、node、装置文件、实验卡），全部一致（`runs/phase5-*/versions-before-*.json`、`versions-after-*.json`、`manifest-*.json`）。

## 3. 预注册与偏离

**预注册。**三张实验卡（metacodes、附录、dsh）各在自己的第一次计数运行前冻结，连同 `witness/stream-retry` 的装置哈希。卡上的预测参考了冻结前的试跑，卡里写明了。三个矩阵的结果和卡上的预测一致。

**偏离日志（各证据目录的 `DEVIATIONS.md`）：**
- metacodes：加了 F0-tag、F0T-tag 两个阳性对照（任务原定条件里没有）。
- 附录：加了 `claude -p`、`codex exec` 两个非交互宿主（为了在同一版本、同一 mock 上回答"交互和非交互有没有差别"），加了 F0-tag。
- dsh：三种协议都测；安装时没跑 5 个包的安装脚本（用户选择）。
- 计数矩阵运行期间：0 次无效、0 次补跑。

**冻结前的试跑（不计入）：**
- metacodes 24 次（每格 1 次，四种模式）。试跑期间改过：metacodes 空输入框写着 `Try "fix typecheck errors"`，提示词表里的 error 会把它当成提示，健康对照全部会被判失败；改成按工具排除这行固定 UI 文本（RQ-I-012）。
- 附录 13 次。codex 交互那一轮因 mock 崩溃中断：codex 的标题请求走 `/v1/responses` 的结构化输出，本期新加的思考字段在那条路径上没有默认值。修好后补了回归测试和变异检查，再重跑试跑（RQ-I-011）。
- dsh 24 次加手工几次。发现 dsh 的标题请求是纯文本、又带着本次的随机标记，会被当成正式回答、吃掉一次性故障；给 mock 加了 `aux_match`。

**判定口径相对第 4 期的改动：**本期所有重发分支的判定都记 `reported`（第 4 期只在 fork 上记）；F4/F5 用单独的 `_grade_signal`。第 4 期已发布的判定标签不受影响。

## 4. 完整性声明

1. 三个矩阵共 240 次计数运行，都判了分，没有删格、选格或改标签。矩阵跑完后用最终版判定代码从证据文件重判，240/240 不变（各证据目录的 `regrade.jsonl`，写在公开副本导出之后，所以公开副本里没有它）。
2. 环境失败：0 次。
3. 污染登记：
   - 三个矩阵依次运行，中间没有并行的被测运行；npm 安装和 Go 构建在矩阵之间做。
   - 冻结前的试跑参考了结论。
   - 沙箱让被测处于离线状态。
4. 写报告时已知的证人盲区：
   - 原始字节证明的是"写到了终端"，不是"人看得见多久"；
   - mock 对续写请求总是从头写，Claude Code 的 F4 续写显示两份（TUI）、`-p` 看起来完整，都依赖这个假设；
   - FTHINK 的重发是普通回答，没有思考；
   - `--stream-json` 的读法假设消费者按协议把行归到当时开着的段；
   - tmux 不是真终端；
   - 网页端和 C ABI 宿主没有测。

## 7. Posting gate 记录

- [x] 第三方发现先在上游报：dsh 的"长度截断后光秃秃的退出码 1"。上游关了 issue，按 CONTRIBUTING 走 Discussions；相近的 #12347、#11298、#10743 没覆盖这一点。2026-11-16 10:14:53Z 经负责人同意，以 feature request 发在 Ideas 分类：[#13496](https://github.com/deepseek-ai/deepseek-harness/discussions/13496)（作者 BiBoyang；README 的 Exit mapping 写明这是设计如此，所以按 feature request 写）。读回逐字一致：标题与草稿标题行相同，正文与草稿从 `## Summary` 到结尾相同（3043 字符）。
- [ ] metacodes 的 TUI 留屏：[#465](https://github.com/metask-ai/metacodes/pull/465) 正文已写明这是取舍（不是新缺陷）。本期的实测和补充（只有思考时也留屏、屏上那段模型没见过、原始字节零提示）要不要写成 enhancement、是否指派，由负责人定；enhancement 草稿 `metacodes-issue-draft-tui-retry-fork-2026-11-16.md`。
- [x] codex 的 F4/F5 行为变化：不是缺陷（报告写明了原因、不再重试），不需要上游动作。
- [x] Claude Code `-p` 续写后只打印最后一条消息：写成待验证的观察，没有报上游。
- [x] skill-up：#253、#263 已关、修复已合，本期只复验；#280、#281 状态没有变化，没有写入。
- [x] 每个数字都对照了一手来源（`runs.jsonl`、`runs-noninteractive.jsonl`、逐次 `record.json`、送达日志、会话文件）。
- [x] 公开副本用 `export_public.py` 导出（源目录导出前后哈希清单一致），禁用串扫描和 `audit_artifacts.py` 都通过。私有禁用词清单在仓库外。
- [ ] 推送与远端 SHA 核对：本期提交只在本地分支 `feat/phase5-stream-retest`，没有推送。
