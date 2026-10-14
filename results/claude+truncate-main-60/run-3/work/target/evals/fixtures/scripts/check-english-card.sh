#!/usr/bin/env bash
# judge 脚本：英文卡片检查（退出码 0 = PASS，非 0 = FAIL）。
# 判定规则来自 target Skill 的 SKILL.md 与 references/tone-guide.md：
#   1) 语言跟随用户：英文提问应得到纯英文卡片，不出现中日韩字符；
#   2) 结尾恰好一个 emoji，且 emoji 之后没有其他内容；
#   3) 英文卡片不超过 60 个单词。
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys

message = (os.environ.get("EVAL_FINAL_MESSAGE") or "").strip()
failures = []

if not message:
    print("FAIL: 最终输出为空。")
    sys.exit(1)

# 中日韩字符、CJK 标点与全角字符都不应出现在英文卡片里。
cjk_re = re.compile("[㐀-䶿一-鿿　-〿＀-￯]")
emoji_re = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
word_re = re.compile(r"[A-Za-z][A-Za-z'’-]*")

if cjk_re.search(message):
    failures.append("用户用英文提问时，卡片应使用英文，不应出现中日韩字符或全角标点。")

emojis = list(emoji_re.finditer(message))
if len(emojis) != 1:
    failures.append(f"结尾应恰好有一个 emoji，实际找到 {len(emojis)} 个。")
elif message[emojis[0].end():].strip():
    failures.append("emoji 必须位于最末尾，其后不应再有文字。")

body = message[: emojis[0].start()] if len(emojis) == 1 else message
words = word_re.findall(body)
if len(words) > 60:
    failures.append(f"英文卡片不应超过 60 个单词，实际 {len(words)} 个。")
elif len(words) < 4:
    failures.append(f"英文卡片过短，不像一张完整卡片，实际 {len(words)} 个单词。")

# 只有卡片正文：不要 markdown，也不要有说明性开头。
if any(marker in message for marker in ("**", "__", "`", "##")):
    failures.append("卡片正文不应包含 markdown 标记。")
if re.search(r"(?m)^\s*(#|[-*+]\s|\d+\.\s|>\s)", message):
    failures.append("卡片正文不应包含标题、列表或引用。")
if re.match(r"(?i)^dear\b", message):
    failures.append("用户在非正式场景下提问，卡片不应以 “Dear” 开头。")
if re.match(r"(?i)^(here('s| is)|sure[,!]|of course|i'?d be happy to|absolutely)", message):
    failures.append("卡片应只包含正文，不要以 “Here's…/Sure…” 之类的说明开头。")

if failures:
    print("英文卡片检查未通过：")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: 英文卡片符合 tone-guide 的语言与格式要求。")
PY
