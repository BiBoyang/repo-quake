# 流中途断开、自动重发之后的显示：汇总

由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。

## 矩阵 `20261115T230639-62330`

- 时间：2026-11-15T15:06:40.210+00:00 → 2026-11-15T15:17:02.598+00:00
- 工具：claude, codex；条件：F0-pre, F0-tag, F1-once, F6-once, FLONG-once, F0-post；每格 3 次；模式 interactive
- tmux：[110, 400]；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` e7fef77a7d9d37f8，`content.json` 1e7aa28970310b2c，`runner.py` e507c4b8fb5c9882，`grading.py` 506b8d112f11be4c，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：66fcde0a3c5741cb

- claude：`2.1.282 (Claude Code)`，启动文件 sha256 fcfd837103965c64，实际执行的二进制 sha256 fcfd837103965c64
- codex：`codex-cli 0.169.0`，启动文件 sha256 e14fc83739c13c10，实际执行的二进制 sha256 739cda86e15d30a6

## 判定总表（交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| claude | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| claude | F0-tag | 3 | tag_visible 3/3 | — | 1 / 1 |
| claude | F1-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| claude | F6-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| claude | FLONG-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| claude | F0-post | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F0-tag | 3 | tag_visible 3/3 | — | 1 / 1 |
| codex | F1-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| codex | F6-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| codex | FLONG-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓ | 2 / 1 |
| codex | F0-post | 3 | healthy 3/3 | — | 1 / 1 |

运行时核对（每次运行对 tmux 面板进程做 `lsof`，看实际执行的文件）：
- claude：sha256 fcfd837103965c64，18 次
- codex：sha256 739cda86e15d30a6，18 次

## 逐次证人（故障格）

| 工具 | 条件 | 次 | 判定 | 故障流（相对重发开始，ms） | 原始字节首见标记 | 中途截图 | 标记在屏时段 | 重叠截图 | 最终画面完整 | 下一轮带半截 | 原始字节里的提示（相对 FIN，ms） |
|---|---|---:|---|---|---:|---:|---|---|---|---|---|
| claude | F1-once | 1 | retracted | -888 → -581 | -734 | -718 | -718 → -532 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+6） |
| claude | F1-once | 2 | retracted | -921 → -614 | -770 | -752 | -752 → -607 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+5） |
| claude | F1-once | 3 | retracted | -887 → -586 | -734 | -716 | -716 → -578 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+5） |
| claude | F6-once | 1 | retracted | -864 → -545 | -710 | -677 | -677 → -527 | 无 | 是 | 否 | Connection closed before the response finished · Retrying in 1s · attempt 1/1（+5） |
| claude | F6-once | 2 | retracted | -827 → -526 | -673 | -651 | -651 → -463 | 无 | 是 | 否 | Connection closed before the response finished · Retrying in 1s · attempt 1/1（+17） |
| claude | F6-once | 3 | retracted | -882 → -576 | -725 | -698 | -698 → -535 | 无 | 是 | 否 | Connection closed before the response finished · Retrying in 1s · attempt 1/1（+7） |
| claude | FLONG-once | 1 | retracted | -25230 → -618 | -24807 | -24795 | -24795 → -602 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+11） |
| claude | FLONG-once | 2 | retracted | -25204 → -562 | -24786 | -24739 | -24739 → -486 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+36） |
| claude | FLONG-once | 3 | retracted | -25223 → -588 | -24809 | -24792 | -24792 → -562 | 无 | 是 | 否 | API error · Retrying in 1s · attempt 1/10（+8） |
| codex | F1-once | 1 | retracted | -550 → -223 | -469 | -446 | -446 → +670 | +127（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+5）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+5） |
| codex | F1-once | 2 | retracted | -548 → -220 | -469 | -434 | -434 → +660 | +91（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+16）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+16） |
| codex | F1-once | 3 | retracted | -512 → -189 | -431 | -405 | -405 → +630 | +109（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+5）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+5） |
| codex | F6-once | 1 | retracted | -520 → -198 | -441 | -406 | -406 → +662 | +115（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+4）；└ Stream disconnected before completion: stream closed before response.completed（+4） |
| codex | F6-once | 2 | retracted | -533 → -217 | -453 | -421 | -421 → +666 | +83（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+5）；└ Stream disconnected before completion: stream closed before response.completed（+5） |
| codex | F6-once | 3 | retracted | -558 → -224 | -471 | -455 | -455 → +637 | +97（标记 12，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+5）；└ Stream disconnected before completion: stream closed before response.completed（+5） |
| codex | FLONG-once | 1 | retracted | -24933 → -189 | -24464 | -24438 | -24438 → +31021 | +516（标记 160，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+9）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+9） |
| codex | FLONG-once | 2 | retracted | -24958 → -186 | -24485 | -24468 | -24468 → +31052 | +487（标记 160，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+9）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+9） |
| codex | FLONG-once | 3 | retracted | -24986 → -232 | -24513 | -24478 | -24478 → +31091 | +530（标记 160，首段 ×2） | 是 | 否 | Reconnecting... 1/5（+49）；└ Stream disconnected before completion: Transport error: network error: error decoding response body（+49） |

## FLONG 断开前一刻

| 工具 | 次 | 断开前截图里的 L 编号（唯一） | 断开前画面完整 |
|---|---:|---:|---|
| claude | 1 | 150 | 是 |
| claude | 2 | 150 | 是 |
| claude | 3 | 150 | 是 |
| codex | 1 | 150 | 是 |
| codex | 2 | 150 | 是 |
| codex | 3 | 150 | 是 |

## 前后 F0 对照

| 工具 | F0-pre | F0-post |
|---|---|---|
| claude | healthy, healthy, healthy | healthy, healthy, healthy |
| codex | healthy, healthy, healthy | healthy, healthy, healthy |

## 无效、n/a 与对照失败

- 无

## 沙箱拦下的外连

```json
{
  "window": [
    "2026-11-15 23:06:26",
    "2026-11-15 23:17:02"
  ],
  "denials": 60,
  "by_target": {
    "codex -> /private/var/run/mDNSResponder": 60
  },
  "first": [
    {
      "time": "2026-11-15 23:06:40.596012+0800",
      "process": "codex",
      "pid": 62277,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:51.779453+0800",
      "process": "codex",
      "pid": 75771,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:51.938851+0800",
      "process": "codex",
      "pid": 75771,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:56.170399+0800",
      "process": "codex",
      "pid": 75771,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:58.557433+0800",
      "process": "codex",
      "pid": 75771,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:59.752162+0800",
      "process": "codex",
      "pid": 76222,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:11:59.902106+0800",
      "process": "codex",
      "pid": 76222,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:00.540371+0800",
      "process": "codex",
      "pid": 76222,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:06.296245+0800",
      "process": "codex",
      "pid": 76222,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:07.540731+0800",
      "process": "codex",
      "pid": 76881,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:07.676142+0800",
      "process": "codex",
      "pid": 76881,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:07.810428+0800",
      "process": "codex",
      "pid": 76881,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:14.009018+0800",
      "process": "codex",
      "pid": 76881,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:15.258779+0800",
      "process": "codex",
      "pid": 78192,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:15.417712+0800",
      "process": "codex",
      "pid": 78192,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:15.468424+0800",
      "process": "codex",
      "pid": 78192,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:21.488899+0800",
      "process": "codex",
      "pid": 78192,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:22.736316+0800",
      "process": "codex",
      "pid": 79074,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:22.868578+0800",
      "process": "codex",
      "pid": 79074,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-15 23:12:22.956113+0800",
      "process": "codex",
      "pid": 79074,
      "target": "/private/var/run/mDNSResponder"
    }
  ]
}
```

## LaunchServices 登记

```json
{
  "at": "2026-11-15T15:17:27.161+00:00",
  "claude_url_handler_paths": [
    "<HOME>/Applications/Claude Code URL Handler.app (0x1548)"
  ]
}
```

