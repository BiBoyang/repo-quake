#!/usr/bin/env bash
# greeting-card 输出结构判分脚本：退出码 0 = PASS，非 0 = FAIL。
# 判定点：恰好一个 emoji 且位于结尾、句数不超过 3、中文 80 字 / 英文 60 词以内、
# 无 Markdown 格式、正文不被引号包裹。
# 约定：最终输出由环境变量 EVAL_FINAL_MESSAGE 提供。
# 说明：所有判定都用码点判断，脚本逻辑中不出现任何非 ASCII 字面量。
set -euo pipefail

python3 - <<'PY'
import os
import sys

message = os.environ.get("EVAL_FINAL_MESSAGE", "")
text = message.strip()

if not text:
    print("FAIL: final message is empty")
    sys.exit(1)

failures = []


def is_emoji_base(ch):
    """emoji 基字符：表情、杂项符号、符号与箭头三段。"""
    o = ord(ch)
    return 0x1F300 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF


def is_emoji_suffix(ch):
    """emoji 的修饰符：肤色修饰符与变体选择符，算作同一个 emoji 的一部分。"""
    o = ord(ch)
    return 0x1F3FB <= o <= 0x1F3FF or o == 0xFE0F


def is_cjk(ch):
    """CJK 表意文字（含扩展 A 区），用于语言与长度判断。"""
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF


def is_sentence_end(ch):
    """中英文句末标点：。！？ ! ?"""
    return ord(ch) in (0x3002, 0xFF01, 0xFF1F, 0x21, 0x3F)


def is_quote(ch):
    """直引号与中英文弯引号。"""
    return ord(ch) in (0x22, 0x27, 0x201C, 0x201D, 0x2018, 0x2019)


# 恰好一个 emoji，且必须位于正文结尾。
emoji_count = 0
emoji_end = -1
index = 0
while index < len(text):
    if is_emoji_base(text[index]):
        emoji_count += 1
        cursor = index + 1
        while cursor < len(text) and is_emoji_suffix(text[cursor]):
            cursor += 1
        emoji_end = cursor
        index = cursor
    else:
        index += 1

if emoji_count != 1:
    failures.append("expected exactly 1 emoji, found %d" % emoji_count)
elif emoji_end != len(text):
    failures.append("the single emoji is not at the end of the message")

# 不得使用 Markdown 格式（加粗、代码块、标题、引用、列表）。
if "**" in text or "```" in text:
    failures.append("message contains Markdown formatting")
else:
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped[:1] in ("#", ">") or stripped[:2] in ("- ", "* "):
            failures.append("message contains Markdown formatting")
            break

# 正文不应被引号包裹（tone-guide: no quotes around the text）。
if len(text) >= 2 and is_quote(text[0]) and is_quote(text[-1]):
    failures.append("message is wrapped in quotation marks")

# 句数上限 3。
sentence_ends = sum(1 for ch in text if is_sentence_end(ch))
if sentence_ends > 3:
    failures.append("expected at most 3 sentences, found %d" % sentence_ends)

# 长度上限：中文按字符数（80），英文按词数（60）。
cjk_chars = sum(1 for ch in text if is_cjk(ch))
if cjk_chars:
    if cjk_chars > 80:
        failures.append("Chinese card exceeds 80 characters, found %d" % cjk_chars)
else:
    words = 0
    in_word = False
    for ch in text:
        if ch.isascii() and ch.isalpha():
            if not in_word:
                words += 1
            in_word = True
        elif ch == "'" and in_word:
            pass
        else:
            in_word = False
    if words > 60:
        failures.append("English card exceeds 60 words, found %d" % words)

if failures:
    print("Card structure check failed:")
    for failure in failures:
        print("- %s" % failure)
    sys.exit(1)

print("PASS: card structure matches tone-guide (single trailing emoji, sentence and length limits, no Markdown).")
PY
