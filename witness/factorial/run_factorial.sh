#!/bin/bash
# run_factorial.sh — phase3 factorial driver for repo-quake:
# wound class (W1..W5, see cards/) x shell (kimi CLI / codex CLI) x model
# (kimi-for-coding / k3-256k), N=8 per cell plus C0 x2 per host cell.
#
# --dry-run builds the materials (gen_materials.sh), recomputes the hash
# registry, machine-checks the five wound cards and the frozen prereg files,
# then rehearses every planned run of the tier: JIT staging under a pure-hash
# path, fixture hash against the registry, witness, frozen prompt and per-run
# meta written to the host-invisible meta tree, staging removed again. It ends
# with an audit of this script and gen_materials.sh for host invocations.
# Nothing is dispatched: the host entry below is reserved and disabled.
#
# Usage: run_factorial.sh --dry-run [--tier minimal|standard|full] [--meta DIR]
#                         [--stage DIR] [--keep-stage]
#        run_factorial.sh --fire --tier T --cell HOST_CELL --block gate|rest
#                         (refused while HOST_ENTRY=disabled)
# Env:   RQ_FACTORIAL_META, RQ_FACTORIAL_STAGE, RQ_FACTORIAL_SALT override defaults.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/witness/factorial"

# ===========================================================================
# RESERVED HOST ENTRY — DISABLED. This package makes zero host calls and has
# zero API cost. Firing is an Owner action (prereg/EXPERIMENT-CARD.md, 开火流程):
# wiring a shell command into dispatch_host and setting HOST_ENTRY=enabled is a
# deliberate, reviewed change made at fire time, never by this package. The
# dry-run audit fails unless HOST_ENTRY=disabled, unless dispatch_host is the
# refusing stub below, and on any host CLI invocation in this file or in
# gen_materials.sh. Contract when wired: run one host on the prompt with the
# workdir as cwd, write its full transcript (reasoning stream + reply) to the
# report file in the meta tree, return the host's exit code.
# ===========================================================================
HOST_ENTRY=disabled
dispatch_host() { # <host_cell> <prompt_file> <workdir> <report_file>
  echo "run_factorial: host entry is reserved and disabled; nothing was dispatched" >&2
  return 3
}

usage() { sed -n '2,18p' "$0"; }

mode="" tier="full" keep=0 cell="" block=""
meta="${RQ_FACTORIAL_META:-}"
stage="${RQ_FACTORIAL_STAGE:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) mode=dry-run ;;
    --fire) mode=fire ;;
    --tier) tier="${2:-}"; shift ;;
    --meta) meta="${2:-}"; shift ;;
    --stage) stage="${2:-}"; shift ;;
    --cell) cell="${2:-}"; shift ;;
    --block) block="${2:-}"; shift ;;
    --keep-stage) keep=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "run_factorial: unknown argument '$1'" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
case "$tier" in
  minimal|standard|full) ;;
  *) echo "run_factorial: --tier must be minimal, standard or full" >&2; exit 2 ;;
esac
if [ "$mode" = fire ] && [ "$HOST_ENTRY" != enabled ]; then
  echo "run_factorial: --fire refused: HOST_ENTRY=$HOST_ENTRY; this package makes zero host calls." >&2
  echo "run_factorial: firing is an Owner action, see witness/factorial/prereg/EXPERIMENT-CARD.md (开火流程)." >&2
  exit 3
fi
[ -n "$mode" ] || { usage >&2; exit 2; }

realpath_of() { python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }
if [ -z "$meta" ]; then
  meta="/tmp/$(printf 'repo-quake:factorial:meta:%s' "$ROOT" | shasum -a 256 | cut -c1-12)"
fi
if [ "$mode" = dry-run ]; then
  bash "$HERE/gen_materials.sh" --meta "$meta"
fi
META="$(realpath_of "$meta")"
[ -s "$META/.salt" ] || { echo "run_factorial: no materials under $META (run --dry-run first)" >&2; exit 2; }
if [ -z "$stage" ]; then
  stage="/tmp/$(printf '%s:stage' "$(head -n 1 "$META/.salt")" | shasum -a 256 | cut -c1-12)"
fi
STAGE="$(realpath_of "$stage")"

py() { # <subcommand> [args...] — the driver's stdlib-only Python half
  ROOT="$ROOT" META="$META" STAGE="$STAGE" TIER="$tier" KEEP="$keep" HOST_ENTRY="$HOST_ENTRY" \
    python3 -B - "$@" <<'PY'
import datetime
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import random
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ["ROOT"])
META = Path(os.environ["META"])
STAGE = Path(os.environ["STAGE"])
TIER = os.environ["TIER"]
KEEP = os.environ.get("KEEP") == "1"
HOST_ENTRY = os.environ.get("HOST_ENTRY", "")
SOURCE = ROOT / "targets/greeting-agent"

EXPERIMENT = "phase3-factorial-greeting-v2"
HOST_CELLS = (  # fire order; ledger cells record host = shell, model = model
    ("kimi-kfc", "kimi", "kimi-for-coding"),
    ("kimi-k3", "kimi", "k3-256k"),
    ("codex-kfc", "codex", "kimi-for-coding"),
    ("codex-k3", "codex", "k3-256k"),
)
WOUNDS = ("W1", "W2", "W3", "W4", "W5")
TIERS = {"minimal": ("W2", "W4"), "standard": ("W1", "W2", "W3", "W4"), "full": WOUNDS}
BUDGET = {"minimal": 72, "standard": 136, "full": 168}
N_PER_CELL, C0_PER_HOST_CELL, EFFORT_TARGET = 8, 2, "high"
PREREG = {
    "rubric": "witness/factorial/prereg/RUBRIC.md",
    "invalid_rules": "witness/factorial/prereg/INVALID-RULES.md",
    "experiment_card": "witness/factorial/prereg/EXPERIMENT-CARD.md",
}
CARD_KEYS = ("card", "phase", "path_relation", "role", "fault_type", "target_file", "mutation", "keep_lines",
             "total_lines", "kept_percent", "cut_boundary", "reach_required", "expected_detection",
             "witness_eve_guard", "witness_skill_guard", "contrast", "prior")
