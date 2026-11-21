"""Tests for witness/stall (phase 6): the frozen verdict table, the plan/card
alignment, the Wilson helper, and a calibration of the two clocks the matrix
reads (time to the input box, echo lag of keys typed into a blocked prompt)
against a fake TUI with known delays.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = ROOT / "witness" / "stall"
sys.path.insert(0, str(WS))
import fakes  # noqa: E402
import stall  # noqa: E402

FAKE = ROOT / "tests" / "fixtures" / "stall" / "fake_subject.py"
CARD = ROOT / "examples" / "experiment-card-phase6-metacodes-stall.json"


class PlanTests(unittest.TestCase):
    def test_every_arm_has_a_runner_and_a_group(self):
        self.assertEqual(set(stall.ARMS), set(stall.DISPATCH))
        self.assertTrue(set(stall.ARMS.values()) <= {"baseline", "pool", "precise", "post"})

    def test_every_verdict_maps_to_known_fields(self):
        for verdict, fields in stall.VERDICTS.items():
            self.assertEqual(len(fields), 5, verdict)
            self.assertIn(fields[4], (None, "L0", "L1", "L2", "L3"), verdict)

    def test_card_arms_match_the_witness(self):
        if not CARD.exists():
            self.skipTest("phase-6 card not written yet")
        card = json.loads(CARD.read_text(encoding="utf-8"))
        self.assertEqual({a["id"] for a in card["arms"]}, set(stall.ARMS))
        self.assertEqual({h["name"] for h in card["hosts"]}, {stall.HOST})

    def test_wilson_bounds(self):
        lo, hi = stall.wilson(3, 3)
        self.assertAlmostEqual(lo, 0.53, places=2)
        self.assertEqual(hi, 1.0)
        lo, hi = stall.wilson(0, 3)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.47, places=2)


class ClockCalibration(unittest.TestCase):
    """The fake TUI's delays are known, so the witness must read them back."""

    def run_fake(self, start_delay, freeze_on, freeze_s):
        p = fakes.Pty([sys.executable, str(FAKE), str(start_delay), freeze_on, str(freeze_s)],
                      {"PATH": "/usr/bin:/bin", "TERM": "xterm-256color"}, str(ROOT))
        try:
            t_box = p.wait_for(stall.BOX, 10)
            self.assertIsNotNone(t_box)
            box_s = t_box - p.t0
            time.sleep(0.3)
            p.type("/mode", gap=0.05)
            p.write(b"l")
            time.sleep(0.2)
            t_q = p.write(b"q")
            t_echo = p.wait_for(b"/modelq", 10)
            self.assertIsNotNone(t_echo)
            p.type("\x15", gap=0.01)
            return box_s, t_echo - t_q, p
        finally:
            p.write(b"\r")
            p.kill()

    def test_start_delay_is_read_back(self):
        box_s, lag, _ = self.run_fake(1.0, "", 0)
        self.assertGreaterEqual(box_s, 1.0)
        self.assertLess(box_s, 1.6)
        self.assertLess(lag, 0.3)

    def test_blocked_prompt_is_read_as_echo_lag(self):
        _, lag, _ = self.run_fake(0.0, "/model", 2.0)
        self.assertGreaterEqual(lag, 1.6)
        self.assertLess(lag, 2.5)


class ServerTests(unittest.TestCase):
    def test_gateway_holds_and_logs(self):
        g = fakes.Gateway(models_delay=0.3)
        try:
            t = time.monotonic()
            out = subprocess.run(["curl", "-s", "http://127.0.0.1:%d/v1/models" % g.port], capture_output=True, timeout=10)
            self.assertIn(b"claude-sonnet", out.stdout)
            self.assertGreaterEqual(time.monotonic() - t, 0.3)
            self.assertEqual([e[1] for e in g.events], ["GET", "ANSWERED"])
        finally:
            g.stop()

    def test_silent_listener_accepts_and_never_answers(self):
        s = fakes.Silent()
        try:
            out = subprocess.run(["curl", "-s", "-m", "1", "http://127.0.0.1:%d/" % s.port], capture_output=True, timeout=10)
            self.assertNotEqual(out.returncode, 0)
            self.assertEqual(len(s.accepts), 1)
            self.assertGreater(s.bytes_in, 0)
        finally:
            s.stop()


if __name__ == "__main__":
    unittest.main()
