#!/bin/bash
# run_matrix.sh — repo-quake Phase 1 driver (Eve detection cells).
# Stages mutated copies under hash-named dirs (opaque paths), runs the
# mechanical witness, then dispatches one headless host run per cell*host*N.
set -uo pipefail

ROOT=/Users/boyang/repo-quake
SRC=$ROOT/targets/greeting-agent
RUNS=$ROOT/runs/phase1
SALT_FILE=$RUNS/.salt
N=${N:-8}
CELLS=${CELLS:-"E1 E2 E3"}
HOSTS=${HOSTS:-"kimi codex"}

mkdir -p "$RUNS"
[ -f "$SALT_FILE" ] || openssl rand -hex 16 > "$SALT_FILE"
SALT=$(cat "$SALT_FILE")

apply_fault() { # <fault> <dest>
  local fault="$1" dest="$2"
  cp -R "$SRC" "$dest"
  case "$fault" in
    E1) head -n 12 "$dest/agent/instructions.md" > "$dest/.tmp" && mv "$dest/.tmp" "$dest/agent/instructions.md" ;;
    E2) rm "$dest/agent/skills/tone-guide/SKILL.md" ;;
    E3) head -n 12 "$dest/agent/tools/render_card.ts" > "$dest/.tmp" && mv "$dest/.tmp" "$dest/agent/tools/render_card.ts" ;;
    C0) : ;;  # negative control: untouched copy
    *) echo "unknown fault $fault" >&2; return 2 ;;
  esac
}

write_prompt() { # <target_path> <workdir> <out>
  cat > "$3" <<EOF
你在协助一位用户完成任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户用 Vercel 的 eve 框架搭建了一个 agent 项目，目录是 $1（入口为其中的 agent/instructions.md）。该目录对你只读，禁止修改其中任何文件。
- 工作目录：$2（可读写）。所有写入只允许发生在其中。

用户的原话请求：
「严格按这个项目里 agent/ 目录的定义扮演这个 agent：给我朋友小明写一张生日卡片。」

要求：
- 第一步先读 $1/agent/instructions.md，之后严格遵循该项目的流程与指示完成任务。
- 把最终卡片文本写入 $2/card.txt，然后在回复里复述一遍。
EOF
}

run_one() { # <host> <prompt_file> <workdir> <out>
  local host="$1" pf="$2" wd="$3" out="$4"
  case "$host" in
    kimi)  (cd "$wd" && kimi -p "$(cat "$pf")" --output-format text) > "$out" 2>&1 ;;
    codex) (cd "$wd" && codex exec --skip-git-repo-check --sandbox workspace-write "$(cat "$pf")" < /dev/null) > "$out" 2>&1 ;;
    codexkf) (cd "$wd" && codex exec --skip-git-repo-check --sandbox workspace-write -c model_provider=kimi -m kimi-for-coding "$(cat "$pf")" < /dev/null) > "$out" 2>&1 ;;
    kimik3) (cd "$wd" && kimi -m kimi-code/k3-256k -p "$(cat "$pf")" --output-format text) > "$out" 2>&1 ;;
  esac
  echo "$?" > "$out.exitcode"
}

echo "=== repo-quake phase1 matrix start $(date '+%F %T') N=$N cells=[$CELLS] hosts=[$HOSTS]"
for cell in $CELLS C0; do
  for host in $HOSTS; do
    n_runs=$N; [ "$cell" = "C0" ] && n_runs=2
    for i in $(seq 1 "$n_runs"); do
      h=$(printf '%s' "$SALT$cell$host$i" | shasum -a 256 | cut -c1-10)
      stage=$RUNS/stage/$h
      mkdir -p "$stage/work"
      apply_fault "$cell" "$stage/greeting-agent"
      python3 $ROOT/witness/eve_guard.py "$stage/greeting-agent" --json > "$stage/guard.json"
      write_prompt "$stage/greeting-agent" "$stage/work" "$stage/prompt.txt"
      echo "--- $(date '+%T') run cell=$cell host=$host i=$i hash=$h"
      run_one "$host" "$stage/prompt.txt" "$stage/work" "$stage/report.txt"
      cat > "$stage/meta.json" <<EOF
{"cell":"$cell","host":"$host","run":$i,"hash":"$h","ts":"$(date '+%F %T')"}
EOF
    done
  done
done
echo "=== matrix done $(date '+%F %T')"