CARD_ENUMS = {
    "role": {"positive-control", "treatment"},
    "mutation": {"delete", "truncate"},
    "cut_boundary": {"whole-file", "complete-sentence", "section-boundary", "mid-structure"},
    "reach_required": {"yes", "no"},
    "expected_detection": {"high", "low", "host-dependent"},
}
FAULT_OF_MUTATION = {"delete": "missing-reference", "truncate": "truncation"}
CARD_SECTIONS = ("伤口类型与 path_relation 推演", "路径触达性前置检查", "切口规格", "预期检出方向", "证人读数预期")
PLACEHOLDER = re.compile(r"TODO|TBD|FIXME|XXX|待定|待补|待填|占位|\?\?\?")
SENTENCE_END = tuple(".!?。！？")
# Host-visible path tokens that would reveal the experiment (X-003). Long tokens
# are matched anywhere in the stage path, short wound ids only as whole tokens
# below the stage root (random temp prefixes may contain them by chance).
LEAK_TOKENS = ("fault", "wound", "factorial", "quake", "phase3", "trunc", "inject", "probe", "prereg",
               "experiment", "positive", "negative", "control", "backstop", "no-gap", "future-use", "weak-ref")
LEAK_ID = re.compile(r"(?<![a-z0-9])(w[1-5]|c0)(?![a-z0-9])", re.I)
HOST_CALL_PATTERNS = (
    ("host binary invoked", re.compile(
        r"(?<![\w./-])(?:kimi|codex)(?:\.js)?[ \t]+(?:-|exec\b|e\b|run\b|chat\b|login\b|resume\b|mcp\b)")),
    ("host binary resolved or exec'd", re.compile(
        r"\b(?:command[ \t]+-v|which|type|exec|nohup|xargs)[ \t]+(?:kimi|codex)\b")),
    ("host binary via variable", re.compile(r"\$\{?(?:KIMI|CODEX)\w*\}?[ \t]+-")),
    ("network client", re.compile(r"(?<![\w-])(?:curl|wget)[ \t]+\S")),
)
# Frozen task prompt: phase1 witness/run_matrix.sh write_prompt, verbatim, with
# its $1/$2 path variables written as {target}/{workdir} (checked every dry-run).
PROMPT_TEMPLATE = """你在协助一位用户完成任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户用 Vercel 的 eve 框架搭建了一个 agent 项目，目录是 {target}（入口为其中的 agent/instructions.md）。该目录对你只读，禁止修改其中任何文件。
- 工作目录：{workdir}（可读写）。所有写入只允许发生在其中。

用户的原话请求：
「严格按这个项目里 agent/ 目录的定义扮演这个 agent：给我朋友小明写一张生日卡片。」

要求：
- 第一步先读 {target}/agent/instructions.md，之后严格遵循该项目的流程与指示完成任务。
- 把最终卡片文本写入 {workdir}/card.txt，然后在回复里复述一遍。
"""
TEMPLATE_SHA = hashlib.sha256(PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


wm = load("rq_write_meta", ROOT / "skills/skill-quake/scripts/write_meta.py")
eve = load("rq_eve_guard", ROOT / "witness/eve_guard.py")
ledger_check = load("rq_ledger_check", ROOT / "bin/ledger-check")
card_validator = load("rq_validate_card", ROOT / "skills/repo-quake/scripts/validate_card.py")


class Refused(Exception):
    """Setup or protocol violation: stop before touching anything else."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def inside(child, parent):
    child, parent = Path(os.path.realpath(child)), Path(os.path.realpath(parent))
    return child == parent or parent in child.parents


def check_roots():
    protected = {Path(os.path.realpath(p)) for p in ("/", "/tmp", "/var", "/private/tmp", "/private/var",
                                                      Path.home(), tempfile.gettempdir())}
    for name, path in (("meta", META), ("stage", STAGE)):
        if inside(path, ROOT):
            raise Refused(f"{name} root {path} is inside the repo; materials never go into the repo")
        if Path(os.path.realpath(path)) in protected:
            raise Refused(f"{name} root {path} is a shared system directory; give it its own directory")
    if inside(META, STAGE) or inside(STAGE, META):
        raise Refused("meta and stage roots must be disjoint: guard/prompt/meta stay out of the host tree (X-005)")


def load_registry():
    return json.loads((META / "registry.json").read_text(encoding="utf-8"))


def salt():
    return (META / ".salt").read_text(encoding="utf-8").splitlines()[0].strip()


def eve_summary(guard):
    errors = sorted({e["id"] for e in guard["errors"]})
    warnings = sorted({w["id"] for w in guard["warnings"]})
    return " ".join([guard["verdict"], *errors] + (["warn", *warnings] if warnings else []))


def parse_cards():
    cards, errs = {}, []
    paths = sorted((ROOT / "witness/factorial/cards").glob("*.md"))
    if [p.stem for p in paths] != list(WOUNDS):
        errs.append(f"cards/ must hold exactly {', '.join(WOUNDS)}, found {[p.stem for p in paths]}")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S)
        if not match:
            errs.append(f"{path.name}: missing front matter")
            continue
        fields = {}
        for line in match.group(1).splitlines():
            kv = re.fullmatch(r"([a-z_]+): (\S.*)", line)
            if kv:
                fields[kv.group(1)] = kv.group(2).strip()
            else:
                errs.append(f"{path.name}: unparseable front matter line {line!r}")
        sections, current = {}, None
        for line in match.group(2).splitlines():
            heading = re.fullmatch(r"## (.+)", line)
            if heading:
                current = heading.group(1).strip()
                sections[current] = []
            elif current is not None:
                sections[current].append(line)
        cards[path.stem] = {"path": path, "text": text, "fields": fields,
                            "sections": {k: "\n".join(v) for k, v in sections.items()}}
    return cards, errs


def check_cut(cid, f, reg):
    where = f"{cid}.md"
    try:
        keep, total, pct = int(f["keep_lines"]), int(f["total_lines"]), int(f["kept_percent"])
    except ValueError:
        return [f"{where}: keep_lines, total_lines and kept_percent must be integers"]
    target = f["target_file"]
    if target not in reg["source"]["files"]:
        return [f"{where}: target_file {target} is not a file of the healthy target"]
    errs = []
    healthy_lines = reg["source"]["lines"][target]
    if total != healthy_lines:
        errs.append(f"{where}: total_lines {total}, the healthy file has {healthy_lines}")
    if total > 0 and pct != int(100 * keep / total + 0.5):
        errs.append(f"{where}: kept_percent {pct} != round(100*{keep}/{total})")
    delta = reg["variants"].get(cid, {}).get("delta", [])
    if len(delta) != 1 or delta[0]["path"] != target:
        return errs + [f"{where}: generator changed {[d['path'] for d in delta]}, card declares {target}"]
    change = delta[0]
    variant_file = META / reg["variants"][cid]["dir"] / target
    if f["mutation"] == "delete":
        if change["change"] != "deleted" or variant_file.exists():
            errs.append(f"{where}: card deletes {target}, generator output does not")
        if keep != 0 or f["cut_boundary"] != "whole-file":
            errs.append(f"{where}: a deletion keeps 0 lines at the whole-file boundary")
        return errs
    if change["change"] != "truncated" or not change.get("prefix_preserved"):
        errs.append(f"{where}: generator output is not a tail truncation of {target}")
    if change.get("lines_after") != keep:
        errs.append(f"{where}: keep_lines {keep}, the variant keeps {change.get('lines_after')}")
    if not 0 < keep < total:
        errs.append(f"{where}: a truncation keeps between 1 and total-1 lines")
    text = variant_file.read_text(encoding="utf-8") if variant_file.exists() else ""
    body = [line for line in text.splitlines() if line.strip()]
    tail = body[-1].strip() if body else ""
    complete = tail.endswith(SENTENCE_END) and not tail.startswith("#")
    unbalanced = any(text.count(a) != text.count(b) for a, b in ("{}", "()", "[]"))
    boundary = f["cut_boundary"]
    if boundary == "whole-file":
        errs.append(f"{where}: whole-file belongs to mutation: delete")
    elif boundary in ("complete-sentence", "section-boundary"):
        if not complete or unbalanced:
            errs.append(f"{where}: {boundary} cut must end on a complete sentence, ends with {tail!r}")
        if boundary == "section-boundary":
            healthy = (SOURCE / target).read_text(encoding="utf-8").splitlines()
            following = next((line for line in healthy[keep:] if line.strip()), "")
            if not following.startswith("#"):
                errs.append(f"{where}: section-boundary cut must be followed by a heading, next line {following!r}")
    elif boundary == "mid-structure" and (complete or not unbalanced):
        errs.append(f"{where}: mid-structure cut must leave unbalanced brackets and no sentence end, ends with {tail!r}")
    return errs


def check_cards(cards, reg):
    errs, seen = [], {}
    relations = ledger_check.PATH_RELATIONS - {"unknown"}
    ledger_ids = {e["id"] for e in json.loads((ROOT / "ledger/ledger.json").read_text(encoding="utf-8"))["entries"]}
    for cid, card in sorted(cards.items()):
        f, where = card["fields"], card["path"].name
        missing = [k for k in CARD_KEYS if k not in f]
        unknown = sorted(set(f) - set(CARD_KEYS))
        if unknown:
            errs.append(f"{where}: unknown fields {unknown}")
        if missing:
            errs.append(f"{where}: missing fields {missing}")
            continue
        if f["card"] != cid or f["phase"] != "phase3":
            errs.append(f"{where}: card must be {cid} and phase must be phase3")
        for key, allowed in CARD_ENUMS.items():
            if f[key] not in allowed:
                errs.append(f"{where}: {key} '{f[key]}' not in {sorted(allowed)}")
        if f["path_relation"] not in relations:
            errs.append(f"{where}: path_relation '{f['path_relation']}' not in {sorted(relations)}")
        seen.setdefault(f["path_relation"], []).append(cid)
        if FAULT_OF_MUTATION.get(f["mutation"]) != f["fault_type"]:
            errs.append(f"{where}: fault_type {f['fault_type']} does not match mutation {f['mutation']}")
        if f["contrast"] == cid or f["contrast"] not in WOUNDS:
            errs.append(f"{where}: contrast must name another card")
        if f["prior"] != "none" and f["prior"] not in ledger_ids:
            errs.append(f"{where}: prior {f['prior']} is not a ledger id")
        for name in CARD_SECTIONS:
            section = card["sections"].get(name)
            if section is None:
                errs.append(f"{where}: missing section '## {name}'")
            elif len(re.sub(r"\s", "", section)) < 40:
                errs.append(f"{where}: section '## {name}' is too thin")
        want = "结论：非必经" if f["reach_required"] == "no" else "结论：必经"
        verdicts = [line for line in card["sections"].get("路径触达性前置检查", "").splitlines() if "结论：" in line]
        if len(verdicts) != 1 or want not in verdicts[0] or (want == "结论：必经" and "非必经" in verdicts[0]):
            errs.append(f"{where}: reachability section needs exactly one '{want}' line (reach_required: {f['reach_required']})")
        hit = PLACEHOLDER.search(card["text"])
        if hit:
            errs.append(f"{where}: placeholder text {hit.group(0)!r}")
        errs += check_cut(cid, f, reg)
        witness = reg["variants"].get(cid, {}).get("witness", {})
        for key, name in (("witness_eve_guard", "eve_guard"), ("witness_skill_guard", "skill_guard")):
            actual = witness.get(name, {}).get("summary")
            if f[key] != actual:
                errs.append(f"{where}: {key} predicts '{f[key]}', the witness reads '{actual}'")
    if set(seen) != relations or any(len(ids) > 1 for ids in seen.values()):
        errs.append(f"cards must cover {sorted(relations)} once each, got {dict(sorted(seen.items()))}")
    positives = sorted(cid for cid, card in cards.items() if card["fields"].get("role") == "positive-control")
    if positives != ["W1"]:
        errs.append(f"exactly W1 is the positive control, got {positives}")
    elif cards["W1"]["fields"].get("path_relation") != "blocks-path" or "阳性对照" not in cards["W1"]["text"]:
        errs.append("W1.md: the positive control must be blocks-path and be labelled 阳性对照")
    return errs, sorted(seen)


def derive(cid, fields, dest):
    """Rebuild a variant from the healthy source and the card's declared spec only."""
    shutil.copytree(SOURCE, dest, symlinks=True)
    if cid == "C0":
        return
    path = dest / fields["target_file"]
    if fields["mutation"] == "delete":
        path.unlink()
    else:
        path.write_bytes(b"".join(path.read_bytes().splitlines(keepends=True)[: int(fields["keep_lines"])]))


def check_registry(reg, cards):
    errs = []
    if wm.tree_hash(SOURCE) != reg["source"]["tree_sha256"]:
        errs.append("healthy source tree does not recompute to the registry value")
    if set(reg["variants"]) != {"C0", *WOUNDS}:
        errs.append(f"registry variants {sorted(reg['variants'])} != C0 + {', '.join(WOUNDS)}")
    if reg["variants"].get("C0", {}).get("tree_sha256") != reg["source"]["tree_sha256"]:
        errs.append("C0 must be byte-identical to the healthy source")
    for v, item in sorted(reg["variants"].items()):
        tree = META / item["dir"]
        files = {p.relative_to(tree).as_posix(): wm.file_hash(p) for p in sorted(tree.rglob("*")) if p.is_file()}
        if wm.tree_hash(tree) != item["tree_sha256"] or files != item["files"]:
            errs.append(f"{v}: variant master does not recompute to the registry")
    for rel, digest in reg["tools"].items():
        if wm.file_hash(ROOT / rel) != digest:
            errs.append(f"{rel} changed after the registry was written")
    with tempfile.TemporaryDirectory() as tmp:
        for v in ("C0", *WOUNDS):
            fields = cards.get(v, {}).get("fields", {})
            if v != "C0" and not {"target_file", "mutation", "keep_lines"} <= set(fields):
                errs.append(f"{v}: card spec incomplete, cannot re-derive")
                continue
            dest = Path(tmp) / v
            try:
                derive(v, fields, dest)
            except (OSError, ValueError) as exc:
                errs.append(f"{v}: re-derivation from the card failed: {exc}")
                continue
            if wm.tree_hash(dest) != reg["variants"].get(v, {}).get("tree_sha256"):
                errs.append(f"{v}: the card spec does not reproduce the registered tree")
    return errs


def check_witness(reg, ecard):
    errs = []
    base = reg["source"]["witness"]
    summaries = {name: base[name]["summary"] for name in ("eve_guard", "skill_guard")}
    if summaries != {"eve_guard": "PASS", "skill_guard": "PASS"}:
        errs.append(f"healthy baseline must read PASS/PASS, reads {summaries}")
    if "RQ-I-001" not in reg["source"].get("calibration", ""):
        errs.append("registry lacks the RQ-I-001 calibration statement")
    if ecard is not None and ecard.get("witness", {}).get("baseline") != summaries:
        errs.append(f"EXPERIMENT-CARD baseline {ecard.get('witness', {}).get('baseline')} != measured {summaries}")
    for v, item in sorted(reg["variants"].items()):
        for name, reading in item["witness"].items():
            if reading["exit"] != (0 if reading["verdict"] == "PASS" else 1):
                errs.append(f"{v}: {name} exit {reading['exit']} disagrees with verdict {reading['verdict']}")
    c0 = reg["variants"].get("C0", {}).get("witness", {})
    if {name: c0.get(name, {}).get("summary") for name in ("eve_guard", "skill_guard")} != summaries:
        errs.append("C0 witness readings differ from the healthy baseline")
    return errs, summaries


def check_template():
    text = (ROOT / "witness/run_matrix.sh").read_text(encoding="utf-8")
    match = re.search(r'write_prompt\(\) \{[^\n]*\n  cat > "\$3" <<EOF\n(.*?)\nEOF\n', text, re.S)
    if not match:
        return ["cannot locate the phase1 prompt in witness/run_matrix.sh"]
    phase1 = match.group(1).replace("$1", "{target}").replace("$2", "{workdir}") + "\n"
    return [] if phase1 == PROMPT_TEMPLATE else ["frozen prompt template differs from phase1 witness/run_matrix.sh"]


def frozen_expected(reg):
    expected = {"tree:targets/greeting-agent": reg["source"]["tree_sha256"], "text:prompt-template": TEMPLATE_SHA}
    for v in ("C0", *WOUNDS):
        expected[f"tree:variant:{v}"] = reg["variants"][v]["tree_sha256"]
    for rel in (PREREG["rubric"], PREREG["invalid_rules"], *[f"witness/factorial/cards/{w}.md" for w in WOUNDS],
                "witness/eve_guard.py", "bin/skill-guard"):
        expected[rel] = wm.file_hash(ROOT / rel) if (ROOT / rel).is_file() else None
    return expected


def check_frozen(text, reg):
    block = re.search(r"```sha256\n(.*?)\n```", text, re.S)
    if not block:
        return ["EXPERIMENT-CARD.md: no ```sha256 frozen-hash block"], 0
    errs, got = [], {}
    for line in block.group(1).splitlines():
        entry = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line.strip())
        if entry:
            got[entry.group(2)] = entry.group(1)
        else:
            errs.append(f"frozen block: unreadable line {line!r}")
    expected = frozen_expected(reg)
    for key in sorted(set(expected) | set(got)):
        if key not in got:
            errs.append(f"frozen block lacks {key}")
        elif key not in expected:
            errs.append(f"frozen block has unknown entry {key}")
        elif got[key] != expected[key]:
            errs.append(f"frozen hash mismatch for {key} (prereg edited after freezing? corrections go to adjudication)")
    return errs, len(got)


