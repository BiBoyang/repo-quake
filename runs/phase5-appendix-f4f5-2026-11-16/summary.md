# 流中途断开、自动重发之后的显示：汇总

由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。

## 矩阵 `20261116T165016-18790`

- 时间：2026-11-16T08:50:16.847+00:00 → 2026-11-16T08:59:55.238+00:00
- 工具：claude, codex；条件：F0-pre, F0-tag, F4-once, F5-once, F0-post；每格 3 次；模式 interactive
- tmux：[110, 400]；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` d9115c9385ccc48a，`content.json` 1e7aa28970310b2c，`runner.py` 0bd3acf518be7e0b，`grading.py` 1cc52258b4c28563，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：0e860304892e99ad

- claude：`2.1.282 (Claude Code)`，启动文件 sha256 fcfd837103965c64，实际执行的二进制 sha256 fcfd837103965c64
- codex：`codex-cli 0.169.0`，启动文件 sha256 e14fc83739c13c10，实际执行的二进制 sha256 739cda86e15d30a6

## 矩阵 `20261116T165955-40745`

- 时间：2026-11-16T08:59:56.087+00:00 → 2026-11-16T09:00:41.724+00:00
- 工具：claude, codex；条件：F0-pre, F0-tag, F4-once, F5-once, F0-post；每格 3 次；模式 noninteractive
- tmux：None；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` d9115c9385ccc48a，`content.json` 1e7aa28970310b2c，`runner.py` 0bd3acf518be7e0b，`grading.py` 1cc52258b4c28563，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：0e860304892e99ad

- claude：`2.1.282 (Claude Code)`，启动文件 sha256 fcfd837103965c64，实际执行的二进制 sha256 fcfd837103965c64
- codex：`codex-cli 0.169.0`，启动文件 sha256 e14fc83739c13c10，实际执行的二进制 sha256 739cda86e15d30a6

## 判定总表（交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| claude | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| claude | F0-tag | 3 | tag_visible 3/3 | — | 1 / 1 |
| claude | F4-once | 3 | length_continued 3/3 | detected✓、reported✗ | 2 / 1 |
| claude | F5-once | 3 | length_retried 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| claude | F0-post | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F0-tag | 3 | tag_visible 3/3 | — | 1 / 1 |
| codex | F4-once | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 1 / 1 |
| codex | F5-once | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 1 / 1 |
| codex | F0-post | 3 | healthy 3/3 | — | 1 / 1 |

运行时核对（每次运行对 tmux 面板进程做 `lsof`，看实际执行的文件）：
- claude：sha256 fcfd837103965c64，15 次
- codex：sha256 739cda86e15d30a6，15 次

## 逐次证人（故障格）

| 工具 | 条件 | 次 | 判定 | 故障流（相对重发开始，ms） | 原始字节首见标记 | 中途截图 | 标记在屏时段 | 重叠截图 | 最终画面完整 | 下一轮带半截 | 原始字节里的提示（相对 FIN，ms） |
|---|---|---:|---|---|---:|---:|---|---|---|---|---|
| claude | F4-once | 1 | length_continued | — → — | — | — | — → 最后 | —（标记 12，首段 ×2） | 是 | 是 | 无 |
| claude | F4-once | 2 | length_continued | — → — | — | — | — → 最后 | —（标记 12，首段 ×2） | 是 | 是 | 无 |
| claude | F4-once | 3 | length_continued | — → — | — | — | — → 最后 | —（标记 12，首段 ×2） | 是 | 是 | 无 |
| claude | F5-once | 1 | length_retried | — → — | — | — | — → — | 无 | 是 | 否 | 无 |
| claude | F5-once | 2 | length_retried | — → — | — | — | — → — | 无 | 是 | 否 | 无 |
| claude | F5-once | 3 | length_retried | — → — | — | — | — → — | 无 | 是 | 否 | 无 |
| codex | F4-once | 1 | reported_failure | — → — | — | — | — → 最后 | 无 | 是 | 是 | 无 |
| codex | F4-once | 2 | reported_failure | — → — | — | — | — → 最后 | 无 | 是 | 是 | 无 |
| codex | F4-once | 3 | reported_failure | — → — | — | — | — → 最后 | 无 | 是 | 是 | 无 |
| codex | F5-once | 1 | reported_failure | — → — | — | — | — → — | 无 | 是 | 否 | 无 |
| codex | F5-once | 2 | reported_failure | — → — | — | — | — → — | 无 | 是 | 否 | 无 |
| codex | F5-once | 3 | reported_failure | — → — | — | — | — → — | 无 | 是 | 否 | 无 |

