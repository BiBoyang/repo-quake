#!/usr/bin/env python3
"""Copy the publishable part of a stream-retry evidence root, redact the COPY, audit it.

  export_public.py --src EVIDENCE_ROOT --dst runs/<phase-dir> [--replace OLD=NEW ...]
                   [--deny REGEX ...] [--skip GLOB ...]

The evidence root is never modified: a sha256 manifest of every source file is taken
before and after, and any difference fails the export (exit 2). Request bodies, session
files, temporary HOMEs, the subjects' working directories and raw terminal bytes are
never copied (they carry third-party system prompts, local paths and device/user ids);
derived witnesses (record.json, raw-analysis.json, screen captures) are. Every copied
text file is redacted (paths -> placeholders, e-mail addresses), then the destination
is scanned for forbidden strings (exit 1 on any hit) and audited with
skills/repo-quake/scripts/audit_artifacts.py (exit 1 on any finding).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
AUDIT = REPO / "skills" / "repo-quake" / "scripts" / "audit_artifacts.py"

TOP_LEVEL = ["summary.md", "manifest-*.json", "versions-before-*.json", "versions-after-*.json", "card-frozen.json",
             "frozen-sha256.txt", "egress.json", "lsregister.json", "regrade.jsonl", "window-*.txt", "matrix.log",
             "runs.jsonl", "runs-noninteractive.jsonl"]
PROBE_FILES = ["*.json", "*.txt"]
MOCK_FILES = ["delivery.jsonl", "ready.json", "stdout.txt"]
RUN_FILES = ["record.json", "gate.txt", "prompt-gate.txt", "mid.txt", "mid.json", "overlap.txt", "overlap.json",
             "prefin.txt", "final-view.txt", "final-history.txt", "followup-view.txt", "raw-analysis.json",
             "samples.jsonl", "stdout.txt", "stderr.txt", "output-timeline.jsonl"]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Generic patterns only. Project-internal names, people and anything else that must not be
# published go in a private --deny-file kept outside the repository.
DEFAULT_DENY = [
    r"/Users/[A-Za-z0-9._-]+", r"/home/[A-Za-z0-9._-]+",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r'"(?:device_id|deviceId|machineID|machineId|userID|userId|accountUuid|account_uuid|oauthAccount)"',
    # a leaked request body: system prompt / instructions / tool schemas
    r'"(?:system|instructions)"\s*:\s*[\["]', r'"input_schema"\s*:', r'"tool_choice"\s*:',
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def manifest(root: Path) -> dict[str, str]:
    out = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in files:
            p = Path(current) / name
            if p.is_symlink() or not p.is_file():
                continue
            out[str(p.relative_to(root))] = sha256(p)
    return out


def selected(src: Path, skips: list[str]) -> list[Path]:
    picks: list[Path] = []
    for pattern in TOP_LEVEL:
        picks += [p for p in src.glob(pattern) if p.is_file()]
    picks += [p for pat in PROBE_FILES for p in (src / "probes").glob(pat) if p.is_file()]
    for mock_dir in src.glob("mock-*"):
        picks += [mock_dir / n for n in MOCK_FILES if (mock_dir / n).is_file()]
    for record in list(src.glob("runs/*/*/*/record.json")) + list(src.glob("runs-noninteractive/*/*/*/record.json")):
        picks += [record.parent / n for n in RUN_FILES if (record.parent / n).is_file()]
    picks = sorted(set(picks))
    return [p for p in picks if not any(fnmatch.fnmatch(str(p.relative_to(src)), s) for s in skips)]


def redact(text: str, rules: list[tuple[str, str]]) -> str:
    for old, new in rules:
        text = text.replace(old, new)
    return EMAIL.sub("<EMAIL>", text)


def default_rules(src: Path) -> list[tuple[str, str]]:
    home = str(Path.home())
    rules = []
    # both spellings: /var/... and its resolved /private/var/... both occur in evidence
    for spelling in sorted({str(src.absolute()), str(src.resolve())}, key=len, reverse=True):
        rules += [(spelling, "<EVIDENCE_ROOT>"), (spelling.replace("/", "-").replace(".", "-"), "<EVIDENCE_ROOT_SLUG>")]
    rules += [(home, "<HOME>"), (home.replace("/", "-"), "-<HOME_SLUG>")]
    user = Path.home().name
    return rules + [(f"/{user}/", "/<USER>/")] if user else rules


def scan(dst: Path, patterns: list[str], extra_words: list[str]) -> list[str]:
    regs = [re.compile(p) for p in patterns] + [re.compile(rf"\b{re.escape(w)}\b") for w in extra_words if w]
    hits = []
    for p in sorted(dst.rglob("*")):
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for reg in regs:
            m = reg.search(text)
            if m:
                hits.append(f"{p.relative_to(dst)}: {reg.pattern!r} -> {m.group(0)[:60]!r}")
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--replace", action="append", default=[], help="OLD=NEW; all rules apply longest OLD first")
    ap.add_argument("--deny", action="append", default=[], help="extra forbidden regex")
    ap.add_argument("--deny-file", action="append", default=[],
                    help="private file of forbidden regexes, one per line (keep it outside the repository)")
    ap.add_argument("--skip", action="append", default=[], help="glob (relative to src) to leave out")
    args = ap.parse_args(argv)
    src, dst = Path(args.src).absolute(), Path(args.dst)
    if not src.is_dir():
        print(f"export: no such evidence root {src}", file=sys.stderr)
        return 2
    if dst.exists() and any(dst.iterdir()):
        print(f"export: destination {dst} is not empty; refusing to overwrite", file=sys.stderr)
        return 2
    before = manifest(src)
    # longest OLD first: the evidence root wins over a workspace prefix, which wins over HOME
    rules = sorted([tuple(r.split("=", 1)) for r in args.replace] + default_rules(src), key=lambda r: -len(r[0]))
    files = selected(src, args.skip)
    dst.mkdir(parents=True, exist_ok=True)
    for path in files:
        target = dst / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            print(f"export: {path} is not UTF-8 text; refusing to copy binary evidence", file=sys.stderr)
            return 1
        target.write_text(redact(text, rules), encoding="utf-8")
    after = manifest(src)
    if before != after:
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        print(f"export: SOURCE CHANGED during export: {changed[:10]}", file=sys.stderr)
        return 2
    digest = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    note = [
        "# 公开副本说明（export_public.py 生成）", "",
        f"- 源证据目录：`<EVIDENCE_ROOT>`，共 {len(before)} 个文件；导出前后哈希清单一致，清单摘要 sha256 `{digest}`。",
        f"- 复制了 {len(files)} 个文本文件；只在副本上脱敏：本机路径换成占位符（`<EVIDENCE_ROOT>`、`<HOME>` 等），邮箱换成 `<EMAIL>`。",
        "- 没有复制：请求体（`requests/`、`mock-*/req-*.json`，含第三方系统提示词和工具 schema）、被测程序的临时 HOME 与会话文件、工作目录、终端原始字节 `raw.bin` 及其时间索引。由它们得出的证人（`record.json`、`raw-analysis.json`、截屏）已复制。",
        "- 复制后做了禁用串扫描和 `skills/repo-quake/scripts/audit_artifacts.py` 审计，均无命中。", ""]
    (dst / "EXPORT.md").write_text("\n".join(note), encoding="utf-8")
    private = []
    for path in args.deny_file:
        private += [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")]
    hits = scan(dst, DEFAULT_DENY + args.deny + private, [Path.home().name])
    if hits:
        print("export: forbidden strings remain in the copy:\n  " + "\n  ".join(hits[:40]), file=sys.stderr)
        return 1
    audit = subprocess.run([sys.executable, str(AUDIT), str(dst)], capture_output=True, text=True)
    if audit.returncode != 0:
        print("export: audit_artifacts.py reported findings:\n" + audit.stdout + audit.stderr, file=sys.stderr)
        return 1
    print(json.dumps({"copied": len(files), "source_files": len(before), "source_manifest_sha256": digest,
                      "dst": str(dst)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
