# 流中途断开、自动重发之后的显示：汇总

由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。

## 矩阵 `20261116T170952-52970`

- 时间：2026-11-16T09:09:52.875+00:00 → 2026-11-16T09:13:43.441+00:00
- 工具：dsh-cc, dsh-resp, dsh-anth；条件：F0-pre, F1-once, F2-once, F3-once, F4-once, F5-once, F6-once, F0-post；每格 3 次；模式 noninteractive
- tmux：None；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` 49440ba1a9daf492，`content.json` 1e7aa28970310b2c，`runner.py` d9e312344eaf9cae，`grading.py` cd9b4f7a6d74fc50，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：41d9989a08fbd0a6

- dsh-cc：`0.2.2-rc.3`，启动文件 sha256 36f86742e0c3cc1c，实际执行的二进制 sha256 —
- dsh-resp：`0.2.2-rc.3`，启动文件 sha256 36f86742e0c3cc1c，实际执行的二进制 sha256 —
- dsh-anth：`0.2.2-rc.3`，启动文件 sha256 36f86742e0c3cc1c，实际执行的二进制 sha256 —

## 判定总表（非交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| dsh-anth | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| dsh-anth | F1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-anth | F2-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-anth | F3-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-anth | F4-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-anth | F5-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-anth | F6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-anth | F0-post | 3 | healthy 3/3 | — | 1 / 1 |
| dsh-cc | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| dsh-cc | F1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-cc | F2-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-cc | F3-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-cc | F4-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-cc | F5-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-cc | F6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-cc | F0-post | 3 | healthy 3/3 | — | 1 / 1 |
| dsh-resp | F0-pre | 3 | healthy 3/3 | — | 1 / 1 |
| dsh-resp | F1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-resp | F2-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-resp | F3-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-resp | F4-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-resp | F5-once | 3 | exit_code_only 3/3 | detected✓、reported✗ | 1 / 1 |
| dsh-resp | F6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✗ | 2 / 1 |
| dsh-resp | F0-post | 3 | healthy 3/3 | — | 1 / 1 |

## 逐次证人（非交互，故障格）

| 工具 | 条件 | 次 | 判定 | 退出码 | 正式请求 | stdout 里的失败标记 | 消费者读到的失败标记 | 丢弃段 | stderr/结果里的提示 |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| dsh-anth | F1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F2-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F2-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F2-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F3-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F3-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F3-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F4-once | 1 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-anth | F4-once | 2 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-anth | F4-once | 3 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-anth | F5-once | 1 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-anth | F5-once | 2 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-anth | F5-once | 3 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-anth | F6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-anth | F6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F2-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F2-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F2-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F3-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F3-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F3-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F4-once | 1 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-cc | F4-once | 2 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-cc | F4-once | 3 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-cc | F5-once | 1 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-cc | F5-once | 2 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-cc | F5-once | 3 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-cc | F6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-cc | F6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F2-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F2-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F2-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F3-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F3-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F3-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F4-once | 1 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-resp | F4-once | 2 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-resp | F4-once | 3 | exit_code_only | 1 | 1 | 12 | 12 | — | 无 |
| dsh-resp | F5-once | 1 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-resp | F5-once | 2 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-resp | F5-once | 3 | exit_code_only | 1 | 1 | 0 | 0 | — | 无 |
| dsh-resp | F6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | 无 |
| dsh-resp | F6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | 无 |

## 沙箱拦下的外连

```json
{
  "window": [
    "2026-11-16 17:09:52",
    "2026-11-16 17:13:43"
  ],
  "denials": 0,
  "by_target": {},
  "first": []
}
```

