#!/usr/bin/env bash
# 贺卡格式断言脚本：长度上限、恰好一个 emoji 且位于结尾、纯正文无额外包装。
# 退出码 0 = PASS，非 0 = FAIL；失败原因打印到 stdout。
set -uo pipefail

python3 - <<'PY'
import json
import os
import pathlib
import re
import sys

# emoji 基字符：杂项符号、装饰符号、各类表情与符号、区域指示符。
EMOJI = re.compile(
    "[☀-➿"
    "⬀-⯿"
    "\U0001f000-\U0001f2ff"
    "\U0001f300-\U0001faff"
    "\U0001f1e6-\U0001f1ff]"
)
# 结尾允许 emoji 后跟随变体选择符（U+FE0F）或空白。
EMOJI_AT_END = re.compile(
    "[☀-➿⬀-⯿\U0001f000-\U0001faff️]\\s*$"
)
CJK = re.compile("[㐀-䶿一-鿿]")
WORD_TIGHT = re.compile("\\s")


def read_final_message():
    """取最终回复：优先 skill-up 注入的环境变量，其次读 transcript 文件。"""
    message = os.environ.get("EVAL_FINAL_MESSAGE", "")
    if message.strip():
        return message, "EVAL_FINAL_MESSAGE"

    transcript_path = os.environ.get("EVAL_TRANSCRIPT_PATH", "")
    if transcript_path and pathlib.Path(transcript_path).exists():
        try:
            transcript = json.loads(pathlib.Path(transcript_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "", ""
        texts = []

        def walk(node):
            if isinstance(node, dict):
                content = node.get("content")
                if node.get("role") in ("assistant", "agent") and isinstance(content, str):
                    texts.append(content)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(transcript)
        if texts:
            return texts[-1], "EVAL_TRANSCRIPT_PATH"

    return "", ""


message, source = read_final_message()
if not message.strip():
    print("FAIL: no final agent message found (checked EVAL_FINAL_MESSAGE and EVAL_TRANSCRIPT_PATH).")
    sys.exit(1)

text = message.strip()
print(f"source: {source}")
failures = []

# 1) 恰好一个 emoji，且位于结尾。
emoji_count = len(EMOJI.findall(text))
if emoji_count != 1:
    failures.append(f"expected exactly 1 emoji, found {emoji_count}.")
if not EMOJI_AT_END.search(text):
    failures.append("the message does not end with an emoji.")

# 2) 长度上限：中文按字符数 <= 80，英文按单词数 <= 60。
body = EMOJI.sub("", text).strip()
compact_length = len(WORD_TIGHT.sub("", body))
word_count = len(re.findall(r"[A-Za-z']+", body))
if CJK.search(body):
    if compact_length > 80:
        failures.append(f"Chinese card body exceeds 80 characters (got {compact_length}).")
elif word_count > 60:
    failures.append(f"English card body exceeds 60 words (got {word_count}).")

# 3) 1-3 句：按中英文句末标点切分。
sentences = [part for part in re.split(r"[.!?。！？…]+", body) if part.strip()]
if len(sentences) > 3:
    failures.append(f"expected 1-3 sentences, found {len(sentences)}.")

# 4) 纯正文：无 markdown、无抬头/落款、无整体引号包裹。
if re.search(r"(?m)^\s*(#|[-*+]\s|\d+[.)]\s)", text):
    failures.append("the message contains markdown headings or list markers.")
if "**" in text or "__" in text:
    failures.append("the message contains markdown emphasis markers.")
if re.match(r"^\s*(亲爱的|尊敬的|Dear\b|Hi\b|Hello\b)", text, re.IGNORECASE):
    failures.append("the message starts with a greeting header.")
if re.match(r"^\s*(此致|祝好|Best\b|Regards\b|Sincerely\b)", text, re.IGNORECASE):
    failures.append("the message looks like it contains a signature.")
if re.search(r"(?m)^\s*(此致|祝好|——|--)\s*$", text):
    failures.append("the message looks like it contains a signature line.")
if re.fullmatch(r"[\"“”'‘’].*[\"“”'‘’]", text, re.DOTALL):
    failures.append("the message is wrapped in quotes.")

if failures:
    print("Card format check failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: card body respects length, sentence-count and single-trailing-emoji rules.")
PY
