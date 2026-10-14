#!/usr/bin/env bash
# greeting-card 格式校验脚本（script judge）
# 约定：退出码 0 = PASS，非 0 = FAIL；Agent 最终输出在 $EVAL_FINAL_MESSAGE。
set -u

# 统一 UTF-8 locale，保证按字符计数而非按字节
if locale -a 2>/dev/null | grep -qiE '^C\.UTF-8$'; then
  export LC_ALL=C.UTF-8
else
  export LC_ALL=en_US.UTF-8
fi

msg="${EVAL_FINAL_MESSAGE:-}"
fail() { echo "FAIL: $1" >&2; exit 1; }

[ -n "$msg" ] || fail "输出为空"

# 去掉首尾空白后再判定
trimmed="$(printf '%s' "$msg" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
[ -n "$trimmed" ] || fail "输出只有空白字符"

# 1. 中文贺卡不超过 80 个字符
len=${#trimmed}
[ "$len" -le 80 ] || fail "文案长度 ${len} 字符，超过 80 字上限"

# 2. 恰好一个 emoji（覆盖常见 emoji 码位区间）
emoji_count=$(printf '%s' "$trimmed" | perl -CSD -ne 'my @m = /[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}]/g; print scalar @m')
[ "$emoji_count" = "1" ] || fail "emoji 数量为 ${emoji_count}，要求恰好 1 个"

# 3. emoji 位于文案末尾
printf '%s' "$trimmed" | perl -CSD -ne 'exit(/[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}]\s*\z/ ? 0 : 1)' \
  || fail "emoji 不在文案末尾"

# 4. 不使用 markdown 格式
printf '%s' "$trimmed" | grep -qE '(\*\*|`|^#|\[[^]]+\]\()' && fail "文案包含 markdown 格式"

# 5. 不以 Dear 开头
printf '%s' "$trimmed" | grep -qiE '^dear' && fail "文案以 Dear 开头"

echo "PASS: 长度 ${len} 字符，恰好 1 个结尾 emoji，无 markdown"
exit 0
