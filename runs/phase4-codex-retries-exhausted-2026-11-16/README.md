# 第 4 期补跑：codex 重试次数用完时的显示（2026-11-16，探索性）

**这批运行不在冻结的实验卡里，没有预注册。**起因有两个：
- 11-14 主矩阵里，codex 交互 F1-always 的最终画面上有两份以上的 P01–P12。那是旧装置在 35 行窗口里截的，数不清总份数。
- 上游 [openai/codex#47538](https://github.com/openai/codex/issues/47538) 里有一条评论，按源码预测了"重试用完时，几次尝试的文字会拼在一起留下来"。

为了在补充上游证据之前把这件事测准，才跑了这批。

## 怎么跑的

- 装置和第 4 期补测相同（`witness/stream-retry/`，三个核心文件的哈希与冻结版一致，见 `summary.md`）。窗口 110×400，`env -i` 白名单 + 一次性 HOME，沙箱只放行 localhost，只连本机 mock。
- 被测：codex-cli 0.169.0（实际执行的原生二进制 sha256 `739cda86…`，12/12 次运行核对一致；前后版本和哈希一致）。
- 条件：F0-pre、F1-always、F6-always、F0-post，各 3 次。always 表示正式回答的每一次请求都出故障：F1 在 P01–P12 后断开 TCP；F6 在 P01–P12 后让 HTTP 正文正常结束，但不发 `response.completed`。

## 结果

- 对照：F0-pre、F0-post 都是 healthy 3/3。
- F1-always、F6-always 各 3/3：codex 一共发 6 次正式请求（第一次加 `Reconnecting... 1/5` 到 `5/5`），每次的 P01–P12 都接在同一条消息后面。报错 `■ stream disconnected before completion: …` 之后也不收，最终画面上 6 份 P01–P12 首尾相接。会话文件里这一轮没有 assistant 记录（0 条），所以错的只是显示。逐次数据在 `retries-exhausted-counts.json`，由各次的 `final-view.txt` 数出。
- 和重发成功的情况一起，已补到上游：[openai/codex#47538 的评论](https://github.com/openai/codex/issues/47538#issuecomment-6905066983)（2026-11-16 01:47Z，读回与 `upstream-repro/comment-47538.md` 逐字一致）。

## `upstream-repro/`

- `retry_dup_mock.py`：评论里附的最小复现（Python 标准库），和评论中的代码逐字相同。
- `comment-47538.md`：发出的评论原文。
- `once-*`、`always-*`：用最小复现对 codex 0.169.0 各跑 1 次的截屏和时间线（每 0.1 s 截一次）。只断一次时，两份同屏约 6 秒，然后收成一份；`--always` 时每次重发多一份，最后 6 份留在屏上。

本目录的其余文件由 `witness/stream-retry/export_public.py` 导出（见 `EXPORT.md`）；`upstream-repro/` 和 `retries-exhausted-counts.json` 是导出后另加的，在副本上做了同样的路径脱敏，并和全目录一起重新做了禁用串扫描与 `audit_artifacts.py` 审计。
