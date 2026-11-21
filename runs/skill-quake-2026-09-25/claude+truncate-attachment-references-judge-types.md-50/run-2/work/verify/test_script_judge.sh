#!/usr/bin/env bash
# Exercise the script-judge fixture with representative card outputs.
set -uo pipefail

SCRIPT="/Users/boyang/skill-quake/results/claude+truncate-attachment-references-judge-types.md-50/run-2/work/target/evals/fixtures/scripts/check-card-structure.sh"

run_case() {
  local label="$1"
  local msg="$2"
  local expected="$3"
  local out
  out="$(EVAL_FINAL_MESSAGE="$msg" bash "$SCRIPT" 2>&1)"
  local code=$?
  if [ "$expected" = "pass" ] && [ "$code" -eq 0 ]; then
    echo "PASS(expected) $label"
  elif [ "$expected" = "fail" ] && [ "$code" -ne 0 ]; then
    echo "PASS(expected) $label -> exit=$code :: $(echo "$out" | tr '\n' ' ')"
  else
    echo "UNEXPECTED    $label -> exit=$code :: $(echo "$out" | tr '\n' ' ')"
  fi
}

run_case "valid Chinese card"          "祝你在考场上稳稳发挥，把这段时间的努力都写进答卷里🎓" pass
run_case "two emojis"                  "加油呀🎓✨" fail
run_case "emoji not at end"            "🎓祝你考试顺利！" fail
run_case "markdown bold"               "祝你**考试顺利**🎓" fail
run_case "four sentences"              "加油。我们都在。你行的。真的。🎓" fail
run_case "wrapped in quotes"           "“祝你考试顺利🎓”" fail
run_case "valid English card"          "You've got this, Maya. Your launch will be great 🌟" pass
run_case "empty message"               "" fail

# EVAL_FINAL_MESSAGE 缺失时的行为
out="$(env -u EVAL_FINAL_MESSAGE bash "$SCRIPT" 2>&1)"; code=$?
echo "missing env var -> exit=$code :: $(echo "$out" | tr '\n' ' ')"
