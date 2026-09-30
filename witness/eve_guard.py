#!/usr/bin/env python3
"""eve-guard: deterministic integrity witness for an Eve agent directory.

Checks (hard errors -> exit 1):
  H1 agent/instructions.md exists and is non-empty
  H2 every relative path referenced from instructions.md exists on disk
  H3 every agent/skills/*/SKILL.md has non-empty frontmatter name/description
  H4 every agent/tools/*.ts has balanced braces/parens/brackets (syntax proxy)

Warnings (never fail alone):
  W1 file ends at a markdown heading or a colon (truncation signature)
  W2 dangling code fence (odd number of ``` lines)
  W3 empty file anywhere under agent/

Usage: eve_guard.py <agent-project-root> [--json]
"""
import json, re, sys
from pathlib import Path

def check(root: Path):
    errors, warnings = [], []
    agent = root / "agent"
    instr = agent / "instructions.md"
    if not instr.exists() or not instr.read_text().strip():
        errors.append({"id": "H1", "msg": "agent/instructions.md missing or empty"})
        instr_text = ""
    else:
        instr_text = instr.read_text()

    # H2: referenced paths like `skills/tone-guide/SKILL.md`
    for m in re.finditer(r"`((?:skills|tools|subagents|channels|schedules|connections)/[^`\s]+)`", instr_text):
        ref = m.group(1)
        if not (agent / ref).exists():
            errors.append({"id": "H2", "msg": f"referenced path missing: {ref}"})

    # H3: skill frontmatter
    for sk in sorted(agent.glob("skills/*/SKILL.md")):
        text = sk.read_text()
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not fm:
            errors.append({"id": "H3", "msg": f"{sk}: missing frontmatter"})
            continue
        for field in ("name", "description"):
            if not re.search(rf"^{field}:\s*\S", fm.group(1), re.M):
                errors.append({"id": "H3", "msg": f"{sk}: empty '{field}'"})

    # H4: tool syntax proxy
    for ts in sorted(agent.glob("tools/*.ts")):
        text = ts.read_text()
        for open_c, close_c in (("{", "}"), ("(", ")"), ("[", "]")):
            if text.count(open_c) != text.count(close_c):
                errors.append({"id": "H4", "msg": f"{ts.name}: unbalanced '{open_c}{close_c}'"})

    # W1/W2/W3
    for f in sorted(agent.rglob("*")):
        if not f.is_file():
            continue
        text = f.read_text()
        if not text.strip():
            warnings.append({"id": "W3", "msg": f"empty file: {f.relative_to(root)}"})
            continue
        tail = text.rstrip().splitlines()[-1].strip()
        if re.match(r"^#{1,6}\s+\S", tail) or tail.endswith(":"):
            warnings.append({"id": "W1", "msg": f"{f.relative_to(root)}: ends at heading/colon (truncation signature)"})
        if len(re.findall(r"^```", text, re.M)) % 2 == 1:
            warnings.append({"id": "W2", "msg": f"{f.relative_to(root)}: dangling code fence"})

    return errors, warnings

def main():
    root = Path(sys.argv[1])
    as_json = "--json" in sys.argv
    errors, warnings = check(root)
    verdict = "PASS" if not errors else "FAIL"
    if as_json:
        print(json.dumps({"verdict": verdict, "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    else:
        print(f"eve-guard: {verdict}")
        for e in errors: print(f"  ERROR [{e['id']}] {e['msg']}")
        for w in warnings: print(f"  warn  [{w['id']}] {w['msg']}")
    sys.exit(0 if not errors else 1)

if __name__ == "__main__":
    main()
