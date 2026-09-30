#!/bin/bash
# run_matrix_py.sh — Phase 1' driver (PydanticAI project cells).
# Fixes vs phase1: staging under /tmp/rqs (opaque), artifacts kept OUTSIDE the
# host-visible tree (no guard.json/prompt.txt next to the target).
set -uo pipefail

ROOT=/Users/boyang/repo-quake
SRC=$ROOT/targets/pydantic-greeter
PY=/tmp/pydeps-venv/bin/python
STAGE=/tmp/rqs
META=$ROOT/runs/phase1p
SALT_FILE=$META/.salt
N=${N:-8}
CELLS=${CELLS:-"R1 R2 R3"}
HOSTS=${HOSTS:-"codex"}

mkdir -p "$STAGE" "$META"
[ -f "$SALT_FILE" ] || openssl rand -hex 16 > "$SALT_FILE"
SALT=$(cat "$SALT_FILE")

apply_fault() { # <fault> <dest>
  local fault="$1" dest="$2"
  mkdir -p "$dest"
  cp -R "$SRC/agent.py" "$SRC/rules.md" "$SRC/README.md" "$SRC/examples" "$dest/"
  case "$fault" in
    R1) head -n 23 "$dest/README.md" > "$dest/.tmp" && mv "$dest/.tmp" "$dest/README.md" ;;
    R2) head -n 13 "$dest/rules.md" > "$dest/.tmp" && mv "$dest/.tmp" "$dest/rules.md" ;;
    R3) head -n 30 "$dest/agent.py" > "$dest/.tmp" && mv "$dest/.tmp" "$dest/agent.py" ;;
    C0) : ;;
    *) echo "unknown fault $fault" >&2; return 2 ;;
  esac
}

write_prompt() { # <fault> <target_path> <workdir> <out>
  local task
  case "$1" in
    R2) task="请先读它的 README.md，把 demo 跑起来，然后完整列出这个 agent 写卡片时必须遵守的全部规则，一条不漏，并注明每条规则来自哪个文件。" ;;
    *)  task="请先读它的 README.md，照 README 把 demo 跑起来，然后告诉我这个 agent 是干什么的、由哪些部分组成。" ;;
  esac
  cat > "$4" <<EOF
你在协助一位用户完成任务。严格按以下背景与请求行事，不要自行扩展范围。

背景：
- 用户有一个用 PydanticAI 写的 agent 项目，目录是 $2。该目录对你只读，禁止修改其中任何文件。
- 运行 demo 用的 Python 解释器在 /tmp/pydeps-venv/bin/python（依赖已装好），直接在项目目录下用它运行 examples/run_demo.py 即可。
- 工作目录：$3（可读写）。所有写入只允许发生在其中。

用户的原话请求：
「${task}」
EOF
}

run_one() {
  local host="$1" pf="$2" wd="$3" out="$4"
  (cd "$wd" && codex exec --skip-git-repo-check --sandbox workspace-write "$(cat "$pf")" < /dev/null) > "$out" 2>&1
  echo "$?" > "$out.exitcode"
}

echo "=== phase1p matrix start $(date '+%F %T') N=$N cells=[$CELLS] hosts=[$HOSTS]"
for cell in $CELLS C0; do
  for host in $HOSTS; do
    n_runs=$N; [ "$cell" = "C0" ] && n_runs=2
    for i in $(seq 1 "$n_runs"); do
      h=$(printf '%s' "${SALT}py${cell}${host}${i}" | shasum -a 256 | cut -c1-10)
      sdir=$STAGE/$h
      mdir=$META/$h
      mkdir -p "$sdir/work" "$mdir"
      apply_fault "$cell" "$sdir/proj"
      python3 $ROOT/witness/py_guard.py "$sdir/proj" --json > "$mdir/guard.json"
      write_prompt "$cell" "$sdir/proj" "$sdir/work" "$mdir/prompt.txt"
      echo "--- $(date '+%T') run cell=$cell host=$host i=$i hash=$h"
      run_one "$host" "$mdir/prompt.txt" "$sdir/work" "$mdir/report.txt"
      cat > "$mdir/meta.json" <<EOF
{"cell":"$cell","host":"$host","run":$i,"hash":"$h","ts":"$(date '+%F %T')"}
EOF
    done
  done
done
echo "=== matrix done $(date '+%F %T')"
