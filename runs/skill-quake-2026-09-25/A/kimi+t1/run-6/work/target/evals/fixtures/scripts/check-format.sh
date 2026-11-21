#!/usr/bin/env bash
# greeting-card 格式检查脚本：恰好一个 emoji 且位于末尾、无 markdown、1-3 句。
# 约定：退出码 0 = PASS，非 0 = FAIL；输入来自环境变量 EVAL_FINAL_MESSAGE。
set -u

msg="${EVAL_FINAL_MESSAGE:-}"
if [ -z "$msg" ]; then
  echo "FAIL: EVAL_FINAL_MESSAGE 为空"
  exit 1
fi

python3 - "$msg" <<'PY'
import re
import sys

msg = sys.argv[1].strip()
errors = []

# 1) 不使用 markdown 语法
if re.search(r"(^|\n)\s{0,3}#{1,6}\s", msg) or "**" in msg or "__" in msg or "`" in msg:
    errors.append("包含 markdown 格式")

# 2) 不以 Dear 开头，不用引号包裹正文
if msg.lower().startswith("dear"):
    errors.append("以 Dear 开头")
if msg[:1] in "\"'“‘" and msg[-1:] in "\"'”’":
    errors.append("正文被引号包裹")

# 3) 恰好一个 emoji，且位于末尾（容忍 emoji 后的变体选择符）
emoji_re = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
emojis = emoji_re.findall(msg)
if len(emojis) != 1:
    errors.append("emoji 数量为 %d，应为 1" % len(emojis))
elif not msg.rstrip("️").endswith(emojis[0]):
    errors.append("emoji 不在消息末尾")

# 4) 去掉 emoji 后正文为 1-3 句
body = emoji_re.sub("", msg).strip().strip("️")
sentences = [s for s in re.split(r"[。！？!?…]+", body) if s.strip()]
if not 1 <= len(sentences) <= 3:
    errors.append("句子数量为 %d，应在 1-3 之间" % len(sentences))

if errors:
    print("FAIL: " + "; ".join(errors))
    sys.exit(1)
print("PASS")
PY
