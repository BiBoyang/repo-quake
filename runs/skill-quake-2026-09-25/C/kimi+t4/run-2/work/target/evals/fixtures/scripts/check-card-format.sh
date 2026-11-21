#!/usr/bin/env bash
# greeting-card 格式判分脚本：恰好一个 emoji 在结尾、长度与句数限制、无 markdown。
# 约定：退出码 0 = PASS，非 0 = FAIL；最终回复取自 $EVAL_FINAL_MESSAGE。
set -euo pipefail

python3 - <<'PY'
import os
import re
import sys

text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()

failures = []

if not text:
    failures.append("最终回复为空。")

if text:
    # emoji 基础码位范围（覆盖常见 emoji 与符号区段）。
    base = "\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF"
    # 肤色修饰符（在 base 范围内，但属于前一个 emoji，不单独计数）。
    skin = "\U0001F3FB-\U0001F3FF"
    # 一个 emoji 簇 = 基础字符 + 可选肤色 + 可选 VS16 + 可选 ZWJ 组合序列；
    # 两个相邻独立 emoji（无 ZWJ 连接）计为 2 个。
    cluster_re = re.compile(f"[{base}][{skin}]?\uFE0F?(?:\u200D[{base}][{skin}]?\uFE0F?)*")
    clusters = cluster_re.findall(text)
    if len(clusters) != 1:
        failures.append(f"emoji 数量应为恰好 1 个，实际检测到 {len(clusters)} 个。")
    elif not text.endswith(clusters[0]):
        failures.append("emoji 未放在贺卡文本末尾。")

    # 中文贺卡长度上限 80 字（按码点计数，含标点与 emoji）。
    if len(text) > 80:
        failures.append(f"贺卡长度为 {len(text)} 字，超过 80 字上限。")

    # 句数上限 3 句，按句末标点计数；无句末标点视为 1 句，不算违规。
    sentence_marks = re.findall(r"[。！？!?]", text)
    if len(sentence_marks) > 3:
        failures.append(f"句数最多 3 句，实际检测到 {len(sentence_marks)} 句。")

    # 不使用 markdown 格式。
    for marker in ("**", "##", "`"):
        if marker in text:
            failures.append(f"贺卡文本包含 markdown 标记 {marker!r}。")

    # 用户未要求正式风格时，不以 Dear 开头。
    if text.lower().startswith("dear"):
        failures.append("贺卡以 'Dear' 开头，违反默认非正式风格要求。")

if failures:
    for item in failures:
        print(f"FAIL: {item}", file=sys.stderr)
    sys.exit(1)

print("PASS: 贺卡格式符合全部规则。")
PY
