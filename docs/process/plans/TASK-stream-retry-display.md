# 执行提示词模板：流中途断开、自动重发之后，显示和对话是否一致

> 给人看的说明（执行者可以忽略这一块）
> - 这是 repo-quake 第 4 期的执行提示词模板。尖括号里的占位符，派发前一律换成实际值。占位符清单在文末。
> - 用法：在执行者（另一个 CLI 会话）里说一句"读取并执行 `<本文件路径>`"。执行者要能起本地服务、开 tmux、启动别的 CLI、写证据目录，所以要用你认可的权限启动它。
> - 跑完以后，由另一个会话按文末的"复核清单"逐项复核，复核通过才能写报告。第 4 期的经验是：最显眼的那条结论，恰恰最需要复核（`docs/phase4-report.md`）。

---

## 你的角色和要回答的问题

你是实验执行者。要回答的问题是：**模型的流式回答断在中途、CLI 自动重发之后，屏幕上（或 stdout 里）还留不留第一次的半截？用户看到的，和 CLI 存下来、下一轮要发给模型的，是否一致？**

被测的是 `<被测工具清单>` 这几个 CLI 进程。你自己可能也是其中之一，所以被测进程和你自己的会话、配置必须完全隔离。

方法论在 `<仓库>/skills/repo-quake/SKILL.md`，先读其中的 Methodology invariants，再读 `references/fault-catalog.md` 的 §stream 和 §env。实验装置是 `<仓库>/witness/stream-retry/`，先读它的 `README.md`：判定规则、证人和已知盲区都在那里。**不要另写一套 runner。**

## 硬约束

任何一条做不到，就停下来，在 `RUNLOG.md` 里写明原因。

1. **只连本地 mock。** 被测程序只能连 127.0.0.1 上、由 runner 自己启动的 mock，不调用任何真实的模型端点，不花钱。runner 默认用 `sandbox-exec`，只放行到 localhost 的出站连接，不要关（`--no-sandbox` 只用于排查装置问题，用了就要记进偏离日志）。
2. **不改任何真实配置。** 用户自己的 `~/.claude`、`~/.claude.json`、`~/.codex`、`~/.kimi-code`、`~/.config` 一律只读。被测进程由 runner 用 `env -i` 白名单启动，每次运行一个新的临时 HOME，都在证据目录里。
3. **不安装、不升级、不迁移。** 不跑 npm、brew、pip、uv 的 install 或 upgrade。被测程序弹出更新、迁移、登录、信任目录这类提示时，runner 的按键闸门会拒绝输入，把这次运行记为无效。不要手动去按键。
4. **前后各记一次版本和哈希。** `runner.py matrix` 会自动做：开始前写 `versions-before-*.json`，结束后写 `versions-after-*.json`，并比较两份。哈希算的是实际执行的文件：npm 包的 `codex.js` 要追到它 execve 的原生二进制。只要有一项变了，整轮作废，并报告。
5. **不碰 git，不往外发。** 不 commit、不 push，不修改 `<仓库>` 里的任何文件（可以读）。不往网上发任何东西。
6. **证据只放证据目录。** 证据目录是 `<证据目录>`，在公开仓库之外，不放 `/tmp` 或 `/private/tmp`。**不原地改写任何证据**：不脱敏、不重排、不"清理"。要公开的部分，只能用 `export_public.py` 导出副本。
7. **长命令放后台。** 预计超过 2 分钟的命令（矩阵一轮约 12 分钟），用后台方式跑，日志写进证据目录，再用短命令查进度。
8. **环境折腾有时限。** 一个工具的环境问题折腾超过 30 分钟，就放弃它，记为 N/A 并写明原因。环境失败不算数据。
9. **提示词保持中性。** 不要给被测程序任何"可能出错"的暗示。runner 里的提示词是冻结的，不要改。
10. **每个执行者用自己的端口。** runner 默认用临时端口；如果指定端口，被占时 runner 会拒绝运行，不要去"复用"别人的 mock。

