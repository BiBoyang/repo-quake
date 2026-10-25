#!/usr/bin/env python3
"""Audit one experiment directory for archive blockers (stdlib only).

The checker is deliberately conservative about deletion: it only reports. Runtime
artifacts are excluded by path shape, symlinks by file type, and credentials by a
small set of high-confidence content signatures (first 4 MiB per file). Placeholders such as
<secret:token> and words like "password" in a test report are not credentials.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

FORBIDDEN_DIRS = {
    "node_modules", "chrome-profile", "runtime", "home", "bin", "__pycache__",
    ".stage", ".e2e",
}
FORBIDDEN_FILES = {"id_rsa", ".salt", "chrome.log", "chrome-error.log"}
FORBIDDEN_SUFFIXES = (".pem", ".key", ".pid", ".p12", ".pfx")
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("api-token", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
    ("bearer-token", re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9._-]{16,}", re.IGNORECASE)),
)
MAX_SCAN_BYTES = 4 * 1024 * 1024


def issue(code: str, path: str, detail: str) -> dict:
    return {"code": code, "path": path, "detail": detail}


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def forbidden_file(name: str) -> bool:
    return (
        name in FORBIDDEN_FILES
        or name == ".env"
        or name.startswith(".env.")
        or name.endswith(FORBIDDEN_SUFFIXES)
    )


def audit(root: Path) -> dict:
    """Return an audit report without following links or changing the tree."""
    root = root.expanduser()
    if root.is_symlink():
        raise ValueError("audit root must not be a symlink")
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)

    issues: list[dict] = []
    files = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for name in dirs:
            path = current_path / name
            rel = relative(root, path)
            if path.is_symlink():
                issues.append(issue("SYMLINK", rel, "archive entries must be regular, self-contained files"))
                continue
            if name in FORBIDDEN_DIRS or fnmatch.fnmatch(name, "cache-*"):
                issues.append(issue("FORBIDDEN_DIR", rel, "runtime-only directory; retain evidence, not this subtree"))
                continue
            kept_dirs.append(name)
        dirs[:] = kept_dirs

        for name in names:
            path = current_path / name
            rel = relative(root, path)
            if path.is_symlink():
                issues.append(issue("SYMLINK", rel, "archive entries must be regular, self-contained files"))
                continue
            files += 1
            if forbidden_file(name):
                issues.append(issue("FORBIDDEN_FILE", rel, "runtime, browser, PID, or credential-shaped filename"))
                continue
            try:
                with path.open("rb") as handle:
                    data = handle.read(MAX_SCAN_BYTES)
                text = data.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    issues.append(issue("SECRET", rel, f"content matches {label}; review before publication"))

    return {
        "root": str(root),
        "files": files,
        "ok": not issues,
        "issues": issues,
        "scan_limit_bytes_per_file": MAX_SCAN_BYTES,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="experiment directory to audit, not the whole repository")
    parser.add_argument("--json", action="store_true", help="emit the complete report as JSON")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root)
    except (OSError, ValueError) as error:
        print(f"audit_artifacts: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"PASS {report['root']}: {report['files']} files, no archive blockers")
    else:
        print(f"FAIL {report['root']}: {len(report['issues'])} archive blocker(s) across {report['files']} files")
        for issue in report["issues"]:
            print(f"{issue['code']} {issue['path']}: {issue['detail']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
