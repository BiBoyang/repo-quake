#!/usr/bin/env bash
# greeting-card 格式硬规则检查（script judge 用）
# 约定：退出码 0 = PASS，非 0 = FAIL；Agent 最终输出经 $EVAL_FINAL_MESSAGE 传入
set -euo pipefail

python3 - "${EVAL_FINAL_MESSAGE:-}" <<'PY'
import re
import sys

text = (sys.argv[1] or "").strip()
errors = []

if not text:
    print("FAIL: 输出为空", file=sys.stderr)
    sys.exit(1)

# 句数：按句末标点分组计数；完全没有句末标点时按 1 句处理
sentence_marks = re.findall(r"[。！？!?.…]+", text)
sentences = max(1, len(sentence_marks))
if sentences > 3:
    errors.append(f"句子数为 {sentences}，超过 1-3 句上限")

# 长度：中文不超过 80 字符，英文不超过 60 词
if re.search(r"[一-鿿]", text):
    if len(text) > 80:
        errors.append(f"中文卡片长度为 {len(text)} 字符，超过 80 上限")
else:
    words = len(text.split())
    if words > 60:
        errors.append(f"英文卡片长度为 {words} 词，超过 60 上限")

# emoji：恰好一个簇，且位于末尾；VS16 忽略、ZWJ 序列按一个簇计
emoji_char = re.compile(
    "[\U0001F000-\U0001FAFF⌀-➿⬀-⯿〰〽㊗㊙]"
)
core = text.replace("️", "")  # 去掉 VS16
clusters = 0
prev_zwj = False
for ch in core:
    if ch == "‍":  # ZWJ：连接前后 emoji 为同一簇
        prev_zwj = True
        continue
    if emoji_char.match(ch):
        if not prev_zwj:
            clusters += 1
        prev_zwj = False
    else:
        prev_zwj = False
if clusters != 1:
    errors.append(f"emoji 为 {clusters} 个簇，要求恰好 1 个")
tail = core.rstrip()
if tail and not emoji_char.match(tail[-1]):
    errors.append("emoji 未位于卡片末尾")

# 排版：无 markdown 行首、不被引号包裹、不以 Dear 开头
if re.search(r"(?m)^\s*(#|>|`|-\s|\*\s)", text):
    errors.append("包含 markdown 格式")
if text[:1] in {'"', "'", "“", "‘", "「", "《"}:
    errors.append("卡片被引号包裹")
if re.match(r"(?i)\s*dear\b", text):
    errors.append("以 Dear 开头（tone-guide 禁止）")

if errors:
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)
print("PASS: 格式硬规则全部满足")
PY