## 被测对象（版本钉死）

| 工具 | 启动文件 | 期望版本 | 备注 |
|---|---|---|---|
| Claude Code | `<claude 路径>` | `<claude 版本>` | runner 已关自动更新和 deep link 注册（`disableDeepLinkRegistration`） |
| codex | `<codex 路径>` | `<codex 版本>` | npm 启动壳；runner 会追到原生二进制 |
| Kimi Code | `<kimi 路径>` | `<kimi 版本>` | 只在需要时测；它关不掉更新清单拉取，靠沙箱和前后哈希兜底 |

## 步骤

1. **先读再动手。** 读上面提到的三份文档。在 `RUNLOG.md` 里写下开始时间、证据目录、被测版本。
2. **跑测试。** 在 `<仓库>` 里跑 `bash tests/run_tests.sh`，要全部通过。不通过就停。
3. **探针。** 跑 `runner.py probe`：每个工具只启动、截屏、退出。确认能停在输入框、屏上没有需要按键确认的提示、横幅可见。把探针截图存进证据目录（runner 会自动存）。
4. **冻结实验卡。** 复制 `<仓库>/examples/experiment-card-phase4-stream-retry.json`，改成本轮的 id、版本、哈希和预算，用 `skills/repo-quake/scripts/validate_card.py` 校验通过。把冻结的卡复制进证据目录，并记下 runner、mock、grading、content 的 sha256。**卡冻结后不回改**：发现规则有误，另开新卡。
5. **跑矩阵。** 条件和顺序是：F0-pre、F0-tag、F1-once、F6-once、FLONG-once、F0-post，每格 3 次。runner 会先跑阴性对照和阳性对照，这两格不过，该工具的故障格就不跑。命令：

   ```bash
   python3 <仓库>/witness/stream-retry/runner.py matrix --out <证据目录> \
     --tools <被测工具清单> --runs 3 --bin <工具>=<路径> ... --expect <工具>=<版本> ... \
     --path-env "<给被测程序的 PATH>" --card <证据目录>/card-frozen.json
   ```

6. **补跑。** 无效的运行（按键闸门、装置异常、超时）在本工具序列的最后补跑一次。**每次补跑之后，都要再跑一轮 F0-post（3 次）**，两轮 F0-post 都报告。补跑和原因都写进偏离日志。
7. **收尾。**
   - 跑 `runner.py egress --start <开始时刻> --end <结束时刻>`：列出被沙箱拦下的外连。
   - 跑 `runner.py lsregister`：列出 LaunchServices 里的 Claude Code URL Handler。结果里应该只有 `<用户自己的 Applications 目录>` 下那一份；多出来的，**先报告，不要自己注销**。
   - 跑 `runner.py summarize`，生成 `summary.md`。
   - 核对 tmux 和 mock 进程都已退出。
8. **交付。**
   - 证据目录里的 `runs.jsonl`、`summary.md`、`manifest-*.json`、`versions-before/after-*.json`、`RUNLOG.md`、偏离日志；
   - 给派发者回一段 15 行以内的摘要：版本前后是否一致、x/N 总表、意外情况、证据目录。只报数据，不下评价性的结论；凡是推断，都标明"推断"。

## 偏离日志（`DEVIATIONS.md`）

一行一条，写清楚：偏离了什么、为什么、影响哪些格。例如：补跑、改了参数、换了版本、沙箱关掉过、某格 N/A。**一条记下来的偏离是数据；一条没记的偏离是污染。**

---

## 复核清单（给复核者）

复核者不跑新的实验，只读证据。每一项都要写结论和证据位置。

**送达和时间线**
- [ ] 每次故障运行：一次性故障确实送到了带 mark 的正式流式请求上（`delivery.jsonl` 里 `fault_source: once`），标题等辅助请求没有吃掉它。
- [ ] 中途截图是**失败标记**触发的（`mid.json` 里 `trigger: tag`），而且截图时刻早于重发请求的开始时刻（`record.json` 的 `display.mid.lag_vs_retry_start_ms` 为负）。截图晚于重发开始，就不能当"重发前显示过半截"的证据。
- [ ] 原始字节里失败标记第一次写出的时刻（`raw.tag_first_ms`），和故障流的起止时刻对得上。

