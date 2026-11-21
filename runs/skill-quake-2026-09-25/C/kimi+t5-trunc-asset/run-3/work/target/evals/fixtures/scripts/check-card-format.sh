#!/bin/sh
# 贺卡格式校验脚本入口：调用同目录的 python3 实现
# 约定：退出码 0 = PASS，非 0 = FAIL；输出文本来自 $EVAL_FINAL_MESSAGE
exec python3 "$(dirname "$0")/check_card_format.py"
