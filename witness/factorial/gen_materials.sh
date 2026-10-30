#!/bin/bash
# gen_materials.sh — phase3 factorial materials for repo-quake.
# Builds one mutated copy per wound card (C0 + W1..W5) of the healthy
# targets/greeting-agent inside a host-invisible meta tree under a pure-hash
# /tmp path (X-003, X-005), reads both witnesses on every copy and on the
# healthy source, and writes a recomputable hash registry (registry.json).
# The source under targets/ is only read; its tree hash is compared before and
# after. Zero host calls: no host CLI, no network.
#
# Usage: gen_materials.sh [--meta DIR]
#   --meta DIR   meta root (default: $RQ_FACTORIAL_META, else /tmp/<12 hex>)
#   RQ_FACTORIAL_SALT pins the salt (tests); otherwise <meta>/.salt is created once.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/targets/greeting-agent"
VARIANTS="C0 W1 W2 W3 W4 W5"

meta="${RQ_FACTORIAL_META:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --meta) meta="${2:-}"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "gen_materials: unknown argument '$1'" >&2; exit 2 ;;
  esac
  shift
done
if [ -z "$meta" ]; then
  meta="/tmp/$(printf 'repo-quake:factorial:meta:%s' "$ROOT" | shasum -a 256 | cut -c1-12)"
fi

realpath_of() { python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }
meta="$(realpath_of "$meta")"
case "$meta/" in
  "$(realpath_of "$ROOT")/"*)
    echo "gen_materials: meta root $meta is inside the repo; materials never go into the repo (targets/ stays pristine)" >&2
    exit 2 ;;
esac
[ -f "$SRC/agent/instructions.md" ] || { echo "gen_materials: healthy target missing: $SRC" >&2; exit 2; }

tree_of() { # <dir> — same tree hash as per-run meta (write_meta.tree_hash)
  python3 -B -c 'import importlib.util, sys
spec = importlib.util.spec_from_file_location("rq_write_meta", sys.argv[1])
wm = importlib.util.module_from_spec(spec); spec.loader.exec_module(wm)
print(wm.tree_hash(sys.argv[2]))' "$ROOT/skills/skill-quake/scripts/write_meta.py" "$1"
}

mkdir -p "$meta"
if [ -n "${RQ_FACTORIAL_SALT:-}" ]; then
  printf '%s\n' "$RQ_FACTORIAL_SALT" > "$meta/.salt"
elif [ ! -s "$meta/.salt" ]; then
  python3 -c 'import secrets; print(secrets.token_hex(16))' > "$meta/.salt"
fi
salt="$(head -n 1 "$meta/.salt")"
vhash() { printf '%s:variant:%s' "$salt" "$1" | shasum -a 256 | cut -c1-12; }

cut_head() { # <file> <keep_lines> — tail truncation in place (keeps inode and mode)
  local tmp
  tmp="$(mktemp)"
  head -n "$2" "$1" > "$tmp"
  cat "$tmp" > "$1"
  rm -f "$tmp"
}

# The wound table. One branch per card in witness/factorial/cards/; W1, W2 and
# W4 reproduce phase1 E2, E1 and E3 byte for byte (witness/run_matrix.sh).
apply_wound() { # <variant> <copy_root>
  local a="$2/agent"
  case "$1" in
    C0) : ;;                                        # negative control: untouched copy
    W1) rm "$a/skills/tone-guide/SKILL.md" ;;       # blocks-path, positive control (= E2)
    W2) cut_head "$a/instructions.md" 12 ;;         # redundant-backstop (= E1)
    W3) cut_head "$a/tools/get_occasion.ts" 12 ;;   # future-use
    W4) cut_head "$a/tools/render_card.ts" 12 ;;    # weak-reference (= E3)
    W5) cut_head "$a/skills/tone-guide/SKILL.md" 23 ;;  # on-path-no-gap
    *) echo "gen_materials: unknown variant '$1'" >&2; return 2 ;;
  esac
}

read_witnesses() { # <agent_project_root> <out_dir> — FAIL is data; only a missing verdict is a crash
  local rc=0
  python3 -B "$ROOT/witness/eve_guard.py" "$1" --json > "$2/eve_guard.json" || rc=$?
  echo "$rc" > "$2/eve_guard.exit"
  rc=0
  python3 -B "$ROOT/bin/skill-guard" --json "$1/agent/skills/tone-guide" > "$2/skill_guard.json" || rc=$?
  echo "$rc" > "$2/skill_guard.exit"
  for w in eve_guard skill_guard; do
    if ! grep -q '"verdict"' "$2/$w.json"; then
      echo "gen_materials: witness $w crashed on $1 (no verdict in $2/$w.json)" >&2
      exit 2
    fi
  done
}

source_before="$(tree_of "$SRC")"
rm -rf "$meta/variants" "$meta/baseline"
mkdir -p "$meta/variants" "$meta/baseline"
read_witnesses "$SRC" "$meta/baseline"
for v in $VARIANTS; do
  vdir="$meta/variants/$(vhash "$v")"
  mkdir -p "$vdir"
  cp -R "$SRC" "$vdir/greeting-agent"
  apply_wound "$v" "$vdir/greeting-agent"
  read_witnesses "$vdir/greeting-agent" "$vdir"
done
source_after="$(tree_of "$SRC")"
if [ "$source_before" != "$source_after" ]; then
  echo "gen_materials: healthy source changed during generation ($source_before -> $source_after)" >&2
  exit 2
fi

python3 -B - "$ROOT" "$meta" "$salt" $VARIANTS <<'PY'
import datetime
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

