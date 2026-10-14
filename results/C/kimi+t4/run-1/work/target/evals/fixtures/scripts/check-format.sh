#!/usr/bin/env bash
# 格式校验脚本（judge.type: script）：退出码 0 = PASS，非 0 = FAIL
# 检查 greeting-card 的格式硬规则：
#   1. 输出非空
#   2. 中文卡片长度不超过 80 字符
#   3. 恰好一个 emoji，且位于消息结尾（允许 emoji 后跟 VS16 修饰符）
#   4. 不以 "Dear"/"亲爱的"/markdown 标题开头，不含 markdown 加粗/代码标记
set -u

python3 - <<'PY'
import os
import re
import sys

msg = (os.environ.get("EVAL_FINAL_MESSAGE") or "").strip()


def fail(reason):
    print(f"FAIL: {reason}", file=sys.stderr)
    sys.exit(1)


if not msg:
    fail("输出为空")

if len(msg) > 80:
    fail(f"长度 {len(msg)} 字符，超过 80 字符上限")

if msg.startswith(("Dear", "亲爱的", "#")):
    fail("以称呼或 markdown 标题开头")

if "**" in msg or "`" in msg:
    fail("包含 markdown 格式标记")

# emoji 基础字符（不含 VS16 U+FE0F、ZWJ U+200D 等修饰符）
emoji_base = re.compile(
    "[\U0001F000-\U0001FAFF" + chr(0x2B00) + "-" + chr(0x2BFF)
    + chr(0x2600) + "-" + chr(0x27BF) + "]"
)
matches = list(emoji_base.finditer(msg))
if len(matches) != 1:
    fail(f"emoji 数量为 {len(matches)}，要求恰好 1 个")

tail = msg[matches[0].end():]
if tail not in ("", "\uFE0F"):  # 空或仅 VS16 修饰符
    fail("emoji 不在消息结尾")

sys.exit(0)
PY
