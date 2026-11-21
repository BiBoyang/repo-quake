#!/usr/bin/env bash
# greeting-card 格式校验脚本，供 judge.type: script 使用。
# 约定：退出码 0 = PASS，非 0 = FAIL；Agent 最终输出在 $EVAL_FINAL_MESSAGE。
set -euo pipefail

msg="${EVAL_FINAL_MESSAGE:-}"

# 输出不能为空
if [ -z "$msg" ]; then
  echo "FAIL: 输出为空"
  exit 1
fi

# 长度上限：中文 80 字约 240 字节（UTF-8 每字 3 字节），加 emoji 与标点余量取 260 字节
bytes=$(printf '%s' "$msg" | wc -c | tr -d ' ')
if [ "$bytes" -gt 260 ]; then
  echo "FAIL: 贺卡超长（${bytes} 字节 > 260 字节）"
  exit 1
fi

# 不允许 markdown 标记
case "$msg" in
  *'# '*|*'**'*|*'`'*)
    echo "FAIL: 检出 markdown 标记"
    exit 1
    ;;
esac

# 不以称呼开头（tone-guide：除非用户要求正式风格，否则不要以 Dear 开头）
case "$msg" in
  Dear*|亲爱的*)
    echo "FAIL: 以称呼开头"
    exit 1
    ;;
esac

echo "PASS: 格式校验通过（${bytes} 字节）"
exit 0