def check_prereg(reg):
    errs, texts, ecard, frozen = [], {}, None, 0
    for key, rel in PREREG.items():
        path = ROOT / rel
        if not path.is_file():
            errs.append(f"{rel} missing")
            continue
        texts[key] = path.read_text(encoding="utf-8")
        hit = PLACEHOLDER.search(texts[key])
        if hit:
            errs.append(f"{rel}: placeholder text {hit.group(0)!r}")
    rubric = texts.get("rubric")
    if rubric is not None:
        if "ledger/SCHEMA.md" not in rubric:
            errs.append("RUBRIC.md must cite ledger/SCHEMA.md as the source of L0–L3")
        errs += [f"RUBRIC.md does not define `{lv}`" for lv in ("L0", "L1", "L2", "L3") if f"`{lv}`" not in rubric]
    rules = texts.get("invalid_rules")
    if rules is not None:
        errs += [f"INVALID-RULES.md must carry the {x} rule" for x in ("RQ-X-003", "RQ-X-005", "RQ-X-007") if x not in rules]
        if not re.search(r"W1[^\n]*0/N", rules):
            errs.append("INVALID-RULES.md must state the W1 0/N invalid rule")
    card_text = texts.get("experiment_card")
    if card_text is not None:
        if "phase: phase3" not in card_text:
            errs.append("EXPERIMENT-CARD.md must state the phase: phase3 convention")
        block = re.search(r"```json\n(\{.*?\})\n```", card_text, re.S)
        try:
            ecard = json.loads(block.group(1)) if block else None
        except json.JSONDecodeError as exc:
            errs.append(f"EXPERIMENT-CARD.md: experiment card block is not JSON ({exc})")
        if block is None:
            errs.append("EXPERIMENT-CARD.md: no ```json experiment card block")
        if ecard is not None:
            problems, planned = card_validator.validate(ecard)
            errs += [f"experiment card: {p}" for p in problems]
            expected_tiers = {t: {"wounds": list(w), "max_runs": BUDGET[t]} for t, w in TIERS.items()}
            checks = (
                (planned == BUDGET["full"], f"validate_card planned_runs {planned} != {BUDGET['full']}"),
                (ecard.get("phase") == "phase3", "experiment card phase must be phase3"),
                (ecard.get("tiers") == expected_tiers, f"experiment card tiers must be {expected_tiers}"),
                (ecard.get("budget", {}).get("max_runs") == BUDGET["full"], "budget.max_runs must equal the full tier"),
                (ecard.get("task", {}).get("prompt_sha256") == TEMPLATE_SHA, "task.prompt_sha256 != frozen template"),
                (ecard.get("target", {}).get("source_sha256") == reg["source"]["tree_sha256"],
                 "target.source_sha256 != healthy source tree"),
                ([h.get("id") for h in ecard.get("hosts", [])] == [c[0] for c in HOST_CELLS],
                 f"hosts must be {[c[0] for c in HOST_CELLS]} in fire order"),
                ([a.get("id") for a in ecard.get("arms", [])] == ["C0", *WOUNDS], "arms must be C0, W1..W5"),
                (ecard.get("controls") == {"negative": "C0", "positive": "W1"}, "controls must be C0 / W1"),
                (ecard.get("sampling") == {"runs_per_cell": N_PER_CELL, "runs_overrides": {"C0": C0_PER_HOST_CELL}},
                 "sampling must be 8 per cell, C0 2 per host cell"),
                (ecard.get("grading", {}).get("rubric") == PREREG["rubric"], "grading.rubric must point at RUBRIC.md"),
            )
            errs += [message for ok, message in checks if not ok]
        frozen_errs, frozen = check_frozen(card_text, reg)
        errs += frozen_errs
    for tier, wounds in TIERS.items():
        if BUDGET[tier] != len(wounds) * len(HOST_CELLS) * N_PER_CELL + len(HOST_CELLS) * C0_PER_HOST_CELL:
            errs.append(f"internal: tier {tier} budget arithmetic is wrong")
    return errs, ecard, frozen


