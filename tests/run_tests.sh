#!/bin/bash
# skill-guard fixture tests: each fixture maps to one known fault class.
set -u
cd "$(dirname "$0")/.." || exit 1
GUARD=bin/skill-guard
fails=0

check() { # name fixture expected_exit expected_substring
  local name="$1" fixture="$2" want_exit="$3" want_str="$4"
  local out rc
  out=$(python3 $GUARD "tests/fixtures/$fixture" 2>&1); rc=$?
  if [ "$rc" -ne "$want_exit" ]; then
    echo "FAIL [$name]: exit=$rc want=$want_exit"; echo "$out"; fails=$((fails+1)); return
  fi
  if [ -n "$want_str" ] && ! grep -qF "$want_str" <<<"$out"; then
    echo "FAIL [$name]: missing '$want_str'"; echo "$out"; fails=$((fails+1)); return
  fi
  echo "ok   [$name]"
}

check healthy           healthy-mini        0 "PASS"
check missing-ref       missing-ref         1 "references/gone.md"
check empty-frontmatter empty-frontmatter   1 "'name' is empty"
check empty-fm-desc     empty-frontmatter   1 "'description' is empty"
check trunc-main-warn   truncated-main      0 "ends at a heading"
check trunc-fence-warn  truncated-fence     0 "odd number of"
check strict-promotes   truncated-main      0 "PASS"   # non-strict: warning only
check cross-skill-ref   cross-skill-ref     0 "PASS  (0 error(s), 0 warning(s))"   # sibling-skill path, URL, ../ are not local refs; ./ is

out=$(python3 $GUARD tests/fixtures/truncated-main --strict 2>&1); rc=$?
if [ "$rc" -eq 1 ]; then echo "ok   [strict-fails-on-warn]"; else echo "FAIL [strict-fails-on-warn]: exit=$rc"; fails=$((fails+1)); fi

out=$(python3 $GUARD tests/fixtures/healthy-mini --json); rc=$?
if [ "$rc" -eq 0 ] && grep -q '"verdict": "PASS"' <<<"$out"; then echo "ok   [json-mode]"; else echo "FAIL [json-mode]"; echo "$out"; fails=$((fails+1)); fi

# dogfood: the gate must PASS on the repo's own two skills. Regression guard for the
# unanchored REF_RE false positive: skill-quake's mention of
# skills/repo-quake/scripts/validate_card.py was read as a local scripts/ reference
# and failed the gate unnoticed from e926ee7 (2026-10-25) until 2026-10-31, because
# only fixtures were ever guarded here.
for s in skills/repo-quake skills/skill-quake; do
  out=$(python3 $GUARD "$s" 2>&1); rc=$?
  if [ "$rc" -eq 0 ] && grep -qF "0 error(s)" <<<"$out"; then echo "ok   [dogfood-$(basename "$s")]"; else echo "FAIL [dogfood-$(basename "$s")]: exit=$rc"; echo "$out"; fails=$((fails+1)); fi
done

# suspicion.py: reread_any tripwire (trace-level signal, never a detection level)
SUS=skills/skill-quake/scripts/suspicion.py
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

printf '%s' '[{"name":"read","arguments":{"path":"/a/SKILL.md"}},{"name":"read","arguments":{"path":"/a/refs.md"}},{"name":"read","arguments":{"path":"/a/SKILL.md"}}]' > "$tmp/reread.json"
out=$(python3 $SUS --trace "$tmp/reread.json"); rc=$?
if [ "$rc" -eq 0 ] && grep -q '"reread_any": true' <<<"$out"; then echo "ok   [suspicion-reread-flagged]"; else echo "FAIL [suspicion-reread-flagged]"; echo "$out"; fails=$((fails+1)); fi

printf '%s' '[{"name":"read","arguments":{"path":"/a/SKILL.md"}},{"name":"read","arguments":{"path":"/a/refs.md"}},{"name":"read","arguments":{"path":"/a/tmpl"}}]' > "$tmp/clean.json"
out=$(python3 $SUS --trace "$tmp/clean.json"); rc=$?
if [ "$rc" -eq 0 ] && grep -q '"reread_any": false' <<<"$out"; then echo "ok   [suspicion-clean-passes]"; else echo "FAIL [suspicion-clean-passes]"; echo "$out"; fails=$((fails+1)); fi

printf '%s\n' \
  '{"type":"message_end","message":{"role":"assistant","content":[{"type":"toolCall","name":"read","arguments":{"path":"/a/SKILL.md"}}]}}' \
  '{"type":"message_end","message":{"role":"user","content":"ignored"}}' \
  '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"no tools here"}]}}' \
  '{"type":"message_end","message":{"role":"assistant","content":[{"type":"toolCall","name":"read","arguments":{"path":"/a/SKILL.md"}}]}}' > "$tmp/pi.jsonl"
out=$(python3 $SUS --pi-jsonl "$tmp/pi.jsonl"); rc=$?
if [ "$rc" -eq 0 ] && grep -q '"reads_total": 2' <<<"$out" && grep -q '"reread_any": true' <<<"$out"; then
  echo "ok   [suspicion-pi-jsonl-extract]"
else
  echo "FAIL [suspicion-pi-jsonl-extract]"; echo "$out"; fails=$((fails+1))
fi

mkdir -p "$tmp/results/ghost+re-read/run-1" "$tmp/results/ghost+healthy/run-1"
cp "$tmp/reread.json" "$tmp/results/ghost+re-read/run-1/trace.json"
printf '%s' '{"level":"L2","detected":true}' > "$tmp/results/ghost+re-read/run-1/grade.json"
cp "$tmp/clean.json" "$tmp/results/ghost+healthy/run-1/trace.json"
printf '%s' '{"level":"L0","detected":false}' > "$tmp/results/ghost+healthy/run-1/grade.json"
out=$(python3 $SUS --results "$tmp/results")
if grep -q 'TP=1 FP=0 TN=1 FN=0' <<<"$out"; then echo "ok   [suspicion-results-confusion]"; else echo "FAIL [suspicion-results-confusion]"; echo "$out"; fails=$((fails+1)); fi

if ! python3 -m unittest discover -s tests -p 'test_*.py'; then
  fails=$((fails+1))
fi

# ledger-check: the fault ledger must validate against the live repo tree
# (ids, enums, detected<=runs, levels==runs, evidence paths exist). Unit tests
# for the checker itself live in tests/test_ledger_check.py (discovered above).
out=$(python3 bin/ledger-check ledger/ledger.json 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then echo "ok   [ledger-check]"; else echo "FAIL [ledger-check]: exit=$rc"; echo "$out"; fails=$((fails+1)); fi

# factorial materials (phase3, witness/factorial/): the dry-run is the pre-fire
# gate (material tree, recomputable hash registry, card field checks, witness
# baseline, frozen prereg, no-host-call audit) and never dispatches a host.
# Unit tests for the driver live in tests/test_factorial_materials.py (above).
out=$(RQ_FACTORIAL_META="$tmp/fm" RQ_FACTORIAL_STAGE="$tmp/fs" bash witness/factorial/run_factorial.sh --dry-run 2>&1); rc=$?
if [ "$rc" -eq 0 ] && grep -q "DRY-RUN GREEN" <<<"$out"; then echo "ok   [factorial-dry-run]"; else echo "FAIL [factorial-dry-run]: exit=$rc"; echo "$out"; fails=$((fails+1)); fi

echo "---"
if [ "$fails" -eq 0 ]; then
  echo "ALL TESTS PASSED"
else
  echo "$fails TEST(S) FAILED"
  exit 1
fi
