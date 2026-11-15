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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR = ROOT / "witness" / "stream-retry"
FIX = ROOT / "tests" / "fixtures" / "stream-retry"
sys.path.insert(0, str(SR))

import grading  # noqa: E402

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
    ok = ending == "clean" and fault == "F0"
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
        self.assertEqual(r["fields"], {"detected": True, "contained": True, "recovered": True})

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


class Bodies(unittest.TestCase):
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
                                        "--conditions", conditions, "--runs", "1"] + self.common,
                           capture_output=True, text=True, timeout=300)
        self.assertIn(r.returncode, (0, 3), r.stdout + r.stderr)
        name = "runs.jsonl" if ui == "interactive" else "runs-noninteractive.jsonl"
        return [json.loads(x) for x in (out / name).read_text().splitlines()]

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
