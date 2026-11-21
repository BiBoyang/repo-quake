#!/usr/bin/env python3
"""greeting-card 感谢贺卡格式校验脚本（judge.type: script）。

约定：退出码 0 = PASS，非 0 = FAIL。
输入来自环境变量 EVAL_FINAL_MESSAGE（Agent 的最终回复）。
校验规则来自 references/tone-guide.md 的硬性条款。
"""

import os
import re
import sys


def is_emoji(ch: str) -> bool:
    """粗略判断字符是否为 emoji（覆盖常见区间，不含 ZWJ 序列拆分）。"""
    cp = ord(ch)
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or cp in (0x203C, 0x2049, 0x2764, 0x2B50, 0x2B55)
    )


def main() -> int:
    text = os.environ.get("EVAL_FINAL_MESSAGE", "").strip()
    errors = []

    if not text:
        print("FAIL: 输出为空")
        return 1

    # 规则：恰好一个 emoji，且位于消息末尾。
    # 先去掉末尾的变体选择符（U+FE0F），避免 ❤️ 这类序列误判末字符。
    emojis = [c for c in text if is_emoji(c)]
    stripped = text.rstrip("\ufe0f")
    if len(emojis) != 1:
        errors.append(f"emoji 数量为 {len(emojis)}，期望恰好 1 个")
    elif not stripped or not is_emoji(stripped[-1]):
        errors.append("emoji 未位于消息末尾")

    # 规则：中文不超过 80 个汉字（按 CJK 字符数计算）。
    cjk = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text)
    if len(cjk) > 80:
        errors.append(f"汉字数 {len(cjk)} 超过上限 80")

    # 规则：不使用 markdown 标记。
    if re.search(r"[#*`\[\]]", text):
        errors.append("包含 markdown 标记")

    # 规则：未要求正式风格时不以 Dear/亲爱的 开头。
    if re.match(r"^\s*(Dear|亲爱的)", text):
        errors.append("以 Dear/亲爱的 开头")

    # 规则：包含收信人名字。
    if "张伟" not in text:
        errors.append("未包含收信人名字「张伟」")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: 格式与长度全部合规")
    return 0


if __name__ == "__main__":
    sys.exit(main())