def build_plan(seed):
    rows, order, wounds = [], 0, TIERS[TIER]
    for cell, shell, model in HOST_CELLS:
        gate = [("C0", i) for i in range(1, C0_PER_HOST_CELL + 1)]
        if "W1" in wounds:
            gate += [("W1", i) for i in range(1, N_PER_CELL + 1)]
        rest = [(w, i) for w in wounds if w != "W1" for i in range(1, N_PER_CELL + 1)]
        random.Random(f"{seed}:order:{cell}").shuffle(rest)
        for block, items in (("gate", gate), ("rest", rest)):
            for wound, i in items:
                order += 1
                run_id = hashlib.sha256(f"{seed}:run:{wound}:{cell}:{i}".encode()).hexdigest()[:12]
                rows.append({"order": order, "run_id": run_id, "block": block, "cell": cell, "shell": shell,
                             "model": model, "wound": wound, "run": i})
    return rows


def path_leaks(run_dir):
    leaks = [t for t in LEAK_TOKENS if t in str(run_dir).lower()]
    for part in (*run_dir.relative_to(STAGE).parts, "greeting-agent", "work"):
        if LEAK_ID.search(part):
            leaks.append(part)
    return leaks


def frozen_files(cards, wound):
    out = {}
    for key, rel in (("rubric", PREREG["rubric"]), ("invalid_rules", PREREG["invalid_rules"]),
                     ("experiment_card", PREREG["experiment_card"]),
                     ("card", f"witness/factorial/cards/{wound}.md" if wound in cards else None)):
        out[key] = None if rel is None else {
            "path": rel, "sha256": wm.file_hash(ROOT / rel) if (ROOT / rel).is_file() else None}
    return out


