#!/usr/bin/env python3
"""py-guard: deterministic integrity witness for a small python agent project.

Hard errors:
  H1 README.md missing/empty
  H2 relative paths referenced in README.md (backtick-quoted) missing on disk
  H4 any *.py fails to compile (py_compile)
Warnings:
  W1 markdown file ends at a heading or colon (truncation signature)
  W2 dangling code fence in markdown
Usage: py_guard.py <project-root> [--json]
"""
import json, py_compile, re, sys
from pathlib import Path

def check(root: Path):
    errors, warnings = [], []
    readme = root / "README.md"
    if not readme.exists() or not readme.read_text().strip():
        errors.append({"id": "H1", "msg": "README.md missing or empty"})
        text = ""
    else:
        text = readme.read_text()
    for m in re.finditer(r"`((?:examples|src|docs)/[^`\s]+?|[^`\s]+\.(?:py|md))`", text):
        ref = m.group(1)
        if not (root / ref).exists():
            errors.append({"id": "H2", "msg": f"referenced path missing: {ref}"})
    for f in sorted(root.rglob("*.py")):
        if ".venv" in f.parts:
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append({"id": "H4", "msg": f"{f.relative_to(root)}: {e.msg.splitlines()[-1] if e.msg else 'compile error'}"})
    for f in sorted(root.rglob("*.md")):
        t = f.read_text()
        tail = t.rstrip().splitlines()[-1].strip() if t.strip() else ""
        if re.match(r"^#{1,6}\s+\S", tail) or tail.endswith(":"):
            warnings.append({"id": "W1", "msg": f"{f.relative_to(root)}: ends at heading/colon"})
        if len(re.findall(r"^```", t, re.M)) % 2 == 1:
            warnings.append({"id": "W2", "msg": f"{f.relative_to(root)}: dangling fence"})
    return errors, warnings

def main():
    root = Path(sys.argv[1])
    errors, warnings = check(root)
    verdict = "PASS" if not errors else "FAIL"
    if "--json" in sys.argv:
        print(json.dumps({"verdict": verdict, "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    else:
        print(f"py-guard: {verdict}")
        for e in errors: print(f"  ERROR [{e['id']}] {e['msg']}")
        for w in warnings: print(f"  warn  [{w['id']}] {w['msg']}")
    sys.exit(0 if not errors else 1)

if __name__ == "__main__":
    main()