**备用屏幕和完整性**
- [ ] 原始字节里有没有 `ESC[?1049h`，在第几个字节（`raw-analysis.json` 的 `alt_screen_on`）。有的话，最终画面只能证明屏上的内容。
- [ ] 判为 `retracted` 或 `not_shown` 的运行，最终画面必须完整：横幅和本次 mark 都在（`final_complete: true`）。不完整就只能判 `n/a`。
- [ ] FLONG 的断开前截图（`prefin.txt`）里，160 段里的前 150 段和横幅能同时在屏上。

**提示**
- [ ] 重发提示的原话，是从原始字节里读的（`raw-analysis.json` 的 `notices_timed`），不只看最终画面。一闪而过的提示，最终画面上没有，属于正常现象。

**请求体和续写**
- [ ] 重发请求体的 assistant 历史里带没带半截（`record.json` 里重发请求的 `carries_partial`、`carries_tag`）。
- [ ] 如果带了：mock 的续写日志（`delivery.jsonl` 里的 `continuation.decision`）是续写还是重写？`continued` 只在"续写"、最终显示每段恰好一次、画面完整时成立。服务端重写、客户端把半截藏起来的情况，不能判成 `continued`。
- [ ] 下一轮请求（`next_request`）和会话文件（`conversation`）里，有没有失败的半截。

**对照**
- [ ] 每个工具的 F0-pre、F0-tag 都通过；F0-post 在**每次补跑之后**都重新跑过，结果一致。
- [ ] 阳性对照 F0-tag 的最终画面上恰好有 12 个失败标记。这证明标记能穿过这个工具的渲染器；否则"没看到标记"不能说明"没显示半截"。

**版本、哈希和隔离**
- [ ] 哈希是在清理之前记录的；前后两份版本证人一致（`manifest-*.json` 的 `versions_equal`）。
- [ ] 每次运行里，`lsof` 查到的实际执行文件的 sha256 等于钉死的原生二进制（codex 不能只算 `codex.js`）。
- [ ] mock 的 sha256 有记录，和冻结时一致。
- [ ] `lsregister` 结果里没有多出来的登记；`egress.json` 里被拦下的外连有没有异常。

**公开前**
- [ ] 公开副本是用 `export_public.py` 从证据目录导出的，源目录前后哈希一致，禁用串扫描和 `audit_artifacts.py` 都无命中。
- [ ] 公开副本里没有：本机用户路径、邮箱、账号 ID、device ID、第三方系统提示词，以及任何内部项目名和同事名字。
- [ ] 第三方的发现，先有上游 issue，再有公开报告（posting gate，见 `skills/repo-quake/references/reporting.md`）。

---

## 占位符清单

| 占位符 | 含义 |
|---|---|
| `<仓库>` | repo-quake 的本地克隆 |
| `<证据目录>` | 本轮证据根目录，放在公开仓库之外，也不在 `/tmp` 下 |
| `<被测工具清单>` | 例如 `claude codex` |
| `<claude 路径>`、`<codex 路径>`、`<kimi 路径>` | 各工具的启动文件 |
| `<claude 版本>`、`<codex 版本>`、`<kimi 版本>` | 期望版本，要出现在 `--version` 的输出里 |
| `<给被测程序的 PATH>` | `env -i` 之后给被测程序的 PATH，要包含 node 和各工具所在目录 |
| `<开始时刻>`、`<结束时刻>` | 矩阵的起止时刻，`log show` 的格式 |
| `<用户自己的 Applications 目录>` | 正常安装的 Claude Code URL Handler 所在目录 |
| `<本文件路径>` | 这份模板派发时的路径 |
