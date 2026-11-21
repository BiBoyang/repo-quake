#!/usr/bin/env bash
# 判分脚本约定：退出码 0 = PASS，非 0 = FAIL。
# 工作目录为用例工作区根目录；Agent 最终回复从 $EVAL_FINAL_MESSAGE 读取。
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys

text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()

failures = []

if not text:
    failures.append("最终回复为空。")

# 正文不应被引号整体包裹。
if len(text) >= 2 and text[0] in "\"'“”‘’" and text[-1] in "\"'“”‘’":
    failures.append("卡片正文被引号包裹。")

# 无 markdown：标题、加粗、列表/引用、行内代码。
if (
    re.search(r"(?m)^\s*#{1,6}\s", text)
    or re.search(r"\*\*[^*]+\*\*", text)
    or re.search(r"(?m)^\s*[-*>]\s", text)
    or "`" in text
):
    failures.append("卡片正文包含 markdown 格式。")

# 恰好一个 emoji 簇，且位于正文最末尾（ZWJ 组合序列算一个簇）。
emoji_char = r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\u2B00-\u2BFF\U0001F1E6-\U0001F1FF]"
cluster_re = re.compile(emoji_char + r"\ufe0f?(?:\u200d" + emoji_char + r"\ufe0f?)*")
clusters = cluster_re.findall(text)
if len(clusters) != 1:
    failures.append(f"emoji 数量应为 1，实际检测到 {len(clusters)}。")
elif not text.endswith(clusters[0]):
    failures.append("emoji 不在正文最末尾。")

# 长度：含中文则按中文字符 <= 80，否则按英文单词 <= 60。
cjk = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text)
if cjk:
    if len(cjk) > 80:
        failures.append(f"中文字数 {len(cjk)} 超过 80。")
else:
    words = re.findall(r"[A-Za-z']+", text)
    if len(words) > 60:
        failures.append(f"英文单词数 {len(words)} 超过 60。")

# 句数：按中英文句末标点统计，1-3 句；无标点视为 1 句。
sentence_marks = re.findall(r"[。！？!?.]", text)
if len(sentence_marks) > 3:
    failures.append(f"句数 {len(sentence_marks)} 超过 3 句。")

# 不以 Dear/亲爱的 开头（用户未要求正式风格时）。
if re.match(r"^(Dear|亲爱的)", text):
    failures.append("以 Dear/亲爱的 开头。")

if failures:
    print("贺卡格式检查未通过：")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: 格式约束全部满足。")
PY