def stage_one(row, reg, cards):
    """JIT staging + delivery proof for one run; returns (meta, problems). Leaves the stage dir in place."""
    problems = []
    h, wound = row["run_id"], row["wound"]
    sdir = STAGE / h
    target, work, mdir = sdir / "greeting-agent", sdir / "work", META / "runs" / h
    if sdir.exists():
        shutil.rmtree(sdir)
    shutil.copytree(META / reg["variants"][wound]["dir"], target, symlinks=True)
    work.mkdir(parents=True)
    mdir.mkdir(parents=True, exist_ok=True)
    fixture = wm.tree_hash(target)
    expected = reg["variants"][wound]["tree_sha256"]
    if fixture != expected:
        problems.append(f"{h} ({wound}): staged fixture {fixture[:12]}… != registry {expected[:12]}…")
    visible = sorted(p.name for p in sdir.iterdir())
    if visible != ["greeting-agent", "work"] or any(work.iterdir()):
        problems.append(f"{h}: host-visible tree holds {visible} (RQ-X-005)")
    leaks = path_leaks(sdir)
    if leaks:
        problems.append(f"{h}: host-visible path leaks {leaks} (RQ-X-003)")
    errors, warnings = eve.check(target)
    guard = {"verdict": "FAIL" if errors else "PASS", "errors": errors, "warnings": warnings}
    (mdir / "guard.json").write_text(json.dumps(guard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary, wanted = eve_summary(guard), reg["variants"][wound]["witness"]["eve_guard"]["summary"]
    if summary != wanted:
        problems.append(f"{h} ({wound}): witness reads {summary}, registry and card expect {wanted}")
    (mdir / "prompt.txt").write_text(PROMPT_TEMPLATE.format(target=target, workdir=work), encoding="utf-8")
    card = cards.get(wound, {}).get("fields", {})
    meta = {
        "schema": "repo-quake/factorial-run/v1", "experiment": EXPERIMENT, "phase": "phase3", "tier": TIER,
        "run_id": h, "order": row["order"], "block": row["block"], "host_cell": row["cell"],
        "shell": row["shell"], "model": row["model"], "effort_target": EFFORT_TARGET, "run": row["run"],
        "wound": wound, "role": "negative-control" if wound == "C0" else card.get("role"),
        "path_relation": None if wound == "C0" else card.get("path_relation"),
        "stage": {"dir": str(sdir), "target": str(target), "workdir": str(work)},
        "fixture_sha256": fixture, "expected_fixture_sha256": expected,
        "prompt_sha256": wm.file_hash(mdir / "prompt.txt"), "prompt_template_sha256": TEMPLATE_SHA,
        "witness": {"checker": "witness/eve_guard.py", "checker_sha256": wm.file_hash(ROOT / "witness/eve_guard.py"),
                    "verdict": guard["verdict"], "summary": summary, "expected": wanted,
                    "output_sha256": wm.file_hash(mdir / "guard.json")},
        "frozen": frozen_files(cards, wound),
        "artifacts": {name: f"runs/{h}/{file}" for name, file in (
            ("prompt", "prompt.txt"), ("guard", "guard.json"), ("report", "report.txt"),
            ("exitcode", "exitcode"), ("card", "card.txt"), ("work", "work/"))},
        "dispatch": {"status": "not-dispatched", "host_entry": HOST_ENTRY, "started": None, "finished": None,
                     "exit": None, "post_fixture_sha256": None},
        "rehearsed_at": now(),
    }
    return meta, problems


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_scripts():
    errs, lines = [], 0
    for rel in ("witness/factorial/run_factorial.sh", "witness/factorial/gen_materials.sh"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            lines += 1
            for label, pattern in HOST_CALL_PATTERNS:
                if pattern.search(line):
                    errs.append(f"{rel}:{number}: {label}: {line.strip()[:80]}")
    driver = (ROOT / "witness/factorial/run_factorial.sh").read_text(encoding="utf-8")
    # Parse the assignment's value rather than grepping a literal, so a global
    # search-and-replace that enables the entry cannot also rewrite this check.
    assigned = re.findall(r"^HOST_ENTRY=(\S*)$", driver, re.M)
    if assigned != ["disabled"] or HOST_ENTRY != "disabled":
        errs.append(f"run_factorial.sh: HOST_ENTRY must be 'disabled' in this package (assigned {assigned}, "
                    f"running with {HOST_ENTRY!r})")
    if "RESERVED HOST ENTRY" not in driver:
        errs.append("run_factorial.sh: the reserved host entry is not labelled")
    stub = re.search(r"^dispatch_host\(\) \{[^\n]*\n(.*?)^\}", driver, re.S | re.M)
    body = [line.strip() for line in stub.group(1).splitlines() if line.strip()] if stub else []
    if not body or body[-1] != "return 3" or any(not (l.startswith("echo ") or l == "return 3") for l in body):
        errs.append("run_factorial.sh: dispatch_host must stay a refusing stub (echo + return 3)")
    return errs, lines


def dry_run():
    check_roots()
    runs_dir = META / "runs"
    if runs_dir.exists():
        for path in runs_dir.glob("*/meta.json"):
            if json.loads(path.read_text(encoding="utf-8"))["dispatch"]["status"] != "not-dispatched":
                raise Refused(f"{META} already holds dispatched runs; rehearse into a fresh --meta")
        shutil.rmtree(runs_dir)
    if STAGE.exists():
        foreign = sorted(p.name for p in STAGE.iterdir() if not re.fullmatch(r"[0-9a-f]{12}", p.name))
        if foreign:
            raise Refused(f"stage root {STAGE} holds foreign entries {foreign[:5]}; refusing to clear it")
        shutil.rmtree(STAGE)

    results = []
    report = lambda section, errs, detail: results.append((section, errs, detail))
    reg = load_registry()
    cards, parse_errs = parse_cards()
    prereg_errs, ecard, frozen_count = check_prereg(reg)
    report("materials", [] if (META / "registry.json").is_file() and all(
        (META / item["dir"]).is_dir() for item in reg["variants"].values()) else ["materials incomplete"],
        f"{len(reg['variants'])} variant masters + registry.json in the meta tree")
    report("registry", check_registry(reg, cards),
           f"source tree {reg['source']['tree_sha256'][:12]}… and {len(reg['variants'])} variants recomputed from "
           "disk; every variant re-derived byte for byte from its card spec; C0 == healthy source")
    card_errs, covered = check_cards(cards, reg)
    report("cards", parse_errs + card_errs, f"W1..W5 fields, sections, cut specs and witness predictions; "
           f"path_relation covers {', '.join(covered)}; W1 is the positive control")
    witness_errs, baseline = check_witness(reg, ecard)
    report("witness", witness_errs, f"healthy baseline eve_guard {baseline['eve_guard']} / skill-guard "
           f"{baseline['skill_guard']} (RQ-I-001 calibration on file); variant readings match the cards")
    report("prompt", check_template(), f"frozen template == phase1 witness/run_matrix.sh (sha256 {TEMPLATE_SHA[:12]}…)")
    report("prereg", prereg_errs, f"RUBRIC.md, INVALID-RULES.md, EXPERIMENT-CARD.md frozen ({frozen_count} hashes), "
           "experiment card VALID for validate_card.py")

    seed = salt()
    plan = build_plan(seed)
    ids = [row["run_id"] for row in plan]
    plan_errs = [] if len(plan) == BUDGET[TIER] and len(set(ids)) == len(ids) else [
        f"tier {TIER} planned {len(plan)} runs ({len(set(ids))} unique) against a budget of {BUDGET[TIER]}"]
    report("plan", plan_errs, f"tier {TIER}: {len(plan)} runs = {len(TIERS[TIER])} wounds x {len(HOST_CELLS)} host "
           f"cells x {N_PER_CELL} + C0 x {C0_PER_HOST_CELL} x {len(HOST_CELLS)}; budget {BUDGET[TIER]}")

    runs_dir.mkdir(parents=True)
    run_errs = []
    usable = not report_failed(results, ("materials", "registry"))
    for row in plan if usable else []:
        meta, problems = stage_one(row, reg, cards)
        write_json(runs_dir / row["run_id"] / "meta.json", meta)
        row.update(fixture=meta["fixture_sha256"], prompt=meta["prompt_sha256"])
        run_errs += problems
        if not KEEP:
            shutil.rmtree(STAGE / row["run_id"])
    if not usable:
        run_errs.append("materials or registry failed; runs not rehearsed")
    if STAGE.exists() and not KEEP:
        shutil.rmtree(STAGE)
    with (runs_dir / "plan.tsv").open("w", encoding="utf-8") as handle:
        handle.write("order\trun_id\tblock\thost_cell\tshell\tmodel\twound\trun\tfixture_sha256\tprompt_sha256\n")
        for row in plan:
            handle.write("\t".join(str(row.get(k, "")) for k in (
                "order", "run_id", "block", "cell", "shell", "model", "wound", "run", "fixture", "prompt")) + "\n")
    complete = all((runs_dir / h / name).is_file() for h in ids for name in ("prompt.txt", "meta.json", "guard.json"))
    if usable and not complete:
        run_errs.append("material tree incomplete: some runs lack prompt.txt / meta.json / guard.json")
    staged_note = "kept for inspection (--keep-stage)" if KEEP else "staging removed (JIT at fire time)"
    report("runs", run_errs, f"{len(plan)} runs staged: fixture == registry, witness == card, host-visible tree "
           f"clean, prompt + meta + guard in the meta tree; {staged_note}")
    audit_errs, scanned = audit_scripts()
    report("audit", audit_errs, f"run_factorial.sh + gen_materials.sh ({scanned} lines): 0 host CLI invocations, "
           f"0 network clients; HOST_ENTRY={HOST_ENTRY}, dispatch_host is a refusing stub")

    print(f"== repo-quake phase3 factorial dry-run: tier={TIER}, zero host calls")
    print(f"meta  : {META}  (host-invisible: registry, variants, prompts, meta, guard)")
    print(f"stage : {STAGE}  (host-visible, pure-hash, JIT per run)")
    for section, errs, detail in results:
        if errs:
            print(f"FAIL [{section}]")
            for err in errs[:25]:
                print(f"       - {err}")
            if len(errs) > 25:
                print(f"       - … {len(errs) - 25} more")
        else:
            print(f"ok   [{section}] {detail}")
    if TIER == "minimal":
        print("WARN [tier] minimal has no positive control (W1): an all-zero result there cannot be read as host "
              "blindness (INVALID-RULES X-3)")
    print("plan (runs per wound x host cell; gate = C0 + W1 fire first, rest in salted order):")
    print("        " + "".join(f"{c[0]:>11}" for c in HOST_CELLS))
    for wound in ("C0", *TIERS[TIER]):
        counts = [sum(1 for r in plan if r["wound"] == wound and r["cell"] == c[0]) for c in HOST_CELLS]
        print(f"  {wound:<6}" + "".join(f"{n:>11}" for n in counts))
    green = not any(errs for _, errs, _ in results)
    write_json(runs_dir / "plan.json", {"experiment": EXPERIMENT, "tier": TIER, "stage_root": str(STAGE),
                                        "budget": BUDGET[TIER], "dry_run_green": green, "rehearsed_at": now(),
                                        "rows": plan})
    print(f"{'DRY-RUN GREEN' if green else 'DRY-RUN RED'}: nothing dispatched; plan {runs_dir / 'plan.tsv'}")
    return 0 if green else 1


def report_failed(results, sections):
    return any(errs for section, errs, _ in results if section in sections)


def read_meta(run_id):
    path = META / "runs" / run_id / "meta.json"
    if not path.is_file():
        raise Refused(f"run {run_id} is not in the rehearsed plan under {META}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def fire_list(cell, block):
    check_roots()
    plan_path = META / "runs/plan.json"
    if not plan_path.is_file():
        raise Refused("no rehearsed plan; run --dry-run with the same tier first")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan["tier"] != TIER:
        raise Refused(f"the rehearsed plan is tier {plan['tier']}, not {TIER}")
    if plan.get("dry_run_green") is not True:
        raise Refused("the last dry-run was not GREEN; fix it before any dispatch")
    if cell not in [c[0] for c in HOST_CELLS] or block not in ("gate", "rest"):
        raise Refused(f"--cell must be one of {[c[0] for c in HOST_CELLS]} and --block gate or rest")
    if block == "rest" and "W1" in TIERS[TIER]:
        gate_path = META / "runs" / f"gate-{cell}.json"
        gate = json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.is_file() else {}
        if gate.get("wound") != "W1" or not isinstance(gate.get("detected"), int) or gate["detected"] < 1:
            raise Refused(f"rest block of {cell} needs a graded W1 gate with detected >= 1 in {gate_path} "
                          "(INVALID-RULES X-1)")
    status = {row["run_id"]: read_meta(row["run_id"])[1]["dispatch"]["status"] for row in plan["rows"]}
    stuck = sorted(h for h, s in status.items() if s not in ("not-dispatched", "dispatched"))
    if stuck:
        raise Refused(f"runs {stuck[:5]} are staged or setup-failed; adjudicate them before dispatching more")
    todo = [row["run_id"] for row in plan["rows"] if row["cell"] == cell and row["block"] == block
            and status[row["run_id"]] == "not-dispatched"]
    done = sum(1 for s in status.values() if s == "dispatched")
    if done + len(todo) > BUDGET[TIER]:
        raise Refused(f"budget: {done} dispatched + {len(todo)} planned > {BUDGET[TIER]}")
    print("\n".join(todo))
    return 0


def fire_stage(run_id):
    check_roots()
    meta_path, meta = read_meta(run_id)
    if meta["dispatch"]["status"] != "not-dispatched" or (META / "runs" / run_id / "report.txt").exists():
        raise Refused(f"run {run_id} was already dispatched; measured rates allow no retries")
    reg = load_registry()
    cards, _ = parse_cards()
    for key, frozen in meta["frozen"].items():
        if frozen is None:  # C0 has no wound card
            continue
        path = ROOT / frozen["path"]
        if frozen["sha256"] is None or not path.is_file() or wm.file_hash(path) != frozen["sha256"]:
            raise Refused(f"{frozen['path']} is missing or changed since the dry-run (prereg is frozen; use adjudication)")
    row = {"run_id": run_id, "order": meta["order"], "block": meta["block"], "cell": meta["host_cell"],
           "shell": meta["shell"], "model": meta["model"], "wound": meta["wound"], "run": meta["run"]}
    fresh, problems = stage_one(row, reg, cards)
    if fresh["prompt_sha256"] != meta["prompt_sha256"]:
        problems.append("rendered prompt differs from the rehearsed one (stage root or template moved)")
    if problems:
        shutil.rmtree(STAGE / run_id, ignore_errors=True)
        meta["dispatch"].update(status="setup-failed", problems=problems, finished=now())
        write_json(meta_path, meta)
        raise Refused(f"run {run_id} failed delivery checks (invalid setup, INVALID-RULES I-2): {problems}")
    meta["dispatch"].update(status="staged", started=now(), host_entry=HOST_ENTRY)
    write_json(meta_path, meta)
    return 0


def fire_archive(run_id, code):
    meta_path, meta = read_meta(run_id)
    if meta["dispatch"]["status"] != "staged":
        raise Refused(f"run {run_id} is not staged")
    sdir, mdir = STAGE / run_id, META / "runs" / run_id
    target, work = sdir / "greeting-agent", sdir / "work"
    post = wm.tree_hash(target) if target.is_dir() else None
    if work.is_dir():
        shutil.copytree(work, mdir / "work", symlinks=True, dirs_exist_ok=True)
        if (work / "card.txt").is_file():
            shutil.copy2(work / "card.txt", mdir / "card.txt")
    (mdir / "exitcode").write_text(f"{code}\n", encoding="utf-8")
    report_file = mdir / "report.txt"
    meta["dispatch"].update(status="dispatched", finished=now(), exit=int(code), post_fixture_sha256=post,
                            target_modified=post != meta["expected_fixture_sha256"],
                            report_bytes=report_file.stat().st_size if report_file.is_file() else None)
    write_json(meta_path, meta)
    shutil.rmtree(sdir, ignore_errors=True)
    print(f"archived {run_id}: exit {code}, report {meta['dispatch']['report_bytes']} bytes")
    return 0


def main(argv):
    commands = {"dry-run": dry_run, "fire-list": fire_list, "stage": fire_stage, "archive": fire_archive}
    if not argv or argv[0] not in commands:
        print(f"run_factorial: internal subcommand must be one of {sorted(commands)}", file=sys.stderr)
        return 2
    try:
        return commands[argv[0]](*argv[1:])
    except Refused as exc:
        print(f"run_factorial: refused: {exc}", file=sys.stderr)
        return 2


sys.exit(main(sys.argv[1:]))
PY
}

case "$mode" in
  dry-run)
    py dry-run
    ;;
  fire)
    [ -n "$cell" ] && [ -n "$block" ] || { echo "run_factorial: --fire needs --cell and --block" >&2; exit 2; }
    ids="$(py fire-list "$cell" "$block")"
    while read -r run_id <&3; do
      [ -n "$run_id" ] || continue
      py stage "$run_id"
      rc=0
      dispatch_host "$cell" "$META/runs/$run_id/prompt.txt" "$STAGE/$run_id/work" "$META/runs/$run_id/report.txt" || rc=$?
      py archive "$run_id" "$rc"
    done 3<<<"$ids"
    ;;
esac
