# 公开副本说明（export_public.py 生成）

- 源证据目录：`<EVIDENCE_ROOT>`，共 1463 个文件；导出前后哈希清单一致，清单摘要 sha256 `d793c13058628304cd2190c5edfa87ddc7adb6ba94bbaf35276a1f79114b9a0d`。
- 复制了 106 个文本文件；只在副本上脱敏：本机路径换成占位符（`<EVIDENCE_ROOT>`、`<HOME>` 等），邮箱换成 `<EMAIL>`。
- 没有复制：请求体（`requests/`、`mock-*/req-*.json`，含第三方系统提示词和工具 schema）、被测程序的临时 HOME 与会话文件、工作目录、终端原始字节 `raw.bin` 及其时间索引。由它们得出的证人（`record.json`、`raw-analysis.json`、截屏）已复制。
- 复制后做了禁用串扫描和 `skills/repo-quake/scripts/audit_artifacts.py` 审计，均无命中。
