#!/usr/bin/env bash
# greeting-card 卡片格式判分脚本：
# 校验 EVAL_FINAL_MESSAGE 中恰好一个表情符号且位于最末尾、长度与句数上限、无 markdown。
# exit 0 = PASS，非 0 = FAIL。
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys
import unicodedata

ZWJ = chr(0x200D)
VS16 = chr(0xFE0F)

def is_emoji_base(ch):
    # 表情符号基字符（Unicode 类别 So，如 🎂 ❤ ✨）
    return unicodedata.category(ch) == "So"

def is_emoji_trailer(ch):
    # 表情簇的组成字符：基字符、肤色修饰（Sk）、VS16、ZWJ
    return unicodedata.category(ch) in ("So", "Sk") or ch in (ZWJ, VS16)

def count_emoji(text):
    # ZWJ 序列（如家庭组合表情）渲染为一个表情，只计一次；肤色修饰不单算
    count = 0
    prev = ""
    for ch in text:
        if is_emoji_base(ch) and prev != ZWJ:
            count += 1
        prev = ch
    return count

text = os.environ.get("EVAL_FINAL_MESSAGE", "")
failures = []

if not text.strip():
    failures.append("最终回复为空。")
else:
    stripped = text.strip()

    emoji_total = count_emoji(stripped)
    if emoji_total != 1:
        failures.append(f"表情符号应恰好 1 个，实际检测到 {emoji_total} 个。")

    # 唯一的表情基字符之后只允许表情簇字符，即表情必须位于最末尾
    last_base = max((i for i, ch in enumerate(stripped) if is_emoji_base(ch)), default=-1)
    if last_base >= 0 and any(not is_emoji_trailer(ch) for ch in stripped[last_base:]):
        failures.append("表情符号必须位于卡片文本的最末尾。")

    # 去掉表情簇字符后的正文
    body = "".join(ch for ch in stripped if not is_emoji_trailer(ch)).strip()

    # 不使用 markdown 格式符号
    if re.search(r"[#*`\[\]]", body):
        failures.append("卡片正文中不允许出现 markdown 格式符号。")

    # 句数不超过 3（按句末标点计数，英文句点只在后接空白或结尾时计）
    sentences = len(re.findall(r"[。！？!?]+|\.+(?=\s|$)", body))
    if sentences > 3:
        failures.append(f"卡片应不超过 3 句话，实际约 {sentences} 句。")

    # 长度上限：含汉字按中文 80 字计（不计空白），否则按英文 60 词计
    def is_han(ch):
        cp = ord(ch)
        return (0x3400 <= cp <= 0x4DBF) or (0x4E00 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF)

    if any(is_han(ch) for ch in body):
        compact = re.sub(r"\s+", "", body)
        if len(compact) > 80:
            failures.append(f"中文卡片应不超过 80 字，实际 {len(compact)} 字。")
    else:
        words = len(re.findall(r"[A-Za-z0-9']+", body))
        if words > 60:
            failures.append(f"英文卡片应不超过 60 词，实际 {words} 词。")

if failures:
    print("greeting-card 格式校验未通过：")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS：表情数量与位置、长度、句数、markdown 检查全部通过。")
PY
