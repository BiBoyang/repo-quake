#!/usr/bin/env bash
# judge 脚本：生日卡片检查（退出码 0 = PASS，非 0 = FAIL）。
# 判定规则来自 target Skill 的 references/tone-guide.md：
#   1) 中文卡片不超过 80 字、1-3 句；
#   2) 结尾恰好一个 emoji，且 emoji 之后没有其他内容；
#   3) 只有卡片正文：没有 markdown、标题行、署名、整体引号；
#   4) 不替用户承诺未来行动；
#   5) 围绕用户给出的具体事件（半程马拉松）展开，而不是泛泛祝福。
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

han_re = re.compile("[㐀-䶿一-鿿]")
emoji_re = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")
terminator_re = re.compile(r"[。！？!?…]")
detail_re = re.compile(r"马拉松|半马|跑|终点|完赛")

# 中文 prompt 应得到中文卡片。
if not han_re.search(message):
    failures.append("用户用中文提问时，卡片应使用中文。")

# 结尾恰好一个 emoji。
emojis = list(emoji_re.finditer(message))
if len(emojis) != 1:
    failures.append(f"结尾应恰好有一个 emoji，实际找到 {len(emojis)} 个。")
elif message[emojis[0].end():].strip():
    failures.append("emoji 必须位于最末尾，其后不应再有文字。")

# 先折叠连续句末标点，避免“！！！”或“……”被重复计数。
collapsed = re.sub(r"[。！？!?…]{2,}", "！", message)
terminators = len(terminator_re.findall(collapsed))
if terminators > 3:
    failures.append(f"卡片应为 1-3 句，实际出现 {terminators} 个句末标点。")

# 长度：去掉 emoji 和空白后统计中文字符数。
body = message[: emojis[0].start()] if len(emojis) == 1 else message
chars = len(re.sub(r"\s+", "", body))
if chars > 80:
    failures.append(f"中文卡片不应超过 80 字，实际 {chars} 字。")

# 只有卡片正文。
if any(marker in message for marker in ("**", "__", "`", "##")):
    failures.append("卡片正文不应包含 markdown 标记。")
if re.search(r"(?m)^\s*(#|[-*+]\s|\d+\.\s|>\s)", message):
    failures.append("卡片正文不应包含标题、列表或引用。")
if re.search(r"(?m)^\s*[^\n：:]{1,12}[：:]\s*$", message):
    failures.append("卡片不应带“标签：”式的标题行。")
if "【" in message or "】" in message:
    failures.append("卡片不应使用方括号式标题。")
if re.search(r"(?m)^\s*(--|—|——|此致|敬礼)", message):
    failures.append("卡片不应带署名。")
if len(message) >= 2 and message[0] in "\"'“”‘’「」『』" and message[-1] in "\"'“”‘’「」『』":
    failures.append("卡片正文不应被引号包裹。")

# 不替用户承诺未来行动。
for marker in ("我会一直", "我永远", "I will always", "I'll always"):
    if marker.lower() in message.lower():
        failures.append(f"卡片不应替用户承诺未来行动：{marker}")

# 具体性：要提到用户给出的半程马拉松事件。
if not detail_re.search(message):
    failures.append("卡片应围绕用户给出的具体事件（半程马拉松）展开，而不是泛泛祝福。")

if failures:
    print("生日卡片检查未通过：")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("PASS: 生日卡片符合 tone-guide 的格式与具体性要求。")
PY
