#!/usr/bin/env python3
"""Local verification for the generated greeting-card evals (no skill-up run involved).

Checks:
  1. bash -n on every judge script;
  2. ast.parse on the python body embedded in every judge script;
  3. YAML parse of eval.yaml and every case file (when PyYAML is available);
  4. behavioral smoke test: judge scripts must PASS good cards and FAIL bad ones.
"""
import ast
import os
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parent / "target"
script_dir = root / "evals" / "fixtures" / "scripts"
problems = []

scripts = sorted(script_dir.glob("*.sh"))

for script in scripts:
    result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        problems.append(f"bash -n failed for {script.name}: {result.stderr.strip()}")

for script in scripts:
    text = script.read_text(encoding="utf-8")
    match = re.search(r"<<'PY'\n(.*?)\nPY\n", text, re.S)
    if not match:
        problems.append(f"no embedded python heredoc in {script.name}")
        continue
    try:
        ast.parse(match.group(1))
    except SyntaxError as exc:
        problems.append(f"python syntax error in {script.name}: {exc}")

yaml_files = [root / "evals" / "eval.yaml"] + sorted((root / "evals" / "cases").glob("*.yaml"))
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None
    print("NOTE: PyYAML unavailable, skipping YAML parse check")
if yaml is not None:
    for path in yaml_files:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append(f"YAML error in {path.name}: {exc}")

smoke_cases = [
    (
        "check-birthday-card.sh",
        "小雨，恭喜你跑完人生第一个半马，冲过终点线的那一刻一定很帅。生日快乐！🎉",
        0,
    ),
    (
        "check-birthday-card.sh",
        "好的，这是给你的生日祝福：\n小雨，生日快乐！🎂🎉",
        1,
    ),
    ("check-birthday-card.sh", "小雨，生日快乐！🎉", 1),
    (
        "check-english-card.sh",
        "Emma, congrats on shipping that project! Wishing you a wonderful birthday tomorrow. 🎉",
        0,
    ),
    ("check-english-card.sh", "Emma，祝你生日快乐！🎉", 1),
    ("check-english-card.sh", "Emma, happy birthday! 🎉🎂", 1),
    ("check-english-card.sh", "Dear Emma, wishing you a wonderful birthday tomorrow. 🎉", 1),
    ("check-english-card.sh", "Here is a birthday card for Emma: wishing you a wonderful year ahead. 🎉", 1),
]

for name, message, expected_rc in smoke_cases:
    env = dict(os.environ, EVAL_FINAL_MESSAGE=message)
    result = subprocess.run(
        ["bash", str(script_dir / name)], capture_output=True, text=True, env=env
    )
    ok = (result.returncode == 0) == (expected_rc == 0)
    label = "PASS" if expected_rc == 0 else "FAIL"
    print(("OK  " if ok else "BAD ") + f"{name} expect={label} rc={result.returncode}")
    first_line = (result.stdout.strip().splitlines() or [""])[0]
    if first_line:
        print("      " + first_line)
    if not ok:
        problems.append(f"{name}: expected {label} but rc={result.returncode}")

print()
if problems:
    print(f"{len(problems)} problem(s):")
    for problem in problems:
        print(" -", problem)
    sys.exit(1)
print("all local checks passed")