root, meta, salt = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
variants = sys.argv[4:]
spec = importlib.util.spec_from_file_location("rq_write_meta", root / "skills/skill-quake/scripts/write_meta.py")
wm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wm)
SOURCE_REL = "targets/greeting-agent"
TOOLS = ("witness/factorial/gen_materials.sh", "witness/eve_guard.py", "bin/skill-guard",
         "skills/skill-quake/scripts/write_meta.py")
CALIBRATION = (
    "skill-guard has a known false-positive class (RQ-I-001: example paths in prose are taken as real "
    "references). The healthy tone-guide contains no references/, assets/ or scripts/ paths, so that class "
    "cannot fire here; the baseline reads PASS 0 err 0 warn and every variant verdict is a delta from a clean "
    "baseline. eve_guard's healthy baseline is PASS with zero warnings (phase0). Both witnesses are blind to "
    "complete-sentence and section-boundary cuts by design (W2, W5)."
)


def files_of(tree):
    out = {}
    for current, dirs, files in os.walk(tree):
        dirs.sort()
        for name in sorted(files):
            path = Path(current) / name
            out[path.relative_to(tree).as_posix()] = wm.file_hash(path)
    return out


def lines_of(tree, rels):
    return {rel: (tree / rel).read_bytes().count(b"\n") for rel in rels}


def reading(out_dir, prefix):
    raw = {}
    for name in ("eve_guard", "skill_guard"):
        raw[name] = json.loads((out_dir / f"{name}.json").read_text(encoding="utf-8"))
    eve, sg = raw["eve_guard"], raw["skill_guard"]
    eve_errors = sorted({e["id"] for e in eve["errors"]})
    eve_warnings = sorted({w["id"] for w in eve["warnings"]})
    eve_summary = " ".join([eve["verdict"], *eve_errors] + (["warn", *eve_warnings] if eve_warnings else []))
    sg_summary = sg["verdict"] + (f" warn {len(sg['warnings'])}" if sg["warnings"] else "")
    strip = lambda msg: msg.replace(prefix + "/", "").replace(prefix, "<project>")
    return {
        "eve_guard": {
            "exit": int((out_dir / "eve_guard.exit").read_text().strip()),
            "verdict": eve["verdict"], "errors": eve_errors, "warnings": eve_warnings,
            "summary": eve_summary, "raw_sha256": wm.file_hash(out_dir / "eve_guard.json"),
        },
        "skill_guard": {
            "exit": int((out_dir / "skill_guard.exit").read_text().strip()),
            "verdict": sg["verdict"], "errors": len(sg["errors"]), "warnings": len(sg["warnings"]),
            "messages": [strip(m) for m in sg["errors"] + sg["warnings"]],
            "summary": sg_summary, "raw_sha256": wm.file_hash(out_dir / "skill_guard.json"),
        },
    }


def delta(src_tree, src_files, var_tree, var_files):
    out = []
    for rel in sorted(set(src_files) | set(var_files)):
        before, after = src_files.get(rel), var_files.get(rel)
        if before == after:
            continue
        item = {"path": rel}
        if after is None:
            item.update(change="deleted", lines_before=(src_tree / rel).read_bytes().count(b"\n"), lines_after=0)
        elif before is None:
            item.update(change="added")
        else:
            a, b = (src_tree / rel).read_bytes(), (var_tree / rel).read_bytes()
            item.update(change="truncated" if a.startswith(b) else "modified",
                        lines_before=a.count(b"\n"), lines_after=b.count(b"\n"),
                        bytes_before=len(a), bytes_after=len(b), prefix_preserved=a.startswith(b))
        out.append(item)
    return out


src = root / SOURCE_REL
src_files = files_of(src)
registry = {
    "schema": "repo-quake/factorial-registry/v1",
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "hash_scheme": ("tree_sha256 = skills/skill-quake/scripts/write_meta.py tree_hash: sha256 over the sorted JSON "
                    "list of [kind, relpath, sha256] entries, directories included; files = per-file sha256"),
    "tools": {rel: wm.file_hash(root / rel) for rel in TOOLS},
    "source": {
        "path": SOURCE_REL, "tree_sha256": wm.tree_hash(src), "files": src_files,
        "lines": lines_of(src, src_files), "witness": reading(meta / "baseline", str(src)),
        "calibration": CALIBRATION,
    },
    "variants": {},
}
for v in variants:
    vh = hashlib.sha256(f"{salt}:variant:{v}".encode()).hexdigest()[:12]
    tree = meta / "variants" / vh / "greeting-agent"
    var_files = files_of(tree)
    registry["variants"][v] = {
        "vhash": vh, "dir": f"variants/{vh}/greeting-agent", "tree_sha256": wm.tree_hash(tree),
        "files": var_files, "delta": delta(src, src_files, tree, var_files),
        "witness": reading(meta / "variants" / vh, str(tree)),
    }
(meta / "registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"gen_materials: source {SOURCE_REL} tree {registry['source']['tree_sha256'][:16]}… "
      f"eve_guard {registry['source']['witness']['eve_guard']['summary']} / "
      f"skill-guard {registry['source']['witness']['skill_guard']['summary']} (healthy baseline)")
for v, item in registry["variants"].items():
    change = "; ".join(
        f"{d['path']} {d['change']}" + (f" {d['lines_after']}/{d['lines_before']}" if "lines_before" in d else "")
        for d in item["delta"]) or "untouched"
    print(f"  {v}  tree {item['tree_sha256'][:16]}…  eve_guard {item['witness']['eve_guard']['summary']:<8} "
          f"skill-guard {item['witness']['skill_guard']['summary']:<5} {change}")
print(f"gen_materials: registry {meta / 'registry.json'}")
PY
