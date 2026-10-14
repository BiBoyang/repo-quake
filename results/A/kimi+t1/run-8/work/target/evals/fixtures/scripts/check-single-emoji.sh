#!/usr/bin/env bash
# 判定脚本：最终输出应恰好包含一个 emoji，且该 emoji 位于消息最末尾。
# 约定：退出码 0 = PASS，非 0 = FAIL；最终输出取自 $EVAL_FINAL_MESSAGE。
set -euo pipefail

msg="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$msg" ]; then
  echo "FAIL: EVAL_FINAL_MESSAGE is empty" >&2
  exit 1
fi

python3 - "$msg" <<'PY'
import re
import sys

msg = sys.argv[1]
# 常见 emoji 区间：表情符号、杂项符号、装饰符号、旗帜区域指示符等。
pattern = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️\U0001F1E6-\U0001F1FF]"
)
emojis = pattern.findall(msg)

if len(emojis) != 1:
    print(f"FAIL: expected exactly 1 emoji, found {len(emojis)}")
    sys.exit(1)

if not msg.rstrip().endswith(emojis[0]):
    print("FAIL: emoji is not at the very end of the message")
    sys.exit(1)

print("PASS: exactly one emoji at the end")
sys.exit(0)
PY
