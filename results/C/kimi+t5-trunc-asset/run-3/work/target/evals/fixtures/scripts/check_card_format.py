# 贺卡格式校验：恰好一个 emoji、位于末尾、长度不超过 80 个字符
# 退出码 0 = PASS，非 0 = FAIL；输出文本来自 $EVAL_FINAL_MESSAGE
import os
import re
import sys

text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()
if not text:
    print("输出为空")
    sys.exit(1)

# 常见 emoji 区间（U+1F000–U+1FAFF、U+2600–U+27BF），允许尾随变体选择符 U+FE0F
emoji_pattern = r"[\U0001F000-\U0001FAFF☀-➿]\uFE0F?"
emojis = re.findall(emoji_pattern, text)
if len(emojis) != 1:
    print(f"emoji 数量应为 1，实际为 {len(emojis)}")
    sys.exit(1)

if not re.search(emoji_pattern + r"\s*$", text):
    print("emoji 未位于贺卡末尾")
    sys.exit(1)

# tone-guide 长度上限：中文不超过 80 个字符
if len(text) > 80:
    print(f"长度 {len(text)} 超过 80 字符上限")
    sys.exit(1)

print("格式校验通过")
sys.exit(0)
