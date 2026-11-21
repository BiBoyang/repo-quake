#!/usr/bin/env python3
"""Check the hard formatting rules of references/tone-guide.md on a card message.

Used by the `card-style-rules` case via judge.type: script.
The agent's final message is read from $EVAL_FINAL_MESSAGE.
Exit code 0 means PASS, any non-zero exit code means FAIL.
"""

import os
import re
import sys

# Emoji and pictograph ranges (sufficient for "exactly one emoji at the end").
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, faces, hands
    "\U0001F000-\U0001F2FF"  # mahjong, dominoes, enclosed characters
    "\U00002600-\U000027BF"  # misc symbols and dingbats
    "\U00002B00-\U00002BFF"  # arrows and misc symbols
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    "]"
)

MARKDOWN_LINE_RE = re.compile(r"(?m)^\s*(?:[-*+]|\d+\.)\s")
CJK_RE = re.compile("[一-鿿㐀-䶿豈-﫿]")
SENTENCE_END_RE = re.compile("[。！？!?]")


def fail(message):
    print("FAIL: %s" % message)
    sys.exit(1)


def main():
    text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()
    if not text:
        fail("EVAL_FINAL_MESSAGE is empty, nothing to grade")

    body = text.strip('"').strip("“”").strip("'")

    # Rule: exactly one emoji, placed at the very end of the message.
    emojis = EMOJI_RE.findall(text)
    if len(emojis) != 1:
        fail("expected exactly one emoji, found %d" % len(emojis))
    if not text.rstrip().endswith(emojis[0]):
        fail("the single emoji must be the very last character of the card")

    # Rule: card text only, no markdown, no wrapping quotes, no header/signature.
    if "**" in body or "`" in body or "##" in body:
        fail("card text must not contain markdown emphasis or headings")
    if MARKDOWN_LINE_RE.search(body):
        fail("card text must not contain markdown list items")
    if text.startswith(('"', "“", "'", "#")):
        fail("card text must not start with a quote or heading marker")
    if body.count("\n") > 0:
        fail("card text must be a single paragraph without line breaks")

    content = text.replace(emojis[0], "").strip()

    # Rule: 1-3 sentences.
    sentence_count = len(SENTENCE_END_RE.findall(content))
    if sentence_count > 3:
        fail("card text must be at most 3 sentences, found %d" % sentence_count)

    # Rule: under 60 words in English or 80 characters in Chinese.
    han_count = len(CJK_RE.findall(content))
    if han_count >= len(content) / 2:
        if len(content) > 80:
            fail("Chinese card text must be under 80 characters, found %d" % len(content))
        length_note = "%d Chinese characters" % len(content)
    else:
        words = [w for w in re.split(r"\s+", content) if w]
        if len(words) > 60:
            fail("English card text must be under 60 words, found %d" % len(words))
        length_note = "%d words" % len(words)

    print("PASS: single trailing emoji, no markdown, %s" % length_note)
    sys.exit(0)


main()
