# 流中途断开、自动重发之后的显示：汇总

由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。

## 矩阵 `20261116T161918-90843`

- 时间：2026-11-16T08:19:18.463+00:00 → 2026-11-16T08:26:31.120+00:00
- 工具：metacodes；条件：F0-pre, F0-tag, F0T-tag, F1-once, F6-once, FLONG-once, FTHINK1-once, FTHINK6-once, F0-post；每格 3 次；模式 interactive
- tmux：[110, 400]；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` d9115c9385ccc48a，`content.json` 1e7aa28970310b2c，`runner.py` 0bd3acf518be7e0b，`grading.py` 1cc52258b4c28563，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：32f1bc2846dfc230

- metacodes：`metacodes 0.12.1-dev+1707da0c6768
commit 1707da0c676863f62d99d58b1e33d0956cf21d1d
zig 0.16.0
target aarch64-macos-none ReleaseSmall
agentcore-abi v1 revision 28
config-schema 1
ripgrep 15.2.0 (e89fff89ac) expected sha256 a326a1fb48074202e9ad41e4cd1e389eeea372c8c6f7d7e80da81176d5d9430e
tinykg 0.3.0 (0b04014ba8d0bcb1f9f73c63c12e49f3c2ee1ece) expected sha256 dd53db2aa5219e899daac3caac2332648ac392550fa6f431b5900a1d495688e1
layout development`，启动文件 sha256 ee7718a91d7d3baa，实际执行的二进制 sha256 ee7718a91d7d3baa

## 矩阵 `20261116T162631-4742`

- 时间：2026-11-16T08:26:31.500+00:00 → 2026-11-16T08:37:02.751+00:00
- 工具：metacodes, metacodes-json, metacodes-sjson；条件：F0-pre, F0-tag, F0T-tag, F1-once, F6-once, FLONG-once, FTHINK1-once, FTHINK6-once, F0-post；每格 3 次；模式 noninteractive
- tmux：None；沙箱：True；静默窗口 60.0 s；稳定判据 3.0 s；截屏间隔 0.03 s
- 前后版本和哈希一致：True
- 装置哈希：`mock.mjs` d9115c9385ccc48a，`content.json` 1e7aa28970310b2c，`runner.py` 0bd3acf518be7e0b，`grading.py` 1cc52258b4c28563，`version_witness.py` c7db93d903d63c07，`rawtap.py` dadfc1666abe8b4b
- 实验卡 sha256：32f1bc2846dfc230

- metacodes：`metacodes 0.12.1-dev+1707da0c6768
commit 1707da0c676863f62d99d58b1e33d0956cf21d1d
zig 0.16.0
target aarch64-macos-none ReleaseSmall
agentcore-abi v1 revision 28
config-schema 1
ripgrep 15.2.0 (e89fff89ac) expected sha256 a326a1fb48074202e9ad41e4cd1e389eeea372c8c6f7d7e80da81176d5d9430e
tinykg 0.3.0 (0b04014ba8d0bcb1f9f73c63c12e49f3c2ee1ece) expected sha256 dd53db2aa5219e899daac3caac2332648ac392550fa6f431b5900a1d495688e1
layout development`，启动文件 sha256 ee7718a91d7d3baa，实际执行的二进制 sha256 ee7718a91d7d3baa
- metacodes-json：`metacodes 0.12.1-dev+1707da0c6768
commit 1707da0c676863f62d99d58b1e33d0956cf21d1d
zig 0.16.0
target aarch64-macos-none ReleaseSmall
agentcore-abi v1 revision 28
config-schema 1
ripgrep 15.2.0 (e89fff89ac) expected sha256 a326a1fb48074202e9ad41e4cd1e389eeea372c8c6f7d7e80da81176d5d9430e
tinykg 0.3.0 (0b04014ba8d0bcb1f9f73c63c12e49f3c2ee1ece) expected sha256 dd53db2aa5219e899daac3caac2332648ac392550fa6f431b5900a1d495688e1
layout development`，启动文件 sha256 ee7718a91d7d3baa，实际执行的二进制 sha256 ee7718a91d7d3baa
- metacodes-sjson：`metacodes 0.12.1-dev+1707da0c6768
commit 1707da0c676863f62d99d58b1e33d0956cf21d1d
zig 0.16.0
target aarch64-macos-none ReleaseSmall
agentcore-abi v1 revision 28
config-schema 1
ripgrep 15.2.0 (e89fff89ac) expected sha256 a326a1fb48074202e9ad41e4cd1e389eeea372c8c6f7d7e80da81176d5d9430e
tinykg 0.3.0 (0b04014ba8d0bcb1f9f73c63c12e49f3c2ee1ece) expected sha256 dd53db2aa5219e899daac3caac2332648ac392550fa6f431b5900a1d495688e1
layout development`，启动文件 sha256 ee7718a91d7d3baa，实际执行的二进制 sha256 ee7718a91d7d3baa

## 判定总表（交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| metacodes | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes | F0T-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes | F1-once | 3 | fork 3/3 | contained✗、detected✓、recovered✓、reported✗ | 2 / 0 |
| metacodes | F6-once | 3 | fork 3/3 | contained✗、detected✓、recovered✓、reported✗ | 2 / 0 |
| metacodes | FLONG-once | 3 | fork 3/3 | contained✗、detected✓、recovered✓、reported✗ | 2 / 0 |
| metacodes | FTHINK1-once | 3 | fork 3/3 | contained✗、detected✓、recovered✓、reported✗ | 2 / 0 |
| metacodes | FTHINK6-once | 3 | fork 3/3 | contained✗、detected✓、recovered✓、reported✗ | 2 / 0 |
| metacodes | F0-post | 3 | healthy 3/3 | — | 1 / 0 |

运行时核对（每次运行对 tmux 面板进程做 `lsof`，看实际执行的文件）：
- metacodes：sha256 ee7718a91d7d3baa，27 次

## 逐次证人（故障格）

| 工具 | 条件 | 次 | 判定 | 故障流（相对重发开始，ms） | 原始字节首见标记 | 中途截图 | 标记在屏时段 | 重叠截图 | 最终画面完整 | 下一轮带半截 | 原始字节里的提示（相对 FIN，ms） |
|---|---|---:|---|---|---:|---:|---|---|---|---|---|
| metacodes | F1-once | 1 | fork | -887 → -595 | -843 | -836 | -836 → 最后 | +70（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | F1-once | 2 | fork | -898 → -602 | -856 | -841 | -841 → 最后 | +109（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | F1-once | 3 | fork | -890 → -597 | -847 | -816 | -816 → 最后 | +88（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | F6-once | 1 | fork | -899 → -605 | -855 | -824 | -824 → 最后 | +120（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | F6-once | 2 | fork | -902 → -607 | -859 | -829 | -829 → 最后 | +101（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | F6-once | 3 | fork | -939 → -643 | -895 | -882 | -882 → 最后 | +122（标记 12，首段 ×2） | 是 | 否 | 无 |
| metacodes | FLONG-once | 1 | fork | -25051 → -596 | -24734 | -24731 | -24731 → 最后 | +482（标记 160，首段 ×2） | 是 | 否 | 无 |
| metacodes | FLONG-once | 2 | fork | -25093 → -583 | -24776 | -24773 | -24773 → 最后 | +498（标记 160，首段 ×2） | 是 | 否 | 无 |
| metacodes | FLONG-once | 3 | fork | -25082 → -607 | -24763 | -24760 | -24760 → 最后 | +495（标记 160，首段 ×2） | 是 | 否 | 无 |
| metacodes | FTHINK1-once | 1 | fork | -779 → -611 | -736 | -707 | -707 → 最后 | 无 | 是 | 否 | 无 |
| metacodes | FTHINK1-once | 2 | fork | -790 → -620 | -746 | -734 | -734 → 最后 | 无 | 是 | 否 | 无 |
| metacodes | FTHINK1-once | 3 | fork | -800 → -629 | -757 | -746 | -746 → 最后 | 无 | 是 | 否 | 无 |
| metacodes | FTHINK6-once | 1 | fork | -799 → -608 | -756 | -722 | -722 → 最后 | 无 | 是 | 否 | 无 |
| metacodes | FTHINK6-once | 2 | fork | -790 → -621 | -748 | -714 | -714 → 最后 | 无 | 是 | 否 | 无 |
| metacodes | FTHINK6-once | 3 | fork | -778 → -609 | -735 | -727 | -727 → 最后 | 无 | 是 | 否 | 无 |

## FLONG 断开前一刻

| 工具 | 次 | 断开前截图里的 L 编号（唯一） | 断开前画面完整 |
|---|---:|---:|---|
| metacodes | 1 | 150 | 是 |
| metacodes | 2 | 150 | 是 |
| metacodes | 3 | 150 | 是 |

## 前后 F0 对照

| 工具 | F0-pre | F0-post |
|---|---|---|
| metacodes | healthy, healthy, healthy | healthy, healthy, healthy |

## 无效、n/a 与对照失败

- 无

## 判定总表（非交互模式）

| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |
|---|---|---:|---|---|---|
| metacodes | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes | F0T-tag | 3 | thinking_hidden 3/3 | — | 1 / 0 |
| metacodes | F1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes | F6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes | FLONG-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes | FTHINK1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes | FTHINK6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes | F0-post | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes-json | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes-json | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes-json | F0T-tag | 3 | thinking_hidden 3/3 | — | 1 / 0 |
| metacodes-json | F1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-json | F6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-json | FLONG-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-json | FTHINK1-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-json | FTHINK6-once | 3 | not_shown 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-json | F0-post | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes-sjson | F0-pre | 3 | healthy 3/3 | — | 1 / 0 |
| metacodes-sjson | F0-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes-sjson | F0T-tag | 3 | tag_visible 3/3 | — | 1 / 0 |
| metacodes-sjson | F1-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-sjson | F6-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-sjson | FLONG-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-sjson | FTHINK1-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-sjson | FTHINK6-once | 3 | retracted 3/3 | contained✓、detected✓、recovered✓、reported✓ | 2 / 0 |
| metacodes-sjson | F0-post | 3 | healthy 3/3 | — | 1 / 0 |

## 逐次证人（非交互，故障格）

| 工具 | 条件 | 次 | 判定 | 退出码 | 正式请求 | stdout 里的失败标记 | 消费者读到的失败标记 | 丢弃段 | stderr/结果里的提示 |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| metacodes | F1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=9a6aa1480001][0m stream returned error RequestFailed at turn 1 |
| metacodes | F1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=22a514a80001][0m stream returned error RequestFailed at turn 1 |
| metacodes | F1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=a8ac40d00001][0m stream returned error RequestFailed at turn 1 |
| metacodes | F6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=30172b480001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes | F6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=b5653cb80001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes | F6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=3b4bd5080001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes | FLONG-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=c0b3b3f00001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FLONG-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=010966b80001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FLONG-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=4281b7f00001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FTHINK1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=7f5cbb180001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FTHINK1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=e6ea8eb80001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FTHINK1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=4eee59900001][0m stream returned error RequestFailed at turn 1 |
| metacodes | FTHINK6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=b6cf65e00001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes | FTHINK6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=3bb13c480001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes | FTHINK6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=a640da500001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | F1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=825e8e300001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | F1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=0a7d4fb80001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | F1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=91429fa80001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | F6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=1781e7180001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | F6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=9dc85a780001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | F6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=234995900001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | FLONG-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=aa2586780001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FLONG-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=0a9e13780001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FLONG-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=4cf75a880001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FTHINK1-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=85dab9c80001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FTHINK1-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=0c415f580001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FTHINK1-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=74242ce00001][0m stream returned error RequestFailed at turn 1 |
| metacodes-json | FTHINK6-once | 1 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=dca050500001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | FTHINK6-once | 2 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=4490e1480001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-json | FTHINK6-once | 3 | not_shown | 0 | 2 | 0 | 0 | — | [31m[ERROR agent req=ab277fc00001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | F1-once | 1 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=89dd4b700001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | F1-once | 2 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=0eefe6380001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | F1-once | 3 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=949d98200001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | F6-once | 1 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=1b3f4ae00001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | F6-once | 2 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=a0946ce80001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | F6-once | 3 | retracted | 0 | 2 | 12 | 0 | 1 | [31m[ERROR agent req=25d5c0a00001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | FLONG-once | 1 | retracted | 0 | 2 | 160 | 0 | 1 | [31m[ERROR agent req=ae0c7ae00001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FLONG-once | 2 | retracted | 0 | 2 | 160 | 0 | 1 | [31m[ERROR agent req=eeae32980001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FLONG-once | 3 | retracted | 0 | 2 | 160 | 0 | 1 | [31m[ERROR agent req=4ca8abf00001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FTHINK1-once | 1 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=aa695c500001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FTHINK1-once | 2 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=12cc81500001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FTHINK1-once | 3 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=7cf049e00001][0m stream returned error RequestFailed at turn 1 |
| metacodes-sjson | FTHINK6-once | 1 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=e53ef4b00001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | FTHINK6-once | 2 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=4db8ab080001][0m stream returned error StreamIncomplete at turn 1 |
| metacodes-sjson | FTHINK6-once | 3 | retracted | 0 | 2 | 6 | 0 | 1 | [31m[ERROR agent req=b638c6180001][0m stream returned error StreamIncomplete at turn 1 |

## 沙箱拦下的外连

```json
{
  "window": [
    "2026-11-16 16:19:13",
    "2026-11-16 16:37:02"
  ],
  "denials": 0,
  "by_target": {},
  "first": []
}
```

## LaunchServices 登记

```json
{
  "at": "2026-11-16T08:47:34.127+00:00",
  "claude_url_handler_paths": [
    "<HOME>/Applications/Claude Code URL Handler.app (0x1548)"
  ]
}
```

