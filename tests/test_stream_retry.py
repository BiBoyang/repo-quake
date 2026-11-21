"""Tests for witness/stream-retry (phase 4): grader, byte witness, mock, version witness,
public export, and an end-to-end calibration run against a fake TUI.

The grader cases include the adversarial ones from the 2026-11-15 verifier report:
a server that restarts while the client hides the partial must not read as
"continued"; a long answer showing only its tail must not read as "continued"; a mid
capture keyed to a marker the retry also emits witnesses nothing; a final screen that
cannot be proven complete cannot support "retracted"; a healthy control is graded,
not assumed.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR = ROOT / "witness" / "stream-retry"
FIX = ROOT / "tests" / "fixtures" / "stream-retry"
sys.path.insert(0, str(SR))
sys.path.insert(1, str(ROOT / "skills" / "repo-quake" / "scripts"))

import card_gate  # noqa: E402
import grading  # noqa: E402
import summarize  # noqa: E402

C = grading.Content(SR / "content.json")
TAG = "〔xabc123〕"
NODE = shutil.which("node")
TMUX = shutil.which("tmux")


def para(prefix: str, width: int, a: int, b: int, tag: str | None = None, upto: int = 0) -> str:
    lines = []
    for i in range(a, b + 1):
        line = f"【{prefix}{i:0{width}d}】正文"
        if tag and i <= upto:
            line += f" {tag}"
        lines.append(line)
    return "\n".join(lines)


def P(a, b, tag=None, upto=0):
    return para("P", 2, a, b, tag, upto)


def L(a, b, tag=None, upto=0):
    return para("L", 3, a, b, tag, upto)


def screen(body: str) -> str:
    return " ▐▛███▛█   Claude Code v2.1.282\n❯ RUNmark 写一份三节分析报告\n\n" + body + "\n\n❯ \n"


def req(seq, fault="F0", source="always", ending="clean", aux=False, stream=True, carried=False,
        carried_tag=False, decision=None, started=None):
    ok = ending == "clean" and fault in ("F0", "F0T")
    return {"seq": seq, "fault": fault, "fault_source": source, "ending": ending, "aux": aux, "stream": stream,
            "witnesses": {"anthropic_message_stop": ok}, "carries_partial": carried, "carries_tag": carried_tag,
            "continuation": {"decision": decision} if decision else None,
            "started_ms": started if started is not None else seq * 1000}


def obs(condition, final_text, reqs, *, tag=TAG, mid=None, raw=None, complete=True, mode="interactive",
        profile=None, next_request=None, stderr="", exit_code=None):
    return {"condition": condition, "mode": mode, "profile": profile, "tag": tag, "requests": reqs,
            "final": {"text": final_text, "complete": complete}, "mid": mid,
            "raw": raw if raw is not None else {"available": True, "tag_seen": False, "notices": []},
            "next_request": next_request, "stderr": stderr, "exit_code": exit_code}


def g(o):
    return grading.grade(o, C)


class TextWitness(unittest.TestCase):
    def test_wrapped_marker_counts(self):
        self.assertEqual(grading.counts("【P2\n   4】 and 【P01】"), {"P24": 1, "P01": 1})

    def test_strip_ansi_breaks_on_cursor_moves_and_drops_osc(self):
        raw = b"\x1b]0;title " + TAG.encode() + b"\x07\x1b[31mAPI error\x1b[0m\x1b[5;1HRetrying"
        text = grading.strip_ansi(raw)
        self.assertNotIn(TAG, text)  # inside an OSC title: never on screen
        self.assertEqual([line for line in text.splitlines() if line], ["API error", "Retrying"])

    def test_tag_split_by_cursor_moves_is_still_seen(self):
        raw = b"\x1b[3;1H\xe3\x80\x94xab\x1b[3;6Hc123\xe3\x80\x95"
        info = grading.raw_analysis(raw, TAG, C)
        self.assertTrue(info["tag_seen"])
        self.assertFalse(info["tag_contiguous"])

    def test_first_seen_ms_maps_bytes_to_tap_time(self):
        chunks = [b"\x1b[?1049h hello ", b"\xe3\x80\x94xab", b"c123\xe3\x80\x95 tail"]
        raw, index, off = b"", [], 0
        for i, c in enumerate(chunks):
            index.append({"t_ms": 1000 + i * 10, "offset": off, "len": len(c)})
            raw += c
            off += len(c)
        info = grading.raw_analysis(raw, TAG, C, index, {"tail": "tail"})
        self.assertEqual(info["tag_first_ms"], 1020)  # complete only once the last chunk arrived
        self.assertEqual(info["alt_screen_on_ms"], 1000)
        self.assertEqual(info["first_seen_ms"]["tail"], 1020)

    def test_notice_vocabulary_excludes_model_content(self):
        text = "✻ API error · Retrying in 1s · attempt 1/10\n  自动重试或续写成功，是最理想的工程形态。\n【P19】L3 告知加恢复"
        self.assertEqual(grading.notices(text, C), ["✻ API error · Retrying in 1s · attempt 1/10"])

    def test_quiet_window_floor(self):
        with self.assertRaises(ValueError):
            grading.no_retry_due(True, False, 0, 0, 100, quiet_s=30)
        self.assertFalse(grading.no_retry_due(True, False, 0, 50, 100, quiet_s=60))
        self.assertTrue(grading.no_retry_due(True, False, 0, 0, 100, quiet_s=60))
        self.assertFalse(grading.no_retry_due(True, True, 0, 0, 100, quiet_s=60))


class HealthyControls(unittest.TestCase):
    def test_healthy(self):
        r = g(obs("F0-pre", screen(P(1, 24)), [req(1, aux=True), req(2)], tag=None))
        self.assertEqual(r["verdict"], "healthy", r["reason"])

    def test_duplicated_display_is_not_healthy(self):
        r = g(obs("F0-pre", screen(P(1, 24) + "\n" + P(1, 24)), [req(2)], tag=None))
        self.assertEqual(r["verdict"], "control_failed")

    def test_no_request_is_not_healthy(self):
        r = g(obs("F0-post", screen(P(1, 24)), [], tag=None))
        self.assertEqual(r["verdict"], "control_failed")

    def test_second_main_request_is_not_healthy(self):
        r = g(obs("F0-pre", screen(P(1, 24)), [req(2), req(3)], tag=None))
        self.assertEqual(r["verdict"], "control_failed")
        self.assertIn("exactly one main request", r["reason"])

    def test_notice_in_raw_bytes_is_not_healthy(self):
        raw = {"available": True, "tag_seen": False, "notices": ["Reconnecting... 1/5"]}
        r = g(obs("F0-pre", screen(P(1, 24)), [req(2)], tag=None, raw=raw))
        self.assertEqual(r["verdict"], "control_failed")

    def test_incomplete_screen_is_not_healthy(self):
        r = g(obs("F0-pre", P(1, 24), [req(2)], tag=None, complete=False))
        self.assertEqual(r["verdict"], "control_failed")

    def test_positive_control(self):
        raw = {"available": True, "tag_seen": True, "notices": []}
        mid = {"text": P(1, 3, TAG, 3), "ts_ms": 5, "trigger": "tag"}
        ok = g(obs("F0-tag", screen(P(1, 24, TAG, 12)), [req(2, source="once")], raw=raw, mid=mid))
        self.assertEqual(ok["verdict"], "tag_visible", ok["reason"])
        lost = g(obs("F0-tag", screen(P(1, 24)), [req(2, source="once")], raw=raw, mid=mid))
        self.assertEqual(lost["verdict"], "control_failed")


class RetryOutcomes(unittest.TestCase):
    faulted = staticmethod(lambda fault="F1", ending="fin": req(2, fault, "once", ending))

    def test_fault_not_delivered(self):
        r = g(obs("F1-once", screen(P(1, 24)), [req(2), req(3)]))
        self.assertEqual(r["verdict"], "n/a")

    def test_not_shown(self):
        r = g(obs("F1-once", screen(P(1, 24)), [self.faulted(), req(3)]))
        self.assertEqual(r["verdict"], "not_shown", r["reason"])
        # phase 5: every retry-branch verdict records `reported` from the notices
        self.assertEqual(r["fields"], {"detected": True, "contained": True, "recovered": True, "reported": False})
        self.assertEqual(r["checks"]["notice_where"], "none")

    def test_not_shown_needs_the_byte_witness(self):
        r = g(obs("F1-once", screen(P(1, 24)), [self.faulted(), req(3)], raw={"available": False}))
        self.assertEqual(r["verdict"], "n/a")

    def test_retracted_by_tag_keyed_mid_capture(self):
        mid = {"text": screen(P(1, 5, TAG, 5)), "ts_ms": 2500, "trigger": "tag"}
        r = g(obs("F1-once", screen(P(1, 24)), [self.faulted(), req(3, started=3000)], mid=mid))
        self.assertEqual(r["verdict"], "retracted", r["reason"])
        self.assertTrue(r["checks"]["mid_before_retry"])

    def test_retracted_by_raw_bytes_only(self):
        raw = {"available": True, "tag_seen": True, "tag_first_ms": 2100, "notices": ["API error · Retrying in 1s"]}
        r = g(obs("F6-once", screen(P(1, 24)), [self.faulted("F6", "clean"), req(3, started=3000)], raw=raw))
        self.assertEqual(r["verdict"], "retracted")
        self.assertTrue(r["checks"]["raw_tag_before_retry"])

    def test_marker_keyed_mid_capture_witnesses_nothing(self):
        # the 2026-11-14 harness triggered on 【P01】, which the retry also emits
        mid = {"text": screen(P(1, 24)), "ts_ms": 3500, "trigger": "marker"}
        r = g(obs("F1-once", screen(P(1, 24)), [self.faulted(), req(3)], mid=mid))
        self.assertEqual(r["verdict"], "not_shown")

    def test_retracted_needs_a_complete_final_screen(self):
        # alternate screen: a 35-row capture that shows only the answer cannot rule out the partial above it
        raw = {"available": True, "tag_seen": True, "notices": []}
        r = g(obs("FLONG-once", L(161, 200), [self.faulted("FLONG"), req(3)], raw=raw, complete=False))
        self.assertEqual(r["verdict"], "n/a")

    def test_full_answer_on_an_incomplete_screen_is_not_retracted(self):
        # the whole answer fits on a 35-row alternate screen while the banner and the prompt
        # have scrolled off: the partial may still sit above the capture
        raw = {"available": True, "tag_seen": True, "notices": []}
        r = g(obs("F1-once", P(1, 24), [self.faulted(), req(3)], raw=raw, complete=False))
        self.assertEqual(r["verdict"], "n/a")
        self.assertIn("not proven complete", r["reason"])

    def test_fork(self):
        final = screen(P(1, 12, TAG, 12) + "\n" + P(1, 24))
        r = g(obs("F1-once", final, [self.faulted(), req(3)]))
        self.assertEqual(r["verdict"], "fork", r["reason"])
        self.assertFalse(r["fields"]["contained"])
        self.assertFalse(r["fields"]["reported"])

    def test_continued(self):
        final = screen(P(1, 12, TAG, 12) + "\n" + P(13, 24))
        reqs = [self.faulted(), req(3, carried=True, carried_tag=True, decision="continue")]
        r = g(obs("F1-once", final, reqs))
        self.assertEqual(r["verdict"], "continued", r["reason"])

    def test_restart_with_hidden_partial_is_not_continued(self):
        # adversarial (a): the retry carried the partial, the server rewrote from scratch,
        # and the client hid the partial: the display reads once, but nothing was continued
        reqs = [self.faulted("FLONG"), req(3, carried=True, carried_tag=True, decision="restart")]
        r = g(obs("FLONG-once", screen(L(1, 200)), reqs))
        self.assertNotEqual(r["verdict"], "continued")
        self.assertEqual(r["verdict"], "n/a")

    def test_long_tail_only_is_not_continued(self):
        # adversarial (b): only L161-L200 on the final display; L001-L160 must be there too
        reqs = [self.faulted("FLONG"), req(3, carried=True, carried_tag=True, decision="continue")]
        r = g(obs("FLONG-once", screen(L(161, 200)), reqs))
        self.assertEqual(r["verdict"], "n/a")

    def test_duplicate(self):
        final = screen(P(1, 12, TAG, 12) + "\n" + P(1, 24))
        reqs = [self.faulted(), req(3, carried=True, carried_tag=True, decision="restart")]
        r = g(obs("F1-once", final, reqs))
        self.assertEqual(r["verdict"], "duplicate")

    def test_duplicate_from_next_request(self):
        reqs = [self.faulted(), req(3, carried=True, carried_tag=True, decision="restart")]
        nxt = {"carries_tag": True, "full_present": True}
        r = g(obs("F1-once", screen(P(1, 24)), reqs, next_request=nxt))
        self.assertEqual(r["verdict"], "duplicate")

    def test_accepted_partial(self):
        r = g(obs("F6-once", screen(P(1, 12, TAG, 12)), [self.faulted("F6", "clean")]))
        self.assertEqual(r["verdict"], "accepted_partial")
        self.assertEqual(r["fields"], {"detected": False, "reported": False})

    def test_reported_failure_from_raw_notice(self):
        raw = {"available": True, "tag_seen": True, "notices": ["Error: [provider.connection_error] terminated"]}
        r = g(obs("F1-once", screen(P(1, 12, TAG, 12)), [self.faulted()], raw=raw))
        self.assertEqual(r["verdict"], "reported_failure")

    def test_unfinished_retry(self):
        r = g(obs("F1-once", screen(P(1, 12)), [self.faulted(), req(3, ending="client-abort")]))
        self.assertEqual(r["verdict"], "n/a")

    def test_noninteractive_stdout_is_append_only(self):
        out = P(1, 12, TAG, 12) + "\n" + P(1, 24)
        r = g(obs("F1-once", out, [self.faulted(), req(3)], mode="noninteractive", raw=None, complete=None))
        self.assertEqual(r["verdict"], "fork")
        clean = g(obs("F1-once", P(1, 24), [self.faulted(), req(3)], mode="noninteractive", raw=None, complete=None))
        self.assertEqual(clean["verdict"], "not_shown")

    def test_persistent_fault(self):
        reqs = [req(i, "F1", "always", "fin") for i in (2, 3, 4)]
        raw = {"available": True, "tag_seen": False, "notices": ["API Error: Connection dropped (ECONNRESET)"]}
        self.assertEqual(g(obs("F1-always", screen(P(1, 12)), reqs, tag=None, raw=raw))["verdict"], "reported_failure")
        self.assertEqual(g(obs("F1-always", screen(P(1, 24)), reqs, tag=None, raw=raw))["verdict"], "n/a")


def R(tag=None):
    """The thinking paragraphs of content.json, optionally tagged (FTHINK / F0T / F5)."""
    return "\n".join(f"{p} {tag}" if tag else p for p in C.data["reasoning"])


class Phase5Grading(unittest.TestCase):
    """FTHINK, the thinking positive control, `reported` from notices, F4/F5 signals."""
    fthink = staticmethod(lambda ending="fin", fault="FTHINK1": req(2, fault, "once", ending))

    def test_reported_reads_every_channel(self):
        raw = {"available": True, "tag_seen": True, "notices": ["API error · Retrying in 1s · attempt 1/10"]}
        r = g(obs("F1-once", screen(P(1, 24)), [req(2, "F1", "once", "fin"), req(3)], raw=raw))
        self.assertEqual((r["verdict"], r["fields"]["reported"], r["checks"]["notice_where"]), ("retracted", True, "raw-only"))
        err = "\x1b[31m[ERROR agent req=1]\x1b[0m stream returned error RequestFailed at turn 1\n"
        r = g(obs("F1-once", P(1, 24), [req(2, "F1", "once", "fin"), req(3)], mode="noninteractive", raw=None,
                  complete=None, stderr=err, exit_code=0))
        self.assertEqual((r["verdict"], r["fields"]["reported"], r["checks"]["notice_where"]), ("not_shown", True, "final"))

    def test_fthink_fork_keeps_the_thinking_on_screen(self):
        final = screen(R(TAG) + "\n" + P(1, 24))
        r = g(obs("FTHINK1-once", final, [self.fthink(), req(3)]))
        self.assertEqual(r["verdict"], "fork", r["reason"])
        self.assertEqual(r["checks"]["final_reasoning_markers"], [f"R0{i}" for i in range(1, 7)])

    def test_fthink_retracted_by_a_discarded_segment(self):
        # stream-json: the tagged thinking was emitted, the consumer's display dropped it
        r = g({**obs("FTHINK6-once", P(1, 24), [self.fthink("clean", "FTHINK6"), req(3)], mode="noninteractive",
                     raw=None, complete=None, exit_code=0), "emitted": R(TAG) + P(1, 24)})
        self.assertEqual(r["verdict"], "retracted", r["reason"])
        self.assertEqual(r["checks"]["emitted_tag_count"], 6)

    def test_fthink_never_emitted_is_not_shown(self):
        r = g({**obs("FTHINK1-once", P(1, 24), [self.fthink(), req(3)], mode="noninteractive", raw=None,
                     complete=None, exit_code=0), "emitted": P(1, 24)})
        self.assertEqual(r["verdict"], "not_shown", r["reason"])

    def test_thinking_positive_control(self):
        raw = {"available": True, "tag_seen": True, "notices": []}
        ok = g(obs("F0T-tag", screen(R(TAG) + "\n" + P(1, 24)), [req(2, "F0T", "once")], raw=raw))
        self.assertEqual(ok["verdict"], "tag_visible", ok["reason"])
        hidden = g({**obs("F0T-tag", P(1, 24), [req(2, "F0T", "once")], mode="noninteractive", raw=None,
                          complete=None, exit_code=0), "emitted": P(1, 24)})
        self.assertEqual(hidden["verdict"], "thinking_hidden", hidden["reason"])
        broken = g(obs("F0T-tag", screen(R(TAG) + "\n" + P(1, 12)), [req(2, "F0T", "once")], raw=raw))
        self.assertEqual(broken["verdict"], "control_failed")

    def test_subject_chrome_is_not_a_notice(self):
        # metacodes' empty input box contains "errors"; the exclusion travels with the run
        mc = sys.modules.get("runner") or __import__("runner")
        chrome = mc.Metacodes.chrome_re
        final = "╭─ metacodes v0.12.1-dev ─╮\n❯ RUNmark 写\n" + P(1, 24) + '\n❯ Try "fix typecheck errors"\n ? for shortcuts\n'
        bad = g(obs("F0-pre", final, [req(2)], tag=None))
        self.assertEqual(bad["verdict"], "control_failed")
        ok = g({**obs("F0-pre", final, [req(2)], tag=None), "chrome": chrome})
        self.assertEqual(ok["verdict"], "healthy", ok["reason"])
        raw = grading.raw_analysis(final.encode(), None, C, ignore=grading.chrome_pattern(chrome))
        self.assertEqual(raw["notices"], [])
        self.assertEqual(grading.notices("❯ API error: something", C, ignore=grading.chrome_pattern(chrome)),
                         ["❯ API error: something"])

    def test_thinking_markers_are_not_foreign_in_a_healthy_run(self):
        r = g(obs("F0-pre", screen("【R01】想一想\n" + P(1, 24)), [req(2)], tag=None))
        self.assertEqual(r["verdict"], "healthy", r["reason"])


class SignalGrading(unittest.TestCase):
    """F4 (length stop after a full answer and an overflow) and F5 (thinking only)."""
    f4 = staticmethod(lambda: req(2, "F4", "once", "clean"))

    def test_signal_vocabulary_is_wider_only_for_f4_f5(self):
        line = "⎿  Output token limit hit · continuing"
        self.assertEqual(grading.notices(line, C), [])
        self.assertEqual(grading.notices(line, C, grading.SIGNAL_RE), [line])
        # model content about truncation never counts
        self.assertEqual(grading.notices("【P18】L2 明确告知，工具直接说明回答被截断，用户不会被误导。", C, grading.SIGNAL_RE), [])

    def test_continued_without_a_notice(self):
        final = screen(P(1, 24, TAG, 12) + "\n" + para("Q", 2, 1, 24) + "\n" + P(1, 24))
        r = g(obs("F4-once", final, [self.f4(), req(3, carried=True, carried_tag=True)]))
        self.assertEqual(r["verdict"], "length_continued", r["reason"])
        # recovered/contained depend on the server branch: not recorded for a continuation
        self.assertEqual(r["fields"], {"detected": True, "reported": False})
        self.assertEqual(r["checks"]["signal_where"], "none")
        self.assertTrue(r["checks"]["first_attempt_on_final"])
        # -p prints the last message only: the first attempt is gone from stdout
        last_only = g(obs("F4-once", P(1, 24), [self.f4(), req(3, carried=True, carried_tag=True)],
                          mode="noninteractive", raw=None, complete=None, exit_code=0))
        self.assertFalse(last_only["checks"]["first_attempt_on_final"])

    def test_fresh_retry_with_a_transient_notice(self):
        raw = {"available": True, "tag_seen": True, "notices": ["• Reconnecting... 1/5"], "signals_extra": []}
        r = g(obs("F4-once", screen(P(1, 24)), [self.f4(), req(3)], raw=raw))
        self.assertEqual(r["verdict"], "length_retried", r["reason"])
        self.assertEqual(r["fields"], {"detected": True, "reported": True, "recovered": True, "contained": True})
        self.assertEqual(r["checks"]["signal_where"], "raw-only")

    def test_fresh_retry_leaving_the_first_attempt(self):
        final = screen(P(1, 24, TAG, 12) + "\n" + para("Q", 2, 1, 24) + "\n" + P(1, 24))
        r = g(obs("F4-once", final, [self.f4(), req(3)]))
        self.assertEqual(r["verdict"], "length_retried")
        self.assertFalse(r["fields"]["contained"])

    def test_no_follow_up(self):
        out = P(1, 24, TAG, 12) + "\n" + para("Q", 2, 1, 24)
        silent = g(obs("F4-once", out, [self.f4()], mode="noninteractive", raw=None, complete=None, exit_code=0))
        self.assertEqual(silent["verdict"], "accepted_silently")
        bare = g(obs("F4-once", out, [self.f4()], mode="noninteractive", raw=None, complete=None, exit_code=1))
        self.assertEqual((bare["verdict"], bare["fields"]), ("exit_code_only", {"detected": True, "reported": False}))
        told = g(obs("F5-once", "", [req(2, "F5", "once", "clean")], mode="noninteractive", raw=None, complete=None,
                     exit_code=1, stderr="error: stopped (max_tokens_exhausted): the reply was cut off\n"))
        self.assertEqual(told["verdict"], "reported_failure")

    def test_not_delivered(self):
        self.assertEqual(g(obs("F5-once", screen(P(1, 24)), [req(2), req(3)]))["verdict"], "n/a")


class StructuredStdout(unittest.TestCase):
    def lines(self, *objs):
        return "".join(json.dumps(o, ensure_ascii=False) + "\n" for o in objs) + "\n"

    def test_stream_json_drops_discarded_segments_with_their_thinking(self):
        out = self.lines(
            {"type": "turn_begin", "turn": 1},
            {"type": "output_segment_begin", "index": 0, "turn": 1, "group": 0},
            {"type": "thinking", "text": f"【R01】想 {TAG}\n"},
            {"type": "text", "text": f"【P01】半截 {TAG}\n"},
            {"type": "output_segment_end", "index": 0, "turn": 1, "group": 0, "disposition": "discarded", "bytes": 9},
            {"type": "output_segment_begin", "index": 1, "turn": 1, "group": 0},
            {"type": "text", "text": "【P01】完整\n"},
            {"type": "output_segment_end", "index": 1, "turn": 1, "group": 0, "disposition": "final", "bytes": 9},
            {"type": "thinking", "text": "【R02】段外\n"},
            {"type": "run_end", "turns": 1, "tool_calls": 0, "stop_reason": "end_turn"})
        d = grading.stream_json_display(out)
        self.assertNotIn(TAG, d["display"])
        self.assertIn("【P01】完整", d["display"])
        self.assertIn("【R02】段外", d["display"])  # nothing tells the consumer to drop it
        self.assertEqual((d["extra"]["discarded_segments"], d["extra"]["lines_outside_segments"],
                          d["extra"]["run_end_stop_reason"]), (1, 1, "end_turn"))
        self.assertEqual(d["extra"]["segments"][0]["thinking_markers"], ["R01"])

    def test_result_line(self):
        out = self.lines({"type": "result", "stop_reason": "end_turn", "text": P(1, 24), "text_kind": "final"})
        d = grading.result_line_display(out)
        self.assertEqual(grading.counts(d["display"]), {f"P{i:02d}": 1 for i in range(1, 25)})
        self.assertEqual(d["extra"]["stop_reason"], "end_turn")

    def test_regrade_re_derives_the_display(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            inputs = {"condition": "F1-once", "mode": "noninteractive", "profile": "short", "tag": TAG,
                      "requests": [req(2, "F1", "once", "fin"), req(3)], "final": {"complete": None},
                      "exit_code": 0, "display_kind": "stream-json"}
            (run / "record.json").write_text(json.dumps({"verdict": "?", "observation_inputs": inputs}), encoding="utf-8")
            out = self.lines(
                {"type": "output_segment_begin", "index": 0},
                *({"type": "text", "text": f"【P{i:02d}】x {TAG}\n"} for i in range(1, 13)),
                {"type": "output_segment_end", "index": 0, "disposition": "discarded", "bytes": 1},
                {"type": "output_segment_begin", "index": 1},
                *({"type": "text", "text": f"【P{i:02d}】y\n"} for i in range(1, 25)),
                {"type": "output_segment_end", "index": 1, "disposition": "final", "bytes": 1})
            (run / "stdout.txt").write_text(out, encoding="utf-8")
            self.assertEqual(g(grading.load_observation(run, C))["verdict"], "retracted")


class Bodies(unittest.TestCase):
    def test_dsh_session_log(self):
        rows = [{"type": "user/message", "seq": 8, "data": {"role": "user", "content": [{"type": "text", "text": "RUNx"}]}},
                {"type": "assistant/message", "seq": 14, "data": {"turn": 1, "message": {"role": "assistant",
                 "content": [{"type": "text", "text": "【P01】a"}]}}},
                {"type": "turn/end", "seq": 16, "data": {"turn": 1, "reason": {"kind": "max-tokens"}}}]
        raw = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        self.assertEqual(grading.assistant_texts_in_file(raw), ["【P01】a"])
        self.assertEqual(grading.stop_reasons_in_file(raw), ["max-tokens"])
        claude = json.dumps({"message": {"role": "assistant", "stop_reason": "end_turn"}})
        self.assertEqual(grading.stop_reasons_in_file(claude + "\n" + raw), ["end_turn", "max-tokens"])
        with tempfile.TemporaryDirectory() as tmp:
            from compression import zstd
            path = Path(tmp) / "session.v4.jsonl.zstd"
            path.write_bytes(zstd.compress(raw.encode("utf-8")))
            self.assertEqual(grading.read_session_text(path), raw)

    def test_metacodes_transcript_blocks(self):
        raw = (json.dumps({"role": "user", "blocks": [{"type": "text", "text": "RUNx"}]}) + "\n"
               + json.dumps({"role": "assistant", "delivered": False,
                             "blocks": [{"type": "thinking", "thinking": "【R01】a"}, {"type": "text", "text": "【P01】b"}]}) + "\n")
        self.assertEqual(grading.assistant_texts_in_file(raw), ["【R01】a【P01】b"])

    def test_request_witness_sees_carried_thinking(self):
        body = {"messages": [{"role": "user", "content": "RUNmark go"},
                             {"role": "assistant", "content": [{"type": "thinking", "thinking": f"【R01】x {TAG}", "signature": "s"}]}]}
        w = grading.request_witness(json.dumps(body).encode(), "anthropic", "RUNmark", TAG)
        self.assertTrue(w["carries_tag"])
        self.assertFalse(w["carries_partial"])

    def test_request_witness_parses_escaped_json(self):
        body = {"input": [{"role": "user", "content": [{"type": "input_text", "text": "RUNmark go"}]},
                          {"role": "assistant", "content": [{"type": "output_text", "text": f"【P01】x {TAG}"}]}]}
        raw = json.dumps(body).encode()  # ensure_ascii: the tag travels as \\u escapes
        w = grading.request_witness(raw, "responses", "RUNmark", TAG)
        self.assertTrue(w["has_mark"] and w["carries_partial"] and w["carries_tag"])
        self.assertEqual(w["trailing_role"], "assistant")

    def test_request_witness_ignores_user_text(self):
        raw = json.dumps({"messages": [{"role": "user", "content": f"【P01】 {TAG}"}]}).encode()
        w = grading.request_witness(raw, "anthropic", "RUNmark", TAG)
        self.assertFalse(w["has_mark"] or w["carries_partial"] or w["carries_tag"])

    def test_session_files(self):
        claude = json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "【P01】a"}], "stop_reason": "end_turn"}})
        codex = json.dumps({"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "【P02】b"}]}})
        raw = claude + "\n" + codex + "\n"
        self.assertEqual(grading.assistant_texts_in_file(raw), ["【P01】a", "【P02】b"])
        self.assertEqual(grading.stop_reasons_in_file(raw), ["end_turn"])


class RegradeFromFiles(unittest.TestCase):
    def test_mid_never_comes_from_the_final_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            inputs = {"condition": "F1-once", "mode": "interactive", "profile": "short", "tag": TAG,
                      "requests": [req(2, "F1", "once", "fin"), req(3)], "final": {"complete": True}}
            (run / "record.json").write_text(json.dumps({"verdict": "?", "observation_inputs": inputs}), encoding="utf-8")
            (run / "final-view.txt").write_text(screen(P(1, 24)), encoding="utf-8")
            o = grading.load_observation(run, C)
            self.assertIsNone(o["mid"])
            self.assertIsNone(o["raw"])
            self.assertEqual(g(o)["verdict"], "n/a")  # no byte witness, no mid: cannot be "retracted"
            # a mid.txt without a tag-trigger meta file is ignored as well
            (run / "mid.txt").write_text(screen(P(1, 5, TAG, 5)), encoding="utf-8")
            self.assertIsNone(grading.load_observation(run, C)["mid"])
            (run / "mid.json").write_text(json.dumps({"ts_ms": 1, "trigger": "tag"}), encoding="utf-8")
            self.assertEqual(g(grading.load_observation(run, C))["verdict"], "retracted")



# ---------------- mock integration (needs node) ----------------
class MockProc:
    """A mock.mjs instance on an ephemeral loopback port with its own token and logdir."""

    def __init__(self, tmp: Path, *extra: str):
        self.dir = tmp / f"mock-{secrets.token_hex(3)}"
        self.token = secrets.token_hex(12)
        env = {"PATH": os.environ.get("PATH", ""), "MOCK_CONTROL_TOKEN": self.token, "MOCK_INSTANCE": "inst-test"}
        ready = self.dir / "ready.json"
        self.dir.mkdir(parents=True)
        self.proc = subprocess.Popen([NODE, str(SR / "mock.mjs"), "--port", "0", "--delay", "0", "--long-delay", "0",
                                      "--logdir", str(self.dir), "--ready-file", str(ready), *extra],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        for _ in range(200):
            if ready.exists():
                break
            time.sleep(0.02)
        self.port = json.loads(ready.read_text())["port"]
        self.base = f"http://127.0.0.1:{self.port}"

    def control(self, body=None, token=True):
        headers = {"content-type": "application/json"}
        if token:
            headers["x-mock-token"] = self.token
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base}/__control", data=data, headers=headers,
                                     method="POST" if body is not None else "GET")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)

    def post(self, path, body):
        """Returns (text, complete): text of every SSE data/JSON body, and whether the HTTP body ended cleanly."""
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("POST", path, json.dumps(body), {"content-type": "application/json"})
        resp = conn.getresponse()
        try:
            return resp.read().decode(), True
        except http.client.IncompleteRead as exc:
            return exc.partial.decode(errors="replace"), False
        finally:
            conn.close()

    def log(self, at_least: int = 0):
        """Delivery records; the mock appends one right after closing a stream, so wait for it."""
        path = self.dir / "delivery.jsonl"
        for _ in range(250):
            rows = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
            if len(rows) >= at_least:
                return rows
            time.sleep(0.02)
        return rows

    def stop(self):
        self.proc.terminate()
        self.proc.wait(timeout=5)


def cc(text, stream=True, structured=False, tools=1, extra_messages=()):
    body = {"model": "m", "stream": stream, "messages": [{"role": "user", "content": text}, *extra_messages]}
    if tools:
        body["tools"] = [{"type": "function", "function": {"name": "f"}}]
    if structured:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "t"}}
    return body


@unittest.skipUnless(NODE, "node not available")
class MockIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rq-mock-test-"))
        self.mocks = []

    def tearDown(self):
        for m in self.mocks:
            m.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mock(self, *extra):
        m = MockProc(self.tmp, *extra)
        self.mocks.append(m)
        return m

    def test_control_plane_needs_the_token(self):
        m = self.mock()
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            m.control(token=False)
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()
        self.assertEqual(m.control()["instance"], "inst-test")
        with urllib.request.urlopen(f"{m.base}/health", timeout=5) as r:
            self.assertEqual(json.load(r), {"ok": True, "instance": "inst-test"})

    def test_once_fault_is_pinned_to_the_main_streaming_request(self):
        m = self.mock()
        m.control({"once": {"fault": "F1", "match": "RUNx", "tag": TAG}})
        text, done = m.post("/v1/chat/completions", cc("RUNx", stream=False))       # non-streaming
        self.assertTrue(done and "【P24】" in text)
        text, done = m.post("/v1/chat/completions", cc("RUNx", structured=True))    # title request
        self.assertTrue(done and "【P" not in text)
        text, done = m.post("/v1/chat/completions", cc("other run"))                # no mark
        self.assertTrue(done and text.rstrip().endswith("data: [DONE]"))
        text, done = m.post("/v1/chat/completions", cc("RUNx"))                     # the main answer
        self.assertFalse(done)
        self.assertEqual(text.count(TAG), 12)
        self.assertNotIn("【P13】", text)
        text, done = m.post("/v1/chat/completions", cc("RUNx"))                     # the retry
        self.assertTrue(done and "【P24】" in text and TAG not in text)
        sources = [(e["fault"], e["fault_source"], e["stream"], e["aux"]) for e in m.log(5)]
        self.assertEqual(sources, [("F0", "always", False, False), ("F0", "always", True, True),
                                   ("F0", "always", True, False), ("F1", "once", True, False),
                                   ("F0", "always", True, False)])

    def test_always_fault_fails_non_streaming_requests_too(self):
        m = self.mock()
        m.control({"always": "F1"})
        text, done = m.post("/v1/chat/completions", cc("x", stream=False))
        self.assertEqual(text, "")
        self.assertEqual(m.log(1)[-1]["ending"], "fin")

    def test_f6_ends_cleanly_without_a_terminator(self):
        m = self.mock()
        m.control({"once": {"fault": "F6", "match": "RUNy"}})
        text, done = m.post("/v1/chat/completions", cc("RUNy"))
        self.assertTrue(done)
        self.assertNotIn("data: [DONE]", text)
        self.assertNotIn('"finish_reason":"stop"', text)
        self.assertIn("【P12】", text)
        self.assertEqual(m.log(1)[-1]["witnesses"]["cc_done"], False)

    def test_long_profile_and_flong(self):
        m = self.mock()
        m.control({"profile": "long", "once": {"fault": "FLONG", "match": "RUNz", "tag": TAG}})
        text, done = m.post("/v1/chat/completions", cc("RUNz"))
        self.assertFalse(done)
        self.assertEqual(text.count(TAG), 160)
        self.assertIn("【L160】", text)
        text, done = m.post("/v1/chat/completions", cc("RUNz"))
        self.assertTrue(done and "【L001】" in text and "【L200】" in text)

    def test_continuation_branches_are_logged(self):
        partial = {"role": "assistant", "content": P(1, 12)}
        cases = [("restart", {}, "【P01】"), ("continue", {}, "【P13】"),
                 ("documented", {}, "【P01】"), ("documented", {"partial": True}, "【P13】")]
        for mode, flag, first in cases:
            m = self.mock("--continuation", mode)
            text, done = m.post("/v1/chat/completions", cc("q", extra_messages=[{**partial, **flag}]))
            got = grading.MARKER_RE.findall(text)
            self.assertEqual(got[0], first.strip("【】"), (mode, flag))
            self.assertEqual(got[-1], "P24")
            self.assertEqual(m.log(1)[-1]["continuation"]["decision"], "continue" if first == "【P13】" else "restart")
        m = self.mock("--continuation", "documented")  # Anthropic assistant prefill is documented: continue
        text, done = m.post("/v1/messages", {"model": "m", "stream": True, "messages": [{"role": "user", "content": "q"}, partial]})
        self.assertEqual(grading.MARKER_RE.findall(text)[0], "P13")

    def test_client_hanging_up_on_the_terminal_event_is_not_an_abort(self):
        # codex closes the socket right after response.completed (pilot 2026-11-15)
        m = self.mock()
        sock = socket.create_connection(("127.0.0.1", m.port))
        body = json.dumps({"model": "m", "stream": True, "input": [{"role": "user", "content": "x"}], "tools": [{"type": "function"}]})
        sock.sendall(f"POST /v1/responses HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: {len(body.encode())}\r\n\r\n{body}".encode())
        data = b""
        while b"response.completed" not in data:
            data += sock.recv(65536)
        sock.close()
        entry = m.log(1)[-1]
        self.assertEqual(entry["ending"], "clean")
        self.assertTrue(entry["witnesses"]["responses_completed"])

    def test_fthink_streams_tagged_thinking_and_nothing_else(self):
        m = self.mock()
        anth = lambda mark: {"model": "m", "stream": True, "messages": [{"role": "user", "content": mark}]}
        resp = lambda mark: {"model": "m", "stream": True, "input": [{"role": "user", "content": mark}]}
        for path, body in (("/v1/messages", anth), ("/v1/chat/completions", lambda mark: cc(mark)),
                           ("/v1/responses", resp)):
            for fault, clean in (("FTHINK1", False), ("FTHINK6", True)):
                mark = f"RUN{fault}{path.replace('/', '')}"
                m.control({"once": {"fault": fault, "match": mark, "tag": TAG}})
                text, done = m.post(path, body(mark))
                self.assertEqual(done, clean, (path, fault))
                self.assertEqual(text.count(TAG), 6, (path, fault))
                self.assertIn("【R06】", text)
                self.assertNotIn("【P01】", text)
                entry = m.log()[-1]
                self.assertEqual((entry["fault"], entry["ending"]), (fault, "clean" if clean else "fin"))
                self.assertFalse(any(entry["witnesses"].values()), (path, fault))
                text, done = m.post(path, body(mark))       # the retry: a plain healthy answer
                self.assertTrue(done and "【P24】" in text and TAG not in text and "【R01】" not in text)

    def test_f0t_is_a_complete_thinking_block_then_the_answer(self):
        m = self.mock()
        m.control({"once": {"fault": "F0T", "match": "RUNt", "tag": TAG}})
        text, done = m.post("/v1/messages", {"model": "m", "stream": True, "messages": [{"role": "user", "content": "RUNt"}]})
        self.assertTrue(done)
        events = [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]
        kinds = [(e["type"], (e.get("delta") or e.get("content_block") or {}).get("type"), e.get("index")) for e in events]
        self.assertIn(("content_block_delta", "signature_delta", 0), kinds)
        self.assertIn(("content_block_start", "text", 1), kinds)
        self.assertEqual(text.count(TAG), 6)                    # the thinking is tagged, the answer is not
        self.assertEqual(kinds[-1][0], "message_stop")
        self.assertTrue(m.log(1)[-1]["witnesses"]["anthropic_message_stop"])
        m.control({"once": {"fault": "F0T", "match": "RUNu", "tag": TAG}})
        text, done = m.post("/v1/responses", {"model": "m", "stream": True, "input": [{"role": "user", "content": "RUNu"}]})
        self.assertTrue(done and "response.completed" in text and text.count(TAG) >= 6 and "【P24】" in text)

    def test_structured_title_requests_on_every_endpoint(self):
        # pilot 2026-11-16: codex's title request on /v1/responses crashed the phase-5 mock
        m = self.mock()
        fmt = {"format": {"type": "json_schema", "name": "t", "schema": {}}}
        bodies = (("/v1/responses", {"model": "m", "stream": True, "input": [{"role": "user", "content": "x"}], "text": fmt}),
                  ("/v1/chat/completions", cc("x", structured=True)),
                  ("/v1/messages", {"model": "m", "stream": True, "messages": [{"role": "user", "content": "x"}],
                                    "output_format": {"type": "json_schema", "schema": {}}}))
        for path, body in bodies:
            text, done = m.post(path, body)
            self.assertTrue(done, path)
            self.assertIn("流式输出完整性报告", json.loads(json.dumps(text)), path)
        self.assertEqual([e["aux"] for e in m.log(3)], [True, True, True])
        with urllib.request.urlopen(f"{m.base}/health", timeout=5) as r:   # still alive
            self.assertTrue(json.load(r)["ok"])

    def test_aux_match_marks_a_plain_title_request(self):
        # deepseek-harness asks for its session title in plain text, carrying the run's mark
        m = self.mock()
        title = "Create a concise title for an AI coding-assistant session"
        m.control({"aux_match": [title], "once": {"fault": "F1", "match": "RUNd", "tag": TAG}})
        text, done = m.post("/v1/chat/completions", {"model": "m", "stream": True, "messages": [
            {"role": "system", "content": title}, {"role": "user", "content": "RUNd"}]})
        self.assertTrue(done and "流式输出完整性报告" in text and "【P" not in text)   # served as auxiliary
        text, done = m.post("/v1/chat/completions", cc("RUNd"))                       # the main answer gets the fault
        self.assertFalse(done)
        rows = m.log(2)
        self.assertEqual([(r["aux"], r["aux_reason"], r["fault"]) for r in rows], [(True, "marker", "F0"), (False, None, "F1")])
        m.control({"reset": True})
        self.assertEqual(m.control()["aux_match"], [])

    def test_f5_tags_its_thinking(self):
        m = self.mock()
        m.control({"once": {"fault": "F5", "match": "RUNf5", "tag": TAG}})
        text, done = m.post("/v1/messages", {"model": "m", "stream": True, "messages": [{"role": "user", "content": "RUNf5"}]})
        self.assertTrue(done and '"max_tokens"' in text and text.count(TAG) == 6 and "【P01】" not in text)

    def test_refuses_unsafe_starts(self):
        env = {"PATH": os.environ.get("PATH", ""), "MOCK_CONTROL_TOKEN": "x" * 20}
        logdir = self.tmp / "busy"
        logdir.mkdir()
        (logdir / "delivery.jsonl").write_text("{}\n")
        for args, e in ((["--logdir", str(logdir)], env),                                  # reused logdir
                        (["--logdir", str(self.tmp / "a"), "--host", "0.0.0.0"], env),     # non-loopback
                        (["--logdir", str(self.tmp / "b")], {"PATH": env["PATH"]})):       # no token
            r = subprocess.run([NODE, str(SR / "mock.mjs"), "--port", "0", *args], env=e, capture_output=True, timeout=10)
            self.assertEqual(r.returncode, 2, args)


# ---------------- version witness ----------------
import version_witness  # noqa: E402


class VersionWitness(unittest.TestCase):
    def test_npm_launcher_is_followed_to_the_native_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "lib" / "node_modules" / "@openai" / "codex"
            (pkg / "bin").mkdir(parents=True)
            (pkg / "bin" / "codex.js").write_text("#!/usr/bin/env node\nconsole.log('launcher')\n")
            native = pkg / "node_modules" / "@openai" / "codex-darwin-arm64" / "vendor" / "aarch64-apple-darwin" / "bin" / "codex"
            native.parent.mkdir(parents=True)
            native.write_bytes(b"\xcf\xfa\xed\xfe native v1")
            (root / "bin").mkdir()
            (root / "bin" / "codex").symlink_to(pkg / "bin" / "codex.js")
            info = version_witness.resolve_executed(str(root / "bin" / "codex"), key=("darwin", "arm64"))
            self.assertEqual(info["shebang"], "/usr/bin/env node")
            self.assertEqual(info["native"]["path"], os.path.realpath(native))
            self.assertEqual(info["native"]["sha256"], hashlib.sha256(native.read_bytes()).hexdigest())
            before = {"tools": {"codex": {**info, "version": "0.169.0"}}, "files": {}, "runtime": {}}
            native.write_bytes(b"\xcf\xfa\xed\xfe native v2")  # same launcher, swapped native binary
            after_info = version_witness.resolve_executed(str(root / "bin" / "codex"), key=("darwin", "arm64"))
            after = {"tools": {"codex": {**after_info, "version": "0.169.0"}}, "files": {}, "runtime": {}}
            diffs = version_witness.compare(before, after)
            self.assertEqual(len(diffs), 1)
            self.assertIn("codex.native", diffs[0])

    def test_plain_binary_is_its_own_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "claude"
            exe.write_bytes(b"\xcf\xfa\xed\xfe")
            info = version_witness.resolve_executed(str(exe))
            self.assertEqual(info["native"]["sha256"], info["realpath_sha256"])


# ---------------- public export ----------------
import export_public  # noqa: E402


class PublicExport(unittest.TestCase):
    def make_src(self, root: Path) -> Path:
        src = root / "evidence"
        run = src / "runs" / "claude" / "F1-once" / "run-1-RUNabc"
        run.mkdir(parents=True)
        (run / "record.json").write_text(json.dumps({"cwd": str(src / "cwd" / "claude"), "who": "a.person@example.org"}))
        (run / "final-view.txt").write_text(f" Claude Code v2.1.282\n {src}/cwd/claude\n")
        (run / "raw.bin").write_bytes(b"\x1b[?1049h" + str(src).encode())
        (run / "requests").mkdir()
        (run / "requests" / "req-1.json").write_text('{"system": "synthetic system prompt", "tools": [{"input_schema": {}}]}')
        (src / "homes" / "claude").mkdir(parents=True)
        (src / "homes" / "claude" / ".claude.json").write_text('{"userID": "abc"}')
        (src / "summary.md").write_text("# s\n")
        return src

    def test_copy_is_redacted_and_the_source_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.make_src(Path(tmp))
            before = export_public.manifest(src)
            dst = Path(tmp) / "public"
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(dst)]), 0)
            self.assertEqual(export_public.manifest(src), before)
            copied = sorted(str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file())
            self.assertEqual(copied, ["EXPORT.md", "runs/claude/F1-once/run-1-RUNabc/final-view.txt",
                                      "runs/claude/F1-once/run-1-RUNabc/record.json", "summary.md"])
            record = (dst / "runs/claude/F1-once/run-1-RUNabc/record.json").read_text()
            self.assertIn("<EVIDENCE_ROOT>/cwd/claude", record)
            self.assertIn("<EMAIL>", record)
            self.assertNotIn(str(src), (dst / "runs/claude/F1-once/run-1-RUNabc/final-view.txt").read_text())

    def test_leftover_forbidden_string_fails_the_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.make_src(Path(tmp))
            (src / "summary.md").write_text("see /Users/someone-else/notes\n")
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(Path(tmp) / "public")]), 1)

    def test_a_leaked_request_body_or_private_word_fails_the_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.make_src(Path(tmp))
            run = src / "runs" / "claude" / "F1-once" / "run-1-RUNabc"
            (run / "stdout.txt").write_text('{"system": "synthetic system prompt"}')  # body in an exported name
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(Path(tmp) / "p1")]), 1)
            (run / "stdout.txt").write_text("plain output mentioning projectx\n")
            deny = Path(tmp) / "private-deny.txt"
            deny.write_text("# private names\n(?i)\\bprojectx\\b\n")
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(Path(tmp) / "p2"),
                                                 "--deny-file", str(deny)]), 1)
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(Path(tmp) / "p3")]), 0)

    def test_refuses_a_non_empty_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self.make_src(Path(tmp))
            dst = Path(tmp) / "public"
            dst.mkdir()
            (dst / "keep.txt").write_text("x")
            self.assertEqual(export_public.main(["--src", str(src), "--dst", str(dst)]), 2)


# ---------------- the pre-dispatch card gate (card_gate.py, runner.py matrix) ----------------
PHASE4_CARD = ROOT / "cards" / "phase4-stream-retry.json"
CELL = "claude|interactive|F1-once"


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True)


class CardGate(unittest.TestCase):
    """A matrix starts only when a committed card's plan and budget cover it. The frozen
    phase-4 card is the fixture: hosts claude and codex, six arms x 3 runs, max_runs 48."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rq-gate-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        self.card = json.loads(PHASE4_CARD.read_text(encoding="utf-8"))
        self.card_path = self.repo / "card.json"
        self.card_path.write_text(json.dumps(self.card), encoding="utf-8")
        git(self.repo, "add", "card.json")
        git(self.repo, "commit", "-q", "-m", "freeze card")
        self.sha = hashlib.sha256(self.card_path.read_bytes()).hexdigest()
        self.out = self.tmp / "out"
        self.out.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def manifest(self, name: str, **fields) -> None:
        body = {"label": name, "mode": "interactive", "tools": ["claude"], "conditions": ["F1-once"], "runs": 3,
                "card_sha256": self.sha}
        body.update(fields)
        (self.out / f"manifest-{name}.json").write_text(json.dumps(body), encoding="utf-8")

    def check(self, tools=("claude",), conditions=("F1-once",), runs=3, mode="interactive", deviation=None, card=None):
        return card_gate.check(card or self.card, self.sha, self.out, list(tools), mode, list(conditions), runs,
                               deviation)

    def run_runner(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SR / "runner.py"), "matrix", "--out", str(self.out),
                               "--tools", "fake", "--bin", f"fake={FIX / 'fake_tui.py'}", *extra],
                              capture_output=True, text=True, timeout=60)

    # provenance: git dates the freeze
    def test_committed_card_records_its_commit(self):
        prov = card_gate.card_provenance(self.card_path)
        self.assertEqual(prov["path"], "card.json")
        self.assertRegex(prov["commit"], r"^[0-9a-f]{40}$")
        self.assertIsNone(prov["upstream"])
        self.assertIsNone(prov["pushed"])

    def test_uncommitted_change_is_refused(self):
        self.card_path.write_text(self.card_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(card_gate.GateError, "not committed"):
            card_gate.card_provenance(self.card_path)

    def test_untracked_or_loose_card_is_refused(self):
        draft = self.repo / "draft.json"
        draft.write_text("{}", encoding="utf-8")
        loose = self.tmp / "loose.json"
        loose.write_text("{}", encoding="utf-8")
        for path in (draft, loose):
            with self.assertRaisesRegex(card_gate.GateError, "not tracked"):
                card_gate.card_provenance(path)

    def test_pushed_tracks_whether_upstream_has_the_card_commit(self):
        remote = self.tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-q", "-u", "origin", "HEAD")
        self.assertTrue(card_gate.card_provenance(self.card_path)["pushed"])
        self.card_path.write_text(json.dumps(self.card, indent=1), encoding="utf-8")
        git(self.repo, "commit", "-q", "-am", "edit the card after the push")
        self.assertFalse(card_gate.card_provenance(self.card_path)["pushed"])

    # plan and budget
    def test_a_fresh_plan_inside_the_card_passes(self):
        gate = self.check(tools=("claude", "codex"), conditions=("F0-pre", "F0-tag", "F1-once"))
        self.assertEqual((gate["dispatched_before"], gate["this_matrix"], gate["max_runs"]), (0, 18, 48))
        self.assertEqual(gate["beyond_plan"], [])
        self.assertRegex(gate["validator_sha256"], r"^[0-9a-f]{64}$")

    def test_an_invalid_card_is_refused(self):
        broken = json.loads(json.dumps(self.card))
        del broken["budget"]
        with self.assertRaisesRegex(card_gate.GateError, "does not validate"):
            self.check(card=broken)

    def test_tools_and_conditions_must_be_in_the_card(self):
        with self.assertRaisesRegex(card_gate.GateError, r"hosts\[\]\.name: kimi"):
            self.check(tools=("kimi",))
        with self.assertRaisesRegex(card_gate.GateError, r"arms\[\]\.id: F2-once"):
            self.check(conditions=("F2-once",))

    def test_runs_beyond_the_plan_need_a_recorded_deviation(self):
        with self.assertRaisesRegex(card_gate.GateError, "--deviation"):
            self.check(runs=4)
        gate = self.check(runs=4, deviation="supplementary run after the FLONG fix")
        self.assertEqual(len(gate["beyond_plan"]), 1)
        self.assertIn(CELL, gate["beyond_plan"][0])

    def test_earlier_manifests_count_toward_the_cell(self):
        self.manifest("a", dispatched={CELL: 3})
        with self.assertRaisesRegex(card_gate.GateError, "beyond the card's plan"):
            self.check(runs=1)
        self.check(conditions=("F6-once",), runs=3)

    def test_an_invalid_run_buys_one_replacement(self):
        self.manifest("a", dispatched={CELL: 3}, invalid={CELL: 1})
        self.check(runs=1)
        with self.assertRaises(card_gate.GateError):
            self.check(runs=2)
        strict = json.loads(json.dumps(self.card))
        strict["sampling"]["invalid_reruns"] = 0
        with self.assertRaises(card_gate.GateError):
            self.check(runs=1, card=strict)

    def test_replacements_stop_at_one_per_planned_run(self):
        self.manifest("a", dispatched={CELL: 6}, invalid={CELL: 6})
        with self.assertRaisesRegex(card_gate.GateError, "beyond the card's plan"):
            self.check(runs=1)

    def test_budget_spans_invocations_and_a_deviation_cannot_lift_it(self):
        self.manifest("a", tools=["codex"], conditions=["F0-pre"], dispatched={"codex|interactive|F0-pre": 46})
        with self.assertRaisesRegex(card_gate.GateError, "budget.max_runs=48: 46"):
            self.check(runs=3, deviation="just this once")
        self.assertEqual(self.check(runs=2)["dispatched_before"], 46)

    def test_a_manifest_without_counts_is_charged_its_whole_plan(self):
        self.manifest("legacy")
        with self.assertRaisesRegex(card_gate.GateError, "beyond the card's plan"):
            self.check(runs=1)

    def test_manifests_of_another_card_are_not_counted(self):
        self.manifest("other", card_sha256="0" * 64, dispatched={CELL: 40})
        self.check(runs=3)

    def test_a_tool_runs_in_no_more_modes_than_the_card_has_hosts(self):
        self.manifest("a", dispatched={CELL: 3})
        with self.assertRaisesRegex(card_gate.GateError, "2 modes"):
            self.check(mode="noninteractive")

    def test_an_unreadable_manifest_stops_the_accounting(self):
        (self.out / "manifest-bad.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(card_gate.GateError, "manifest-bad.json"):
            self.check()

    # the runner applies the gate before anything is started or written
    def test_runner_refuses_a_matrix_without_card_or_reason(self):
        r = self.run_runner()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("needs --card", r.stderr)
        self.assertEqual(list(self.out.glob("manifest-*.json")), [])

    def test_runner_refuses_card_and_exploratory_together(self):
        r = self.run_runner("--card", str(self.card_path), "--exploratory", "calibration")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("mutually exclusive", r.stderr)

    def test_runner_refuses_a_card_that_does_not_cover_the_matrix(self):
        r = self.run_runner("--card", str(self.card_path), "--conditions", "F1-once")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("card gate:", r.stderr)
        self.assertIn("hosts[].name: fake", r.stderr)
        self.assertEqual(list(self.out.glob("manifest-*.json")), [])


class Summary(unittest.TestCase):
    """summary.md prints the one-sided Wilson bounds next to every count and says whether
    the matrix was pre-registered."""

    def test_wilson_matches_the_numbers_in_measurement_md(self):
        self.assertAlmostEqual(summarize.wilson(9, 10)[0], 0.65, places=2)  # measurement.md example
        self.assertAlmostEqual(summarize.wilson(3, 3)[0], 0.526, places=3)
        self.assertEqual(summarize.wilson(3, 3)[1], 1.0)
        self.assertEqual(summarize.wilson(0, 8)[0], 0.0)
        self.assertAlmostEqual(summarize.wilson(0, 8)[1], 0.253, places=3)

    def test_invalid_and_na_leave_the_denominator(self):
        counts = Counter({"retracted": 2, "invalid": 1, "n/a": 1})
        self.assertEqual(summarize.bounds_text(counts, 4), "retracted 2/2：0.42–1.00")
        self.assertEqual(summarize.bounds_text(Counter({"invalid": 3}), 3), "—")

    def write_root(self, root: Path, manifest: dict) -> str:
        (root / "manifest-m1.json").write_text(json.dumps(manifest), encoding="utf-8")
        rows = [{"tool": "claude", "condition": "F1-once", "run_index": i, "verdict": v, "verdict_reason": "x",
                 "requests": [], "fields": {}} for i, v in enumerate(["retracted", "retracted", "invalid"], 1)]
        (root / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        self.assertEqual(summarize.main([str(root)]), 0)
        return (root / "summary.md").read_text(encoding="utf-8")

    def test_exploratory_matrix_is_marked_not_preregistered(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = self.write_root(Path(tmp), {"label": "m1", "preregistered": False, "exploratory": "calibration",
                                               "dispatched": {CELL: 3}, "invalid": {CELL: 1}})
        self.assertIn("预注册：否，探索性运行（calibration）", text)
        self.assertIn("retracted 2/2：0.42–1.00", text)

    def test_preregistered_matrix_shows_card_commit_budget_and_deviation(self):
        manifest = {"label": "m1", "preregistered": True, "deviation": "supplementary F1 run",
                    "card_git": {"path": "examples/card.json", "commit": "ab" * 20, "committed_at": "2026-11-21T09:00:00+08:00",
                                 "pushed": False},
                    "gate": {"dispatched_before": 3, "this_matrix": 3, "max_runs": 48, "beyond_plan": [f"{CELL}: 3 + 3 > 3"]},
                    "dispatched": {CELL: 3}}
        with tempfile.TemporaryDirectory() as tmp:
            text = self.write_root(Path(tmp), manifest)
        self.assertIn("commit abababababab", text)
        self.assertIn("没有推送到上游", text)
        self.assertIn("此前 3 次，本矩阵 3 次（最多 3 次），预算 max_runs 48", text)
        self.assertIn("偏离：supplementary F1 run", text)

    def test_legacy_manifest_says_it_has_no_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = self.write_root(Path(tmp), {"label": "m1"})
        self.assertIn("预注册：manifest 没有记录", text)


# ---------------- end to end against the fake TUI (needs node, tmux, sandbox-exec) ----------------
@unittest.skipUnless(NODE and TMUX and Path("/usr/bin/sandbox-exec").exists(), "node/tmux/sandbox-exec not available")
class FakeTuiEndToEnd(unittest.TestCase):
    """Calibrates the whole witness chain: the same F1-once fault must read as retracted
    when the subject drops the partial, as fork when it keeps it, and a subject that
    renders a healthy answer twice must fail the healthy control."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="rq-e2e-"))
        cls.base = [sys.executable, str(SR / "runner.py")]
        cls.common = ["--tools", "fake", "--bin", f"fake={FIX / 'fake_tui.py'}", "--settle-s", "1",
                      "--followup-s", "15", "--tmux-height", "120"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_matrix(self, out: Path, mode: str, conditions: str, ui: str = "interactive") -> list[dict]:
        if ui == "interactive" and not (out / "probes" / "fake.json").exists():
            r = subprocess.run(self.base + ["probe", "--out", str(out), "--fake-mode", mode] + self.common,
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = subprocess.run(self.base + ["matrix", "--out", str(out), "--fake-mode", mode, "--mode", ui,
                                        "--conditions", conditions, "--runs", "1",
                                        "--exploratory", "fake-TUI calibration"] + self.common,
                           capture_output=True, text=True, timeout=300)
        self.assertIn(r.returncode, (0, 3), r.stdout + r.stderr)
        name = "runs.jsonl" if ui == "interactive" else "runs-noninteractive.jsonl"
        rows = [json.loads(x) for x in (out / name).read_text().splitlines()]
        manifest = json.loads(sorted(out.glob("manifest-*.json"))[-1].read_text())
        self.assertFalse(manifest["preregistered"])
        self.assertEqual(manifest["exploratory"], "fake-TUI calibration")
        self.assertEqual(sum(manifest["dispatched"].values()), len(rows))
        return rows

    def test_retract_keep_double(self):
        rows = self.run_matrix(self.tmp / "retract", "retract", "F0-pre,F0-tag,F1-once")
        self.assertEqual([r["verdict"] for r in rows], ["healthy", "tag_visible", "retracted"],
                         [r["verdict_reason"] for r in rows])
        f1 = rows[-1]
        self.assertTrue(f1["checks"]["shown_mid"] or f1["checks"]["shown_raw"])
        self.assertTrue(f1["display"]["final_complete"])
        self.assertIn("Retrying (1/3)", " ".join(f1["notices_raw"]))
        self.assertFalse(f1["next_request"]["carries_tag"])
        self.assertTrue(f1["executed"]["path"].endswith(("python3", "Python")) or "python" in f1["executed"]["path"].lower())

        keep = self.run_matrix(self.tmp / "keep", "keep", "F1-once")
        self.assertEqual(keep[-1]["verdict"], "fork", keep[-1]["verdict_reason"])
        self.assertTrue(keep[-1]["next_request"] is None or not keep[-1]["next_request"]["carries_tag"])

        double = self.run_matrix(self.tmp / "double", "double", "F0-pre")
        self.assertEqual(double[-1]["verdict"], "control_failed")

    def test_noninteractive_append_only(self):
        rows = self.run_matrix(self.tmp / "print", "retract", "F0-pre,F1-once", ui="noninteractive")
        self.assertEqual([r["verdict"] for r in rows], ["healthy", "fork"], [r["verdict_reason"] for r in rows])
        self.assertEqual(rows[-1]["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
