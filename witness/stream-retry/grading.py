"""Pure grading logic for stream-retry display experiments (stdlib only).

Everything here is a function of an observation bundle; nothing reads the network or
drives a terminal. The runner builds the bundle, the tests build adversarial bundles,
and `load_observation()` rebuilds one from an evidence directory, reading the mid
capture and the final capture from their own files (the 2026-11-14 regrade passed the
final screen in as the mid screen; that cannot happen here).

Verdict labels are grading notes, not a ledger vocabulary: each maps onto the five
observation fields (detected / reported / contained / recovered / reverified) exactly
as in skills/repo-quake/references/fault-catalog.md §stream "Recording retry-display
outcomes".
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONTENT = HERE / "content.json"

MARKER_RE = re.compile(r"【(P\d{2}|L\d{3}|Q\d{2}|ACK)】")
TAG_RE = re.compile(r"〔x[0-9a-f]{6}〕")
NOTICE_RE = re.compile(
    r"(?i)retry|retrying|reconnect|重试|重连|error|错误|interrupted|disconnected|"
    r"unexpected eof|terminated|timed out|timeout|failed"
)
MIN_QUIET_S = 40  # measured max gap between attempts was 33-40 s (2026-11-14)

ALT_ON = (b"\x1b[?1049h", b"\x1b[?1047h", b"\x1b[?47h")
ALT_OFF = (b"\x1b[?1049l", b"\x1b[?1047l", b"\x1b[?47l")

# Escape sequences. Cursor moves and erases become line breaks, so separate screen
# writes do not glue into one "line"; everything else is dropped.
_ESC_RE = re.compile(
    rb"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"        # OSC ... BEL | ST
    rb"|\x1b[P^_X][^\x1b]*\x1b\\"                # DCS / PM / APC / SOS ... ST
    rb"|\x1b\[[0-?]*[ -/]*[@-~]"                 # CSI
    rb"|\x1b[ -/]+[0-~]"                         # nF (charset designation)
    rb"|\x1b[^\[\]P^_X]"                         # two-byte escapes
)
_BREAKING_CSI = set(b"ABCDEFGHJKdfr")

FIELDS = {
    "healthy": {},
    "tag_visible": {},
    "not_shown": {"detected": True, "contained": True, "recovered": True},
    "retracted": {"detected": True, "contained": True, "recovered": True},
    "fork": {"detected": True, "recovered": True, "contained": False, "reported": False},
    "continued": {"detected": True, "recovered": True, "contained": True},
    "duplicate": {"detected": True, "recovered": True, "contained": False},
    "accepted_partial": {"detected": False, "reported": False},
    "reported_failure": {"detected": True, "reported": True, "recovered": False},
}
VERDICTS = set(FIELDS) | {"control_failed", "n/a", "invalid"}


class Content:
    """The shared content fixture (content.json) as marker sets and a text corpus."""

    def __init__(self, path: Path | str = DEFAULT_CONTENT):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.data = data
        self.short = data["short"]
        self.long = data["long"]
        self.short_partial = int(data["short_partial"])
        self.long_partial = int(data["long_partial"])
        paragraphs = data["short"] + data["long"] + data["reasoning"] + data["ack"] + [data["aux_title"]]
        self.corpus = compact("".join(paragraphs))

    def _paras(self, profile: str) -> list[str]:
        if profile == "long":
            return self.long
        if profile == "short":
            return self.short
        raise ValueError(f"unknown profile {profile!r}")

    def full_markers(self, profile: str) -> list[str]:
        return [MARKER_RE.search(p).group(1) for p in self._paras(profile)]

    def partial_markers(self, profile: str) -> list[str]:
        n = self.long_partial if profile == "long" else self.short_partial
        return self.full_markers(profile)[:n]

    def last_marker(self, profile: str) -> str:
        return self.full_markers(profile)[-1]


# ---------------- text helpers ----------------
def compact(text: str | None) -> str:
    """Drop all whitespace; terminal wrapping splits markers across lines."""
    return re.sub(r"\s+", "", text or "")


def counts(text: str | None) -> dict[str, int]:
    return dict(Counter(MARKER_RE.findall(compact(text))))


def tag_count(text: str | None, tag: str | None) -> int:
    if not tag:
        return 0
    return compact(text).count(tag)


def strip_ansi(data: bytes | str) -> str:
    """Terminal byte stream -> plain text; cursor moves and erases become newlines."""
    if isinstance(data, str):
        data = data.encode("utf-8", "replace")

    def repl(match: re.Match) -> bytes:
        seq = match.group(0)
        if seq.startswith(b"\x1b[") and seq[-1] in _BREAKING_CSI:
            return b"\n"
        return b""

    data = _ESC_RE.sub(repl, data)
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    data = bytes(b for b in data if b >= 0x20 or b in (0x0A, 0x09))
    return data.decode("utf-8", "replace")


def is_content_line(line: str, content: Content) -> bool:
    c = compact(line)
    if not c:
        return True
    if MARKER_RE.search(c) or TAG_RE.search(c):
        return True
    return c in content.corpus


def notices(text: str | None, content: Content) -> list[str]:
    """Lines matching the notice vocabulary that are not model content, de-duplicated."""
    seen, out = set(), []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or not NOTICE_RE.search(s) or is_content_line(s, content):
            continue
        s = s[:200]
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def time_at(index: list[dict] | None, offset: int | None) -> int | None:
    """Wall-clock ms at which raw byte `offset` reached the terminal (rawtap index)."""
    if not index or offset is None or offset < 0:
        return None
    for item in index:
        if item["offset"] <= offset < item["offset"] + item["len"]:
            return item["t_ms"]
    return None


def first_seen_ms(raw: bytes, index: list[dict] | None, needle: str) -> int | None:
    """Earliest rawtap chunk time at which `needle` (compact form) is present in the
    stripped prefix of the byte stream. Works when a TUI writes a word cell by cell
    with cursor moves in between (the needle is never contiguous in the raw bytes)."""
    if not index or not needle or needle not in compact(strip_ansi(raw)):
        return None
    lo, hi, found = 0, len(index) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        end = index[mid]["offset"] + index[mid]["len"]
        if needle in compact(strip_ansi(raw[:end])):
            found, hi = index[mid]["t_ms"], mid - 1
        else:
            lo = mid + 1
    return found


def raw_analysis(raw: bytes, tag: str | None, content: Content, index: list[dict] | None = None,
                 needles: dict[str, str] | None = None) -> dict:
    """Byte-level witness: alternate screen, clears, the failed-attempt tag, notices,
    and (with a rawtap index) when each of them first reached the terminal."""
    text = strip_ansi(raw)
    flat = compact(text)
    tag_seen = bool(tag) and tag in flat
    notice_list = notices(text, content)
    alt_offsets = [raw.find(s) for s in ALT_ON if s in raw]
    return {
        "available": len(raw) > 0,
        "bytes": len(raw),
        "indexed": bool(index),
        "alt_screen_on": alt_offsets,
        "alt_screen_on_count": sum(raw.count(s) for s in ALT_ON),
        "alt_screen_off_count": sum(raw.count(s) for s in ALT_OFF),
        "alt_screen_on_ms": time_at(index, min(alt_offsets)) if alt_offsets else None,
        "esc_2J": raw.count(b"\x1b[2J"),
        "esc_3J": raw.count(b"\x1b[3J"),
        "tag_seen": tag_seen,
        "tag_contiguous": bool(tag) and tag.encode("utf-8") in raw,
        "tag_first_ms": first_seen_ms(raw, index, tag) if tag_seen else None,
        "notices": notice_list,
        "notices_timed": [{"text": n, "t_ms": first_seen_ms(raw, index, compact(n))} for n in notice_list],
        "first_seen_ms": {name: first_seen_ms(raw, index, needle) for name, needle in (needles or {}).items()},
    }


def load_index(path: Path | str) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def no_retry_due(fault_seen: bool, healthy_retry: bool, last_request_change: float,
                 last_output_change: float, now: float, quiet_s: float) -> bool:
    """True when a fault was delivered, no healthy retry followed, and both the request
    log and the display have been quiet for `quiet_s` seconds."""
    if quiet_s < MIN_QUIET_S:
        raise ValueError(f"quiet window {quiet_s}s is shorter than the measured max retry gap ({MIN_QUIET_S}s)")
    return (fault_seen and not healthy_retry
            and now - last_request_change >= quiet_s and now - last_output_change >= quiet_s)


# ---------------- grading ----------------
def _result(verdict: str, reason: str, checks: dict, notice_final: list, notice_raw: list) -> dict:
    fields = dict(FIELDS.get(verdict, {}))
    if verdict == "fork" and notice_final:
        fields["reported"] = True
    return {"verdict": verdict, "reason": reason, "fields": fields, "checks": checks,
            "notices_final": notice_final, "notices_raw": notice_raw}


def _terminal_ok(req: dict) -> bool:
    return req.get("ending") == "clean" and any((req.get("witnesses") or {}).values())


def split_condition(condition: str) -> tuple[str, str]:
    fault, _, kind = condition.partition("-")
    if not kind:
        raise ValueError(f"condition must look like F1-once: {condition!r}")
    return fault, kind


def grade(obs: dict, content: Content) -> dict:
    """Grade one run. See README §判定 for the decision table this implements."""
    condition = obs["condition"]
    fault, kind = split_condition(condition)
    interactive = obs.get("mode", "interactive") == "interactive"
    profile = obs.get("profile") or ("long" if fault == "FLONG" else "short")
    full = content.full_markers(profile)
    partial = content.partial_markers(profile)
    tag = obs.get("tag")
    final = obs.get("final") or {}
    final_text = final.get("text") or ""
    complete = final.get("complete")
    mid = obs.get("mid")
    raw = obs.get("raw") or {}
    fc = counts(final_text)
    tag_final = tag_count(final_text, tag)
    notice_final = notices(final_text + "\n" + (obs.get("stderr") or ""), content)
    notice_raw = list(raw.get("notices") or []) if interactive else []
    reqs = sorted(obs.get("requests") or [], key=lambda r: r["seq"])
    main = [r for r in reqs if not r.get("aux")]
    main_stream = [r for r in main if r.get("stream", True)]
    full_once = all(fc.get(m, 0) == 1 for m in full)
    full_present = all(fc.get(m, 0) >= 1 for m in full)
    duplicated = any(fc.get(m, 0) > 1 for m in full)
    foreign = sorted(m for m in fc if m not in full and m != "ACK")
    checks = {
        "profile": profile, "requests": len(reqs), "main_requests": len(main),
        "main_stream_requests": len(main_stream), "final_full_once": full_once,
        "final_full_present": full_present, "final_duplicated": duplicated,
        "final_foreign_markers": foreign[:10], "final_tag_count": tag_final,
        "final_complete": complete,
    }

    def out(verdict: str, reason: str) -> dict:
        return _result(verdict, reason, checks, notice_final, notice_raw)

    if obs.get("invalid"):
        return out("invalid", str(obs["invalid"]))

    # ---- healthy controls (negative: F0-pre/F0-post; positive: F0-tag) ----
    if fault == "F0":
        problems = []
        if not main_stream:
            problems.append("no marked main streaming request reached the mock")
        if any(r.get("fault") != "F0" for r in reqs):
            problems.append("a marked request was served a fault")
        if len(main) != 1:
            problems.append(f"expected exactly one main request, saw {len(main)}")
        if main_stream and not _terminal_ok(main_stream[0]):
            problems.append("the main request did not end cleanly with its terminal witness")
        if not full_present or duplicated:
            problems.append("final display does not read the full answer exactly once" if full_present else "final display lacks part of the full answer")
        if foreign:
            problems.append(f"foreign markers on the final display: {foreign[:5]}")
        if interactive and complete is not True:
            problems.append("final screen not proven complete (banner or prompt missing)")
        if notice_final or notice_raw:
            problems.append("an error/retry notice appeared in a healthy run")
        if not interactive and obs.get("exit_code") not in (0, None):
            problems.append(f"non-zero exit code {obs.get('exit_code')}")
        if kind == "tag":
            want = len(partial)
            if tag_final != want:
                problems.append(f"positive control: tag visible {tag_final}x on the final display, expected {want}")
            if interactive and not raw.get("tag_seen"):
                problems.append("positive control: tag absent from the raw byte stream")
            if interactive and not (mid and mid.get("trigger") == "tag" and tag_count(mid.get("text"), tag) > 0):
                problems.append("positive control: no tag-triggered mid capture")
            checks["positive_control"] = not problems
            return out("tag_visible", "positive control: tagged partial visible in raw bytes, mid capture and final display") if not problems else out("control_failed", "; ".join(problems))
        elif tag_final:
            problems.append("a failed-attempt tag appeared in a healthy run")
        return out("healthy", "healthy control: one clean request, full answer exactly once") if not problems else out("control_failed", "; ".join(problems))

    partial_on_final = tag_final > 0 or any(fc.get(m, 0) for m in partial)
    notice_any = bool(notice_final or notice_raw)

    # ---- persistent fault ----
    if kind == "always":
        if not main_stream or any(r.get("fault") != fault for r in main):
            return out("n/a", "persistent fault not applied to every marked main request")
        if full_present:
            return out("n/a", "persistent fault but the full answer is displayed; check non-streaming deliveries")
        if notice_any:
            return out("reported_failure", "persistent fault ended with an error/retry notice" + ("" if notice_final else " (raw bytes only)"))
        if partial_on_final:
            return out("accepted_partial", "persistent fault ended with partial output and no notice")
        return out("n/a", "persistent-fault display evidence is insufficient")

    if kind != "once":
        raise ValueError(f"unknown condition kind {kind!r}")

    faulted = [r for r in main_stream if r.get("fault") == fault and r.get("fault_source") == "once"]
    if not faulted:
        return out("n/a", f"armed fault {fault} was not delivered to a marked main streaming request")
    first = faulted[0]
    later = [r for r in main_stream if r["seq"] > first["seq"]]
    retry = next((r for r in later if r.get("fault") == "F0" and _terminal_ok(r)), None)
    shown_mid = bool(tag and mid and mid.get("trigger") == "tag" and tag_count(mid.get("text"), tag) > 0)
    shown_raw = bool(interactive and raw.get("available") and raw.get("tag_seen"))
    shown_stdout = (not interactive) and tag_final > 0
    shown = shown_mid or shown_raw or shown_stdout
    checks.update({
        "fault_seq": first["seq"], "retry_seq": retry["seq"] if retry else None,
        "shown_mid": shown_mid, "shown_raw": shown_raw, "shown_stdout": shown_stdout,
        "mid_before_retry": bool(shown_mid and retry and mid.get("ts_ms") is not None
                                 and retry.get("started_ms") is not None
                                 and mid["ts_ms"] < retry["started_ms"]),
        "raw_tag_before_retry": bool(shown_raw and retry and raw.get("tag_first_ms") is not None
                                     and retry.get("started_ms") is not None
                                     and raw["tag_first_ms"] < retry["started_ms"]),
        "partial_on_final": partial_on_final,
    })

    if retry is None:
        if later:
            return out("n/a", "later requests exist but none completed cleanly")
        if notice_any:
            return out("reported_failure", "no retry; an error/retry notice was shown" + ("" if notice_final else " (raw bytes only)"))
        if partial_on_final:
            if len(main_stream) != 1:
                return out("n/a", "no retry but more than one main request")
            return out("accepted_partial", "single request; final display is the partial; no notice")
        return out("n/a", "no healthy retry and insufficient partial/failure evidence")

    carried = bool(retry.get("carries_partial") or retry.get("carries_tag"))
    decision = (retry.get("continuation") or {}).get("decision")
    checks.update({"retry_carried_partial": carried, "continuation_decision": decision})

    if carried:
        if decision == "continue":
            if full_once and (not interactive or complete is True):
                return out("continued", "retry carried the partial; the mock continued; final display reads the full answer exactly once")
            return out("n/a", "continue branch, but the final display does not read every marker of the full answer exactly once")
        if decision == "restart":
            if duplicated:
                return out("duplicate", "retry carried the partial; the mock restarted; the final display repeats markers")
            nxt = obs.get("next_request") or {}
            if nxt.get("carries_tag") and nxt.get("full_present"):
                return out("duplicate", "retry carried the partial; the mock restarted; the next request carries the partial and the full answer")
            return out("n/a", "retry carried the partial and the mock restarted, but the display shows one copy; needs a stored-context witness")
        return out("n/a", "retry carried the partial but no continuation decision was logged")

    if tag_final > 0:
        if full_present:
            return out("fork", "retry carried nothing; the failed attempt's partial stays on the final display next to the full answer")
        return out("n/a", "partial kept on the final display, but the full answer is not displayed")
    if interactive and complete is not True:
        return out("n/a", "final screen not proven complete (banner or prompt missing); cannot rule out the partial above it")
    if not full_once:
        return out("n/a", "final display does not read the full answer exactly once and carries no failed-attempt tag")
    if shown:
        return out("retracted", "partial shown (tag-keyed witness), then gone; the retry carried nothing; one complete answer")
    if interactive and not raw.get("available"):
        return out("n/a", "no raw byte witness; cannot tell not-shown from retracted")
    return out("not_shown", "the failed attempt's tag never reached the terminal; clean retry; one complete answer")


# ---------------- request bodies and stored sessions ----------------
STOP_RE = re.compile(r'"(?:stop_reason|finishReason|finish_reason)"\s*:\s*"([^"]+)"')


def content_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(content_text(v) for v in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if "content" in value:
            return content_text(value["content"])
    return ""


def messages_of(endpoint: str | None, body) -> list[dict]:
    if not isinstance(body, dict):
        return []
    if endpoint == "responses":
        items = body.get("input")
        return [i for i in items if isinstance(i, dict) and i.get("role")] if isinstance(items, list) else []
    msgs = body.get("messages")
    return [m for m in msgs if isinstance(m, dict)] if isinstance(msgs, list) else []


def request_witness(raw: bytes, endpoint: str | None, mark: str | None, tag: str | None) -> dict:
    """What a request body carries: the run mark, and assistant-role history (the
    partial of a failed attempt shows up here when a retry sends it back)."""
    text = raw.decode("utf-8", "replace")
    try:
        body = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        body = {}
    msgs = messages_of(endpoint, body)
    assistants = [content_text(m.get("content")) for m in msgs if m.get("role") == "assistant"]
    joined = "\n".join(assistants)
    amc = counts(joined)
    return {
        "has_mark": bool(mark) and mark in text,
        "assistant_messages": len(assistants),
        "assistant_marker_counts": amc,
        "carries_partial": any(k[0] in "PL" for k in amc),
        "carries_tag": bool(tag) and tag in compact(joined),
        "trailing_role": msgs[-1].get("role") if msgs else None,
        "partial_flag": bool(msgs) and msgs[-1].get("partial") is True,
    }


def _assistant_candidates(value) -> list[str]:
    found: list[str] = []
    if isinstance(value, list):
        for item in value:
            found.extend(_assistant_candidates(item))
    elif isinstance(value, dict):
        message = value.get("message") if isinstance(value.get("message"), dict) else value
        payload = value.get("payload") if isinstance(value.get("payload"), dict) else message
        role = payload.get("role") or message.get("role") or value.get("role")
        if role == "assistant" or value.get("type") == "assistant":
            text = content_text(payload.get("content", message.get("content", value.get("content", payload))))
            if text:
                found.append(text)
            return found
        for child in value.values():
            found.extend(_assistant_candidates(child))
    return found


def assistant_texts_in_file(raw: str) -> list[str]:
    """Assistant texts stored in a session file (JSONL, or one JSON document)."""
    objects = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            objects.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not objects:
        try:
            objects = [json.loads(raw)]
        except json.JSONDecodeError:
            return []
    texts: list[str] = []
    for obj in objects:
        texts.extend(_assistant_candidates(obj))
    return texts


def stop_reasons_in_file(raw: str) -> list[str]:
    return STOP_RE.findall(raw)


# ---------------- evidence directory -> observation ----------------
def load_observation(run_dir: Path | str, content: Content) -> dict:
    """Rebuild a run's observation bundle from its evidence directory.

    Each witness comes from its own file: mid.txt only with a mid.json whose trigger is
    the failed-attempt tag; final-view.txt (interactive) or stdout.txt (non-interactive)
    for the final display; raw.bin for the byte stream. A missing file stays missing.
    """
    run_dir = Path(run_dir)
    record = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
    obs = dict(record["observation_inputs"])
    interactive = obs.get("mode") == "interactive"
    final_name = "final-view.txt" if interactive else "stdout.txt"
    final_path = run_dir / final_name
    obs["final"] = {
        "text": final_path.read_text(encoding="utf-8", errors="replace") if final_path.exists() else "",
        "complete": (obs.get("final") or {}).get("complete"),
    }
    mid_meta = run_dir / "mid.json"
    mid_text = run_dir / "mid.txt"
    obs["mid"] = None
    if mid_meta.exists() and mid_text.exists():
        meta = json.loads(mid_meta.read_text(encoding="utf-8"))
        obs["mid"] = {"text": mid_text.read_text(encoding="utf-8", errors="replace"),
                      "ts_ms": meta.get("ts_ms"), "trigger": meta.get("trigger")}
    raw_path = run_dir / "raw.bin"
    obs["raw"] = (raw_analysis(raw_path.read_bytes(), obs.get("tag"), content, load_index(run_dir / "raw-index.jsonl"))
                  if raw_path.exists() else None)
    stderr_path = run_dir / "stderr.txt"
    if stderr_path.exists():
        obs["stderr"] = stderr_path.read_text(encoding="utf-8", errors="replace")
    return obs
