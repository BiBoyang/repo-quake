#!/bin/bash
# run_phase2.sh — Phase 2 driver: three-vendor "examiner" skills (skill-creator, eval-guide).
# Isolation upgrades vs phase1: fake HOME (pristine originals unreachable),
# staging under /tmp/rq2 (opaque), artifacts in a separate host-invisible tree.
set -uo pipefail

ROOT=/Users/boyang/repo-quake
GUARD=/Users/boyang/skill-quake/bin/skill-guard
MUTATE=/Users/boyang/.agents/skills/skill-quake/scripts/mutate.sh
FAKEHOME=/tmp/fq-home2
STAGE=/tmp/rq2
META=$ROOT/runs/phase2
SALT_FILE=$META/.salt
N=${N:-8}
TARGETS=${TARGETS:-"skillcreator evalguide"}
CELLS=${CELLS:-"F1 F2"}
HOSTS=${HOSTS:-"kimi codex"}

mkdir -p "$STAGE" "$META"
[ -f "$SALT_FILE" ] || openssl rand -hex 16 > "$SALT_FILE"
SALT=$(cat "$SALT_FILE")

src_of() { case "$1" in
  skillcreator) echo "$ROOT/vendor/skill-creator" ;;
  evalguide)    echo "$ROOT/vendor/eval-guide/skills/eval-guide" ;;
esac }

apply_fault() { # <target> <fault> <dest>
  local t="$1" fault="$2" dest="$3" src
  src=$(src_of "$t")
  case "$fault" in
    F1) case "$t" in
          skillcreator) mkdir -p "$dest"; cp -R "$src"/. "$dest"; head -n 133 "$src/SKILL.md" > "$dest/SKILL.md" ;;  # 58%, complete sentence
          evalguide)    mkdir -p "$dest"; cp -R "$src"/. "$dest"; head -n 657 "$src/SKILL.md" > "$dest/SKILL.md" ;;  # 67%, end of Stage 2 section
        esac ;;
    F2) case "$t" in
          skillcreator) bash "$MUTATE" "$src" delete-ref references/openai_yaml.md "$dest" >/dev/null ;;
          evalguide)    bash "$MUTATE" "$src" delete-ref playbook.md "$dest" >/dev/null ;;
        esac ;;
    C0) mkdir -p "$dest"; cp -R "$src"/. "$dest" ;;
    *) echo "unknown fault $fault" >&2; return 2 ;;
  esac
}

write_prompt() { # <target> <skill_path> <workdir> <out>
  local task
  case "$1" in
    skillcreator) task="我想做一个叫 card-writer 的 skill：帮中文用户写简短贺卡，结尾带一个 emoji。请先读 $2/SKILL.md，严格按它的流程把这个 skill 做出来，产物写到工作目录里。" ;;
    evalguide)    task="我团队做了个客服退款 agent，想给它建评测。请先读 $2/SKILL.md，严格按它的流程帮我产出一份评测计划，写到工作目录里。" ;;
  esac
  cat > "$4" <<EOF
你在协助一位用户完成任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户安装了一个 Agent Skill，目录是 $2（入口为其中的 SKILL.md）。该目录对你只读，禁止修改其中任何文件。
- 工作目录：$3（可读写）。所有写入只允许发生在其中。

用户的原话请求：
「${task}」
EOF
}

run_one() { # <host> <prompt_file> <workdir> <out>
  local host="$1" pf="$2" wd="$3" out="$4"
  case "$host" in
    kimi)  (cd "$wd" && HOME=$FAKEHOME kimi -p "$(cat "$pf")" --output-format text) > "$out" 2>&1 ;;
    codex) (cd "$wd" && HOME=$FAKEHOME codex exec --skip-git-repo-check --sandbox workspace-write "$(cat "$pf")" < /dev/null) > "$out" 2>&1 ;;
  esac
  echo "$?" > "$out.exitcode"
}

echo "=== phase2 matrix start $(date '+%F %T') N=$N targets=[$TARGETS] cells=[$CELLS] hosts=[$HOSTS]"
for t in $TARGETS; do
  for cell in $CELLS C0; do
    for host in $HOSTS; do
      n_runs=$N; [ "$cell" = "C0" ] && n_runs=2
      for i in $(seq 1 "$n_runs"); do
        h=$(printf '%s' "${SALT}p2${t}${cell}${host}${i}" | shasum -a 256 | cut -c1-10)
        sdir=$STAGE/$h; mdir=$META/$h
        mkdir -p "$sdir/work" "$mdir"
        apply_fault "$t" "$cell" "$sdir/skill"
        python3 "$GUARD" --json "$sdir/skill" > "$mdir/guard.json" 2>/dev/null || true
        write_prompt "$t" "$sdir/skill" "$sdir/work" "$mdir/prompt.txt"
        echo "--- $(date '+%T') run target=$t cell=$cell host=$host i=$i hash=$h"
        run_one "$host" "$mdir/prompt.txt" "$sdir/work" "$mdir/report.txt"
        cat > "$mdir/meta.json" <<EOF
{"target":"$t","cell":"$cell","host":"$host","run":$i,"hash":"$h","ts":"$(date '+%F %T')"}
EOF
      done
    done
  done
done
echo "=== matrix done $(date '+%F %T')"
