#!/usr/bin/env python3
"""Summarize a stream-retry evidence root into summary.md (Chinese), stdlib only.

  summarize.py <evidence-root>

Reads runs.jsonl / runs-noninteractive.jsonl, manifest-*.json, versions-before/after-*.json,
probes/*.json, egress.json and lsregister.json when present. Never edits them.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ORDER = ["F0-pre", "F0-tag", "F1-once", "F6-once", "FLONG-once", "F1-always", "F0-post"]
VERDICT_ORDER = ["healthy", "tag_visible", "not_shown", "retracted", "fork", "continued", "duplicate",
                 "accepted_partial", "reported_failure", "control_failed", "n/a", "invalid"]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cond_key(c: str) -> int:
    return ORDER.index(c) if c in ORDER else len(ORDER)


def fields_text(fields: dict) -> str:
    if not fields:
        return "—"
    return "、".join(f"{k}{'✓' if v else '✗'}" for k, v in fields.items())


def ms(v) -> str:
    return "—" if v is None else f"{v:+d}"


def retry_and_fault(rec: dict):
    checks = rec.get("checks") or {}
    reqs = {r["seq"]: r for r in rec.get("requests") or []}
    return reqs.get(checks.get("retry_seq")), reqs.get(checks.get("fault_seq"))


def verdict_table(rows: list[dict], mode: str) -> list[str]:
    cells = defaultdict(list)
    for r in rows:
        cells[(r["tool"], r["condition"])].append(r)
    out = [f"| 工具 | 条件 | N | 判定 | 五字段 | 带 mark 请求数（正式/辅助） |", "|---|---|---:|---|---|---|"]
    for (tool, cond) in sorted(cells, key=lambda k: (k[0], cond_key(k[1]))):
        group = cells[(tool, cond)]
        counts = Counter(r["verdict"] for r in group)
        verdicts = "，".join(f"{v} {counts[v]}/{len(group)}" for v in VERDICT_ORDER if counts.get(v))
        fset = {json.dumps(r.get("fields") or {}, sort_keys=True) for r in group}
        fields = fields_text(json.loads(fset.pop())) if len(fset) == 1 else "不一致（见逐次表）"
        mains = [sum(1 for q in r.get("requests") or [] if not q.get("aux")) for r in group]
        auxes = [sum(1 for q in r.get("requests") or [] if q.get("aux")) for r in group]
        rng = lambda xs: f"{min(xs)}–{max(xs)}" if xs and min(xs) != max(xs) else (str(xs[0]) if xs else "—")
        out.append(f"| {tool} | {cond} | {len(group)} | {verdicts} | {fields} | {rng(mains)} / {rng(auxes)} |")
    return out


def per_run_table(rows: list[dict]) -> list[str]:
    out = ["| 工具 | 条件 | 次 | 判定 | 故障流（相对重发开始，ms） | 原始字节首见标记 | 中途截图 | 标记在屏时段 | 重叠截图 | 最终画面完整 | 下一轮带半截 | 原始字节里的提示（相对 FIN，ms） |",
           "|---|---|---:|---|---|---:|---:|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: (x["tool"], cond_key(x["condition"]), x["run_index"])):
        if not r["condition"].endswith("-once"):
            continue
        retry, fault = retry_and_fault(r)
        base = retry["started_ms"] if retry else None
        rel = (lambda t: None if t is None or base is None else int(t - base))
        d = r.get("display") or {}
        raw = r.get("raw") or {}
        fault_span = f"{ms(rel(fault['started_ms']))} → {ms(rel(fault['ended_ms']))}" if fault else "—"
        mid = d.get("mid") or {}
        win = d.get("tag_visible_ms") or []
        win_text = "；".join(f"{ms(rel(a))} → {ms(rel(b)) if b else '最后'}" for a, b in win) or "—"
        ov = d.get("overlap")
        ov_text = f"{ms(rel(ov['ts_ms']))}（标记 {ov['tag_count']}，首段 ×{ov['first_partial_count']}）" if ov else "无"
        fin = fault["ended_ms"] if fault else None
        notes = "；".join(f"{n['text']}（{ms(None if n.get('t_ms') is None or fin is None else int(n['t_ms'] - fin))}）"
                          for n in raw.get("notices_timed") or []) or "无"
        nxt = r.get("next_request")
        nxt_text = "—" if not nxt else ("是" if nxt.get("carries_tag") else "否")
        out.append(f"| {r['tool']} | {r['condition']} | {r['run_index']} | {r['verdict']} | {fault_span} | "
                   f"{ms(rel(raw.get('tag_first_ms')))} | {ms(rel(mid.get('ts_ms')))} | {win_text} | {ov_text} | "
                   f"{'是' if d.get('final_complete') else '否'} | {nxt_text} | {notes} |")
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: summarize.py <evidence-root>", file=sys.stderr)
        return 2
    root = Path(argv[0])
    inter = load_jsonl(root / "runs.jsonl")
    nonint = load_jsonl(root / "runs-noninteractive.jsonl")
    lines = ["# 流中途断开、自动重发之后的显示：汇总", "",
             "由 `witness/stream-retry/summarize.py` 生成；判定规则见 `witness/stream-retry/README.md`。时间都是毫秒，相对于该次运行重发请求开始的时刻（负数在重发之前）。", ""]
    for path in sorted(root.glob("manifest-*.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        lines += [f"## 矩阵 `{m['label']}`", "",
                  f"- 时间：{m.get('started_at')} → {m.get('ended_at')}",
                  f"- 工具：{', '.join(m.get('tools', []))}；条件：{', '.join(m.get('conditions', []))}；每格 {m.get('runs')} 次；模式 {m.get('mode')}",
                  f"- tmux：{m.get('tmux')}；沙箱：{m.get('sandbox')}；静默窗口 {m.get('quiet_s')} s；稳定判据 {m.get('settle_s')} s；截屏间隔 {m.get('poll_s')} s",
                  f"- 前后版本和哈希一致：{m.get('versions_equal')}" + (f"（差异：{m.get('version_diff')}）" if m.get("version_diff") else ""),
                  f"- 装置哈希：" + "，".join(f"`{k}` {v[:16]}" for k, v in (m.get('harness_sha256') or {}).items()),
                  f"- 实验卡 sha256：{(m.get('card_sha256') or '—')[:16]}", ""]
        before = root / f"versions-before-{m['label']}.json"
        if before.exists():
            b = json.loads(before.read_text(encoding="utf-8"))
            for name, info in b["tools"].items():
                native = info.get("native") or {}
                lines.append(f"- {name}：`{info['version']}`，启动文件 sha256 {info['realpath_sha256'][:16]}，实际执行的二进制 sha256 {(native.get('sha256') or '—')[:16]}")
            lines.append("")
    if inter:
        lines += ["## 判定总表（交互模式）", ""] + verdict_table(inter, "interactive") + [""]
        executed = Counter((r["tool"], (r.get("executed") or {}).get("sha256", "—")[:16]) for r in inter)
        lines += ["运行时核对（每次运行对 tmux 面板进程做 `lsof`，看实际执行的文件）："]
        lines += [f"- {tool}：sha256 {h}，{n} 次" for (tool, h), n in sorted(executed.items())] + [""]
        lines += ["## 逐次证人（故障格）", ""] + per_run_table(inter) + [""]
        flong = [r for r in inter if r["condition"] == "FLONG-once"]
        if flong:
            lines += ["## FLONG 断开前一刻", "", "| 工具 | 次 | 断开前截图里的 L 编号（唯一） | 断开前画面完整 |", "|---|---:|---:|---|"]
            for r in sorted(flong, key=lambda x: (x["tool"], x["run_index"])):
                pf = (r.get("display") or {}).get("prefin") or {}
                lines.append(f"| {r['tool']} | {r['run_index']} | {pf.get('L_unique', '—')} | {'是' if pf.get('complete') else '否'} |")
            lines.append("")
        f0 = defaultdict(dict)
        for r in inter:
            if r["condition"] in ("F0-pre", "F0-post"):
                f0[r["tool"]].setdefault(r["condition"], []).append(r["verdict"])
        if f0:
            lines += ["## 前后 F0 对照", "", "| 工具 | F0-pre | F0-post |", "|---|---|---|"]
            for tool, d in sorted(f0.items()):
                lines.append(f"| {tool} | {', '.join(d.get('F0-pre', []))} | {', '.join(d.get('F0-post', []))} |")
            lines.append("")
        bad = [r for r in inter if r["verdict"] in ("invalid", "n/a", "control_failed")]
        lines += ["## 无效、n/a 与对照失败", ""]
        lines += [f"- {r['tool']} {r['condition']} 第 {r['run_index']} 次：{r['verdict']}，{r['verdict_reason']}" for r in bad] or ["- 无"]
        lines.append("")
    if nonint:
        lines += ["## 判定总表（非交互模式）", ""] + verdict_table(nonint, "noninteractive") + [""]
    for name, title in (("egress.json", "沙箱拦下的外连"), ("lsregister.json", "LaunchServices 登记")):
        path = root / name
        if path.exists():
            lines += [f"## {title}", "", "```json", path.read_text(encoding="utf-8").strip(), "```", ""]
    (root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {root / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