## 前后 F0 对照

| 工具 | F0-pre | F0-post |
|---|---|---|
| claude | healthy, healthy, healthy | healthy, healthy, healthy |
| codex | healthy, healthy, healthy | healthy, healthy, healthy |

## 无效、n/a 与对照失败

- 无

## 判定总表（非交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| claude | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| claude | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| claude | F4-once | 3 | length_continued 3/3 | detected✓、reported✗ | 2 / 0 |
| claude | F5-once | 3 | length_retried 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 0 |
| claude | F0-post | 3 | healthy 3/3 | — | 1 / 0 |
| codex | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| codex | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| codex | F4-once | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 1 / 0 |
| codex | F5-once | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 1 / 0 |
| codex | F0-post | 3 | healthy 3/3 | — | 1 / 0 |

## 逐次证人（非交互，故障格）

| 工具 | 条件 | 次 | 判定 | 退出码 | 正式请求 | stdout 里的失败标记 | 消费者读到的失败标记 | 丢弃段 | stderr/结果里的提示 |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| claude | F4-once | 1 | length_continued | 0 | 2 | 0 | 0 | — | 无 |
| claude | F4-once | 2 | length_continued | 0 | 2 | 0 | 0 | — | 无 |
| claude | F4-once | 3 | length_continued | 0 | 2 | 0 | 0 | — | 无 |
| claude | F5-once | 1 | length_retried | 0 | 2 | 0 | 0 | — | 无 |
| claude | F5-once | 2 | length_retried | 0 | 2 | 0 | 0 | — | 无 |
| claude | F5-once | 3 | length_retried | 0 | 2 | 0 | 0 | — | 无 |
| codex | F4-once | 1 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |
| codex | F4-once | 2 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |
| codex | F4-once | 3 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |
| codex | F5-once | 1 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |
| codex | F5-once | 2 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |
| codex | F5-once | 3 | reported_failure | 1 | 1 | 0 | 0 | — | ERROR: Incomplete response returned, reason: max_output_tokens |

## 沙箱拦下的外连

```json
{
  "window": [
    "2026-11-16 16:50:10",
    "2026-11-16 17:00:41"
  ],
  "denials": 55,
  "by_target": {
    "codex -> /private/var/run/mDNSResponder": 55
  },
  "first": [
    {
      "time": "2026-11-16 16:50:17.209877+0800",
      "process": "codex",
      "pid": 18735,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:20.047481+0800",
      "process": "codex",
      "pid": 22404,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:23.751636+0800",
      "process": "codex",
      "pid": 22621,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:27.838438+0800",
      "process": "codex",
      "pid": 22621,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:31.538437+0800",
      "process": "codex",
      "pid": 22861,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:39.283234+0800",
      "process": "codex",
      "pid": 22861,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:42.774549+0800",
      "process": "codex",
      "pid": 23056,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:45.796064+0800",
      "process": "codex",
      "pid": 23056,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:47.064236+0800",
      "process": "codex",
      "pid": 23233,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:47.205824+0800",
      "process": "codex",
      "pid": 23233,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:47.834823+0800",
      "process": "codex",
      "pid": 23233,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:53.554411+0800",
      "process": "codex",
      "pid": 23233,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:54.829061+0800",
      "process": "codex",
      "pid": 23500,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:52:54.960899+0800",
      "process": "codex",
      "pid": 23500,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:53:02.566161+0800",
      "process": "codex",
      "pid": 23500,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:53:02.566170+0800",
      "process": "codex",
      "pid": 23734,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:53:02.702811+0800",
      "process": "codex",
      "pid": 23734,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:53:44.950341+0800",
      "process": "codex",
      "pid": 23734,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:54:08.033169+0800",
      "process": "codex",
      "pid": 27260,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 16:55:13.180074+0800",
      "process": "codex",
      "pid": 27260,
      "target": "/private/var/run/mDNSResponder"
    }
  ]
}
```

## LaunchServices 登记

```json
{
  "at": "2026-11-16T09:01:03.899+00:00",
  "claude_url_handler_paths": [
    "<HOME>/Applications/Claude Code URL Handler.app (0x1548)"
  ]
}
```

