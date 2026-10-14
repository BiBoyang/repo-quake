#!/usr/bin/env bash
# Script judge：校验卡片正文的格式硬约束。
# 退出码 0 = PASS，非 0 = FAIL；被判分输出从环境变量 $EVAL_FINAL_MESSAGE 读取。
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys


def char_class(spans):
    """按码点区间拼出正则字符类，避免源码中出现不可见字符。"""
    parts = []
    for start, end in spans:
        parts.append(chr(start) if end is None else chr(start) + "-" + chr(end))
    return "[" + "".join(parts) + "]"


# 常见 emoji 区间；U+FE0F 与肤色修饰符跟在 emoji 之后，U+200D 用于组合序列。
EMOJI = char_class([
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0x2190, 0x21FF),
    (0x2900, 0x297F),
])
MODIFIER = "(?:" + chr(0xFE0F) + "|" + char_class([(0x1F3FB, 0x1F3FF)]) + ")*"
EMOJI_SEQ = re.compile(EMOJI + MODIFIER + "(?:" + chr(0x200D) + EMOJI + MODIFIER + ")*")

# 汉字区间：扩展 A、基本区、兼容汉字。
CJK = re.compile(char_class([(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)]))

# 中文句末标点：。！？以及半角 !?
SENTENCE_END = "[" + chr(0x3002) + chr(0xFF01) + chr(0xFF1F) + "!?]+"

text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()
failures = []

if not text:
    failures.append("卡片正文为空。")
else:
    sequences = list(EMOJI_SEQ.finditer(text))
    if len(sequences) != 1:
        failures.append("卡片应恰好包含 1 个 emoji，实际为 %d 个。" % len(sequences))
    elif sequences[0].end() != len(text):
        failures.append("emoji 必须位于正文结尾，其后不应再有其他内容。")

    for marker in ("**", "##", "```", "- ", "* "):
        if marker in text:
            failures.append("卡片正文不应包含 markdown 标记：%r" % marker)

    head = text.splitlines()[0].strip()
    for prefix in ("好的", "当然", "以下是", "Here is", "Sure"):
        if head.startswith(prefix):
            failures.append("只应输出卡片正文，不应出现前置说明。")
            break

    if CJK.search(text):
        # 中文卡片：80 字以内，1-3 句（中文句末标点明确，可安全切分）。
        if len(text) > 80:
            failures.append("中文卡片应在 80 字以内，实际 %d 字。" % len(text))
        # 只数句末标点，避免把结尾的 emoji 当成一句。
        sentences = len(re.findall(SENTENCE_END, text))
        if sentences > 3:
            failures.append("卡片应在 1-3 句以内，实际 %d 句。" % sentences)
    else:
        # 英文卡片：60 词以内。
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", text)
        if len(words) > 60:
            failures.append("英文卡片应在 60 词以内，实际 %d 词。" % len(words))

if failures:
    print("卡片格式检查未通过：")
    for failure in failures:
        print("- %s" % failure)
    sys.exit(1)

print("PASS: 卡片格式符合 tone-guide 的硬性约束。")
PY
