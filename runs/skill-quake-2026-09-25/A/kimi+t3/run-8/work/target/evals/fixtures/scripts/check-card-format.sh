#!/bin/bash
# check-card-format.sh — greeting-card 格式规则判分脚本（script judge）
#
# 契约：
#   - 工作目录：用例 workspace 根目录
#   - 环境变量：EVAL_TRANSCRIPT_PATH、EVAL_FINAL_MESSAGE、EVAL_EXIT_CODE
#   - 退出码 0 → PASS，非 0 → FAIL
#   - stdout → 报告中的 evidence，stderr → 调试信息
#
# 校验项（对应 references/tone-guide.md 的格式硬规则）：
#   1. 输出非空
#   2. 恰好一个 emoji
#   3. emoji 位于消息末尾
#   4. 长度合规：中文 80 字以内（不计空白），或英文 60 词以内
#   5. 句子数 1-3 句（按句末标点分组计数）
#   6. 无 markdown 标记、无引号包裹、不以 "Dear"/"亲爱的" 开头

set -euo pipefail

echo "check-card-format.sh: EVAL_EXIT_CODE = ${EVAL_EXIT_CODE:-unset}" >&2

python3 - <<'PYEOF'
import os
import re
import sys

text = (os.environ.get("EVAL_FINAL_MESSAGE") or "").strip()

# 常见 emoji 码点范围；FE0F 变体选择符不算独立 emoji
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF"
    "☀-➿"
    "⬀-⯿]"
)

def fail(reason: str) -> None:
    print(f"FAIL: {reason}")
    sys.exit(1)

# 检查 1：输出非空
if not text:
    fail("输出为空")

# 检查 2：恰好一个 emoji
emojis = EMOJI_RE.findall(text)
if len(emojis) != 1:
    fail(f"期望恰好 1 个 emoji，实际 {len(emojis)} 个：{emojis}")

# 检查 3：emoji 在末尾（忽略尾部空白与变体选择符）
tail = text.rstrip().rstrip("️")
if not tail or not EMOJI_RE.fullmatch(tail[-1]):
    fail("emoji 未位于消息末尾")

# 检查 4：长度合规
cjk_count = len(re.findall(r"[一-鿿]", text))
if cjk_count > 0:
    compact = re.sub(r"\s", "", text)
    if len(compact) > 80:
        fail(f"中文卡片超长：{len(compact)} 字（上限 80，不计空白）")
else:
    words = len(text.split())
    if words > 60:
        fail(f"英文卡片超长：{words} 词（上限 60）")

# 检查 5：句子数 1-3（连续句末标点算一句）
body = EMOJI_RE.sub("", text)
sentences = re.findall(r"[.。!！?？]+", body)
if not 1 <= len(sentences) <= 3:
    fail(f"句子数 {len(sentences)} 不在 1-3 句范围内")

# 检查 6：无 markdown、无引号包裹、无 Dear/亲爱的 开头
if text.startswith("#") or "```" in text or "**" in text:
    fail("包含 markdown 标记")
if text[0] in "\"'「『《":
    fail("卡片被引号包裹")
if text.startswith("Dear") or text.startswith("亲爱的"):
    fail("以称呼头开头（tone-guide 禁止默认使用 Dear/亲爱的）")

print("PASS: 格式全部合规（1 个末尾 emoji、长度与句子数达标、无 markdown/引号/称呼头）")
PYEOF
