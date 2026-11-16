# 流中途断开、自动重发之后的显示：汇总

由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。

## 矩阵 `20261116T093337-28690`

- 时间：2026-11-16T01:33:38.369+00:00 → 2026-11-16T01:41:30.423+00:00
- 工具：codex；条件：F0-pre, F1-always, F6-always, F0-post；每格 3 次；模式 interactive
- tmux：[110, 400]；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` e7fef77a7d9d37f8，`content.json` 1e7aa28970310b2c，`runner.py` e507c4b8fb5c9882，`grading.py` 506b8d112f11be4c，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：—

- codex：`codex-cli 0.169.0`，启动文件 sha256 e14fc83739c13c10，实际执行的二进制 sha256 739cda86e15d30a6

## 判定总表（交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| codex | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F1-always | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 6 / 6 |
| codex | F0-post | 3 | healthy 3/3 | — | 1 / 1 |
| codex | F6-always | 3 | reported_failure 3/3 | detected✓、recovered✗、reported✓ | 6 / 6 |

运行时核对（每次运行对 tmux 面板进程做 `lsof`，看实际执行的文件）：
- codex：sha256 739cda86e15d30a6，12 次

## 逐次证人（故障格）

| 工具 | 条件 | 次 | 判定 | 故障流（相对重发开始，ms） | 原始字节首见标记 | 中途截图 | 标记在屏时段 | 重叠截图 | 最终画面完整 | 下一轮带半截 | 原始字节里的提示（相对 FIN，ms） |
|---|---|---:|---|---|---:|---:|---|---|---|---|---|

## 前后 F0 对照

| 工具 | F0-pre | F0-post |
|---|---|---|
| codex | healthy, healthy, healthy | healthy, healthy, healthy |

## 无效、n/a 与对照失败

- 无

## 沙箱拦下的外连

```json
{
  "window": [
    "2026-11-16 09:33:34",
    "2026-11-16 09:41:30"
  ],
  "denials": 58,
  "by_target": {
    "codex -> /private/var/run/mDNSResponder": 58
  },
  "first": [
    {
      "time": "2026-11-16 09:33:35.515685+0800",
      "process": "codex",
      "pid": 28651,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:35.674137+0800",
      "process": "codex",
      "pid": 28651,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:36.334504+0800",
      "process": "codex",
      "pid": 28651,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:36.874919+0800",
      "process": "codex",
      "pid": 28651,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:38.916960+0800",
      "process": "codex",
      "pid": 28700,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:39.042718+0800",
      "process": "codex",
      "pid": 28700,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:41.536833+0800",
      "process": "codex",
      "pid": 28700,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:45.570052+0800",
      "process": "codex",
      "pid": 28700,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:46.866175+0800",
      "process": "codex",
      "pid": 28921,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:46.991408+0800",
      "process": "codex",
      "pid": 28921,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:47.883245+0800",
      "process": "codex",
      "pid": 28921,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:53.339367+0800",
      "process": "codex",
      "pid": 28921,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:54.548986+0800",
      "process": "codex",
      "pid": 29141,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:54.684232+0800",
      "process": "codex",
      "pid": 29141,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:33:59.277310+0800",
      "process": "codex",
      "pid": 29141,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:34:01.095605+0800",
      "process": "codex",
      "pid": 29141,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:34:02.341351+0800",
      "process": "codex",
      "pid": 29328,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:34:02.471094+0800",
      "process": "codex",
      "pid": 29328,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:34:04.355508+0800",
      "process": "codex",
      "pid": 29328,
      "target": "/private/var/run/mDNSResponder"
    },
    {
      "time": "2026-11-16 09:35:02.310710+0800",
      "process": "codex",
      "pid": 29328,
      "target": "/private/var/run/mDNSResponder"
    }
  ]
}
```

## LaunchServices 登记

```json
{
  "at": "2026-11-16T01:42:00.321+00:00",
  "claude_url_handler_paths": [
    "<HOME>/Applications/Claude Code URL Handler.app (0x1548)"
  ]
}
```

