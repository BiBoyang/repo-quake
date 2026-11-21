#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys

# 常见 emoji 区间：Misc Symbols & Pictographs、Emoticons、Transport、Dingbats、Misc Symbols、Supplemental Symbols。
emoji_pattern = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]")
sentence_end_pattern = re.compile(r"[。！？!?…]+")
markdown_pattern = re.compile(r"(?m)(^#{1,6}\s|^\s*[-*>+]\s|\*\*|__|`|~~)")
wrapper_phrase_pattern = re.compile(r"(以下是|这是|Here is|Here's)")

failures = []

final_message = os.environ.get("EVAL_FINAL_MESSAGE", "")
if not final_message.strip():
    failures.append("Final response is empty.")
    final_message = ""

if final_message:
    text = final_message.strip()

    if wrapper_phrase_pattern.search(text):
        failures.append("Final response contains a wrapper phrase instead of only the card text.")

    if markdown_pattern.search(text):
        failures.append("Final response contains markdown formatting.")

    emojis = emoji_pattern.findall(text)
    if len(emojis) != 1:
        failures.append(f"Expected exactly one emoji, found {len(emojis)}.")
    elif not text.endswith(emojis[0]):
        failures.append("The emoji is not at the very end of the message.")

    body = emoji_pattern.sub("", text)
    sentences = [s for s in sentence_end_pattern.split(body) if s.strip()]
    if not (1 <= len(sentences) <= 3):
        failures.append(f"Expected 1-3 sentences, found {len(sentences)}.")

if failures:
    print("Card format check failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: card text has 1-3 sentences, exactly one trailing emoji, and no markdown.")
PY
