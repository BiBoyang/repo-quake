#!/usr/bin/env python3
"""witness/stall: what a CLI does while a dependency it waits on has stalled.

  stall.py probe      --out ROOT --bin BIN [--gopls PATH]
  stall.py matrix     --out ROOT --bin BIN --card CARD [--arms A,B] [--runs 3] [--parallel 5]
  stall.py summarize  --out ROOT
  stall.py egress     --out ROOT --start "YYYY-MM-DD HH:MM:SS" --end "..."
  stall.py lsregister --out ROOT
  stall.py export     --src ROOT --dst runs/<phase-dir>

Every run starts the subject from an `env -i` allowlist with a fresh HOME, state dir
and working directory inside the evidence root, under a sandbox-exec profile that
allows outbound connections to localhost only. The dependencies are loopback fakes
(fakes.py) whose request logs are the delivery proof. The frozen rubric is VERDICTS
below and README.md (判定). stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import fakes  # noqa: E402

SB_PROFILE = """(version 1)
(allow default)
(deny network-outbound)
(allow network-outbound (remote ip "localhost:*"))
(allow network-outbound (remote unix-socket))
"""
BOX = b'Try "fix typecheck errors"'
BANNER = b"metacodes v"
PY = sys.executable
HOST = "metacodes"
MODE = "tui"
Z = 1.645
KG_BUILD = "sha256:" + "0" * 64

# Arms, in dispatch order. group: baseline runs first and must pass; pool arms
# spend most of their time waiting and may run concurrently; precise arms run one
# at a time after the pool; post runs last.
ARMS = {
    "C0-pre": "baseline", "P-splash": "baseline", "P-stdio5-exit": "baseline",
    "S-models-5s": "pool", "S-models-stall": "pool", "S-models-warm": "pool", "S-kg-stall": "pool",
    "K-keys-5s": "pool", "K-keys-stall": "pool",
    "M-stdio-stall": "pool", "M-stdio-stall-esc": "pool", "M-http-delete-stall": "pool",
    "M-https-tls-stall": "pool", "E-otlp-stall": "pool",
    "T-edit-silent-lsp": "pool",
    "K-keys-0s": "precise", "T-edit-nolsp": "precise", "T-edit-gopls": "precise",
    "T-bash-mixed-1": "precise", "T-bash-mixed-20k": "precise",
    "C0-post": "post",
}

# Frozen mapping verdict -> five observation fields and level (README.md, 判定).
# None means the field is not observed for that verdict.
VERDICTS = {
    "healthy": (None, None, None, None, None),
    "startup_floor_seen": (None, None, None, None, None),
    "freeze_seen": (None, None, None, None, None),
    "responsive": (None, None, None, None, None),
    "no_wait": (None, None, True, True, None),
    "startup_waited": (False, False, False, True, "L0"),
    "startup_blocked": (False, False, False, False, "L0"),
    "startup_waited_kg": (True, False, False, True, "L1"),
    "prompt_frozen": (False, False, False, True, "L0"),
    "frozen_until_watchdog": (False, False, False, False, "L0"),
    "first_message_waited_timeout": (True, True, True, True, "L3"),
    "interruptible": (True, True, True, True, "L3"),
    "exit_blocked": (False, False, False, False, "L0"),
    "unbounded": (False, True, False, False, "L1"),
    "exit_paid_per_server": (None, None, None, None, None),
    "exit_waited_export": (True, False, False, True, "L1"),
    "edit_waited_both_limits": (True, False, False, True, "L1"),
    "first_edit_pays": (None, None, None, None, None),
    "floor_seen": (None, None, None, None, None),
    "observation_paid": (None, None, None, None, None),
    "other": (None, None, None, None, None),
    "control_failed": (None, None, None, None, None),
    "invalid": (None, None, None, None, None),
}
FIELDS = ("detected", "reported", "contained", "recovered")


class Invalid(Exception):
    """The run cannot be graded for its arm (setup, harness, pinned binary)."""


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_card_gate():
    spec = importlib.util.spec_from_file_location("quake_card_gate", HERE.parent / "stream-retry" / "card_gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wilson(k: int, n: int, z: float = Z):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


class Ctx:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out).resolve()
        self.bin = Path(args.bin).resolve() if getattr(args, "bin", None) else None
        self.rg = Path(args.rg).resolve() if getattr(args, "rg", None) else None
        self.gopls = Path(args.gopls).resolve() if getattr(args, "gopls", None) else None
        self.sb = self.out / "loopback.sb"
        self.lock = threading.Lock()


# ---------------------------------------------------------------- one run


class Run:
    def __init__(self, ctx: Ctx, arm: str, index: int):
        self.ctx, self.arm, self.index = ctx, arm, index
        self.run_id = secrets.token_hex(6)
        self.dir = ctx.out / "runs" / arm / ("run-%d-%s" % (index, self.run_id))
        for sub in ("home", "state", "work", "srv"):
            (self.dir / sub).mkdir(parents=True, exist_ok=True)
        self.servers = []
        self.p: fakes.Pty | None = None
        self.rec = {"arm": arm, "index": index, "run_id": self.run_id, "host": HOST, "mode": MODE}

    def stage(self, name: str, neutral: str) -> str:
        dst = self.dir / "srv" / neutral
        shutil.copyfile(HERE / "srv" / name, dst)
        return str(dst)

    def env(self, extra=None) -> dict:
        env = {
            "HOME": str(self.dir / "home"), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "xterm-256color",
            "TMPDIR": "/tmp", "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "FORCE_COLOR": "1", "BROWSER": "true",
            "METACODES_LOG": "*:debug", "METACODES_LOG_FILE": str(self.dir / "subject.log"),
            "METASK_API_KEY": "stall-dummy-key", "METACODES_KG_AUTOSTART": "0",
            "METACODES_NO_STARTUP_ANIMATION": "1", "METACODES_JEV_URL": "off",
        }
        if self.ctx.rg:
            env["RG_BIN"] = str(self.ctx.rg)
        for k, v in (extra or {}).items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
        return env

    def launch(self, base_url: str, extra=None, args=None, rows=30, cols=100, state=None) -> fakes.Pty:
        argv = ["/usr/bin/sandbox-exec", "-f", str(self.ctx.sb), str(self.ctx.bin),
                "--state-dir", str(state or (self.dir / "state")), "--permission", "bypassPermissions",
                "--base-url", base_url] + list(args or [])
        self.p = fakes.Pty(argv, self.env(extra), str(self.dir / "work"), rows, cols)
        self.rec.setdefault("launches", []).append({"argv_tail": argv[3:], "t0": round(self.p.t0, 3)})
        self.check_binary(self.p)
        return self.p

    def check_binary(self, p: fakes.Pty) -> None:
        """lsof on the subject's pid until the pinned binary is mapped as its text
        (sandbox-exec execs it in place), at most 3 s."""
        want = os.path.realpath(str(self.ctx.bin))
        seen = []
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            r = subprocess.run(["lsof", "-a", "-p", str(p.pid), "-d", "txt", "-Fn"], capture_output=True, text=True)
            seen = [line[1:] for line in r.stdout.splitlines() if line.startswith("n")]
            if any(os.path.realpath(x) == want for x in seen):
                self.rec.setdefault("lsof_executable", []).append(want)
                return
            time.sleep(0.05)
        self.rec["lsof_txt_seen"] = seen[:4]
        raise Invalid("the pinned binary was not the subject's executable (lsof)")

    def box(self, p: fakes.Pty, timeout: float):
        return p.wait_for(BOX, timeout)

    def turn(self, p: fakes.Pty, gateway: fakes.Gateway, wait=10.0):
        time.sleep(0.4)
        p.type("hi", gap=0.08)
        time.sleep(0.3)
        mark = p.size()
        t_enter = p.write(b"\r")
        t_reply = p.wait_for(b"pong-ok", wait, start=mark)
        return t_enter, t_reply, mark

    def exit(self, p: fakes.Pty, cap: float):
        p.write(b"\x15")
        time.sleep(0.2)
        p.type("/exit", gap=0.05)
        time.sleep(0.2)
        t_enter = p.write(b"\r")
        t_exit = p.wait_exit(cap)
        return t_enter, t_exit

    def finish(self):
        p = self.p
        if p is not None:
            if not p.poll_exit():
                p.kill()
            else:
                try:
                    os.close(p.fd)
                except OSError:
                    pass
            (self.dir / "raw.bin").write_bytes(bytes(p.buf))
            with open(self.dir / "raw-index.jsonl", "w") as f:
                for t, size in p.chunks:
                    f.write(json.dumps({"t": round(t - p.t0, 4), "size": size}) + "\n")
            with open(self.dir / "writes.jsonl", "w") as f:
                for t, data, note in p.writes:
                    f.write(json.dumps({"t": round(t - p.t0, 4), "data": data, "note": note}) + "\n")
        for server in self.servers:
            try:
                server.stop()
            except Exception:
                pass
        if self.arm.startswith("T-bash"):
            shutil.rmtree(self.dir / "work", ignore_errors=True)


def rel(p, t):
    return None if t is None or p is None else round(t - p.t0, 3)


def gateway(run: Run, **kw) -> fakes.Gateway:
    g = fakes.Gateway(**kw)
    run.servers.append(g)
    return g


def silent(run: Run) -> fakes.Silent:
    s = fakes.Silent()
    run.servers.append(s)
    return s


def write_config(run: Run, servers: dict) -> None:
    (run.dir / "state" / "config.json").write_text(json.dumps({"mcpServers": servers}), encoding="utf-8")


def delivery(run: Run, g: fakes.Gateway | None, t0: float):
    if g is not None:
        run.rec["gateway_events"] = [(round(t - t0, 3), m, path) for t, m, path in list(g.events)]


# ---------------------------------------------------------------- arms


def arm_c0(run: Run):
    g = gateway(run)
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_enter, t_reply, _ = run.turn(p, g)
    t_exit_cmd, t_exit = run.exit(p, 10)
    r = run.rec
    r.update(box_s=rel(p, t_box), reply_after_enter_s=None if t_reply is None else round(t_reply - t_enter, 3),
             exit_s=None if t_exit is None else round(t_exit - t_exit_cmd, 3))
    delivery(run, g, p.t0)
    gets = sum(1 for _, m, path in g.events if m == "GET" and path.startswith("/v1/models"))
    posts = sum(1 for _, m, _ in g.events if m == "POST")
    r.update(models_gets=gets, posts=posts)
    ok = r["box_s"] <= 2.0 and r["reply_after_enter_s"] is not None and r["reply_after_enter_s"] <= 3.0 \
        and r["exit_s"] is not None and r["exit_s"] <= 1.0 and gets == 1 and posts == 1
    return "healthy" if ok else "control_failed"


def arm_splash(run: Run):
    g = gateway(run)
    p = run.launch(g.url, {"METACODES_NO_STARTUP_ANIMATION": None})
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    run.rec["box_s"] = rel(p, t_box)
    t_exit_cmd, t_exit = run.exit(p, 10)
    delivery(run, g, p.t0)
    return "startup_floor_seen" if 1.4 <= run.rec["box_s"] <= 3.5 else "control_failed"


def arm_models(run: Run, delay, cap: float):
    g = gateway(run, models_delay=delay)
    p = run.launch(g.url)
    t_box = run.box(p, cap)
    t_get = g.first("GET", "/v1/models", after=p.t0)
    run.rec.update(models_delay=delay, box_s=rel(p, t_box), models_get_s=rel(p, t_get))
    if t_get is None:
        raise Invalid("no /v1/models request reached the gateway")
    if t_box is None:
        t_c = p.write(b"\x03")
        t_e = p.wait_exit(5)
        run.rec["ctrl_c_exit_s"] = None if t_e is None else round(t_e - t_c, 3)
        delivery(run, g, p.t0)
        return "startup_blocked"
    t_exit_cmd, t_exit = run.exit(p, 10)
    run.rec["exit_s"] = None if t_exit is None else round(t_exit - t_exit_cmd, 3)
    delivery(run, g, p.t0)
    box = run.rec["box_s"]
    if delay is not None and delay <= box < delay + 2.0:
        return "startup_waited"
    return "other"


def arm_models_warm(run: Run):
    g = gateway(run, models_delay=0.0)
    p0 = run.launch(g.url)
    t_box0 = p0.wait_for(BOX, 10)
    if t_box0 is None:
        raise Invalid("cache-filling start showed no input box")
    run.rec["setup_box_s"] = rel(p0, t_box0)
    run.exit(p0, 10)
    if not p0.poll_exit():
        p0.kill()
    run.rec["setup_events"] = [(round(t - p0.t0, 3), m, path) for t, m, path in list(g.events)]
    g.events.clear()
    g.models_delay = 5.0
    (run.dir / "raw-setup.bin").write_bytes(bytes(p0.buf))
    p = run.launch(g.url)
    t_box = run.box(p, 15)
    if t_box is None:
        raise Invalid("input box never appeared on the warm start")
    run.rec["box_s"] = rel(p, t_box)
    t_get = g.first("GET", "/v1/models", after=p.t0)
    run.rec["models_get_s"] = rel(p, t_get)
    t_exit_cmd, t_exit = run.exit(p, 10)
    run.rec["exit_s"] = None if t_exit is None else round(t_exit - t_exit_cmd, 3)
    delivery(run, g, p.t0)
    if t_get is None:
        raise Invalid("the warm start sent no /v1/models refresh")
    return "no_wait" if run.rec["box_s"] < 2.0 else "other"


def arm_kg(run: Run):
    g = gateway(run)
    kg = silent(run)
    p = run.launch(g.url, {"METACODES_KG_URL": "http://127.0.0.1:%d" % kg.port, "METACODES_KG_API_KEY": "stall-kg-key",
                           "METACODES_KG_EXPECTED_BUILD_ID": KG_BUILD, "METACODES_KG_AUTOSTART": None})
    t_box = run.box(p, 45)
    run.rec.update(box_s=rel(p, t_box), kg_accepts_s=[rel(p, t) for t in kg.accepts], kg_bytes_in=kg.bytes_in)
    if not kg.accepts:
        raise Invalid("the KG listener saw no connection")
    if t_box is None:
        delivery(run, g, p.t0)
        return "other"
    banner = bytes(p.buf)
    run.rec["banner_names_kg"] = b"KG unavailable" in banner
    t_exit_cmd, t_exit = run.exit(p, 10)
    run.rec["exit_s"] = None if t_exit is None else round(t_exit - t_exit_cmd, 3)
    delivery(run, g, p.t0)
    return "startup_waited_kg" if 34.0 <= run.rec["box_s"] < 40.0 else "other"


def type_model_then_zq(p: fakes.Pty):
    time.sleep(0.5)
    p.type("/mode", gap=0.08)
    time.sleep(0.4)
    t_l = p.write(b"l")
    time.sleep(0.3)
    p.write(b" ")
    time.sleep(0.05)
    p.write(b"z")
    time.sleep(0.05)
    t_q = p.write(b"q")
    return t_l, t_q


def arm_keys(run: Run, delay):
    g = gateway(run, models_delay=0.0, keys_delay=delay)
    p = run.launch(g.url, {"METACODE_API_KEYS_URL": "http://127.0.0.1:%d/api/v1/keys" % g.port})
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_l, t_q = type_model_then_zq(p)
    t_echo = p.wait_for(b"zq", 15 if delay is not None else 3)
    t_keys = g.first("GET", "/api/v1/keys", after=p.t0)
    r = run.rec
    r.update(keys_delay=delay, box_s=rel(p, t_box), l_written_s=rel(p, t_l), keys_get_s=rel(p, t_keys),
             q_written_s=rel(p, t_q), echo_s=rel(p, t_echo),
             echo_lag_s=None if t_echo is None else round(t_echo - t_q, 3))
    if t_keys is None:
        raise Invalid("the key list request never reached the gateway")
    if delay is not None:
        t_exit_cmd, t_exit = run.exit(p, 10)
        r["exit_s"] = None if t_exit is None else round(t_exit - t_exit_cmd, 3)
        delivery(run, g, p.t0)
        lag = r["echo_lag_s"]
        if delay == 0.0:
            return "responsive" if lag is not None and lag < 0.5 else "control_failed"
        return "prompt_frozen" if lag is not None and lag >= delay - 1.0 else "other"
    t_c = p.write(b"\x03")
    time.sleep(0.2)
    p.write(b"\x03")
    alive_after_ctrl_c = p.wait_exit(5) is None
    t_term = p.signal(signal.SIGTERM)
    t_dead = p.wait_exit(60)
    r.update(alive_5s_after_ctrl_c=alive_after_ctrl_c,
             sigterm_exit_s=None if t_dead is None else round(t_dead - t_term, 3))
    if p.exit_status is not None and os.WIFSIGNALED(p.exit_status):
        r["killed_by_signal"] = os.WTERMSIG(p.exit_status)
    delivery(run, g, p.t0)
    if t_echo is None and alive_after_ctrl_c and r["sigterm_exit_s"] is not None \
            and 44.0 <= r["sigterm_exit_s"] < 50.0 and r.get("killed_by_signal") == signal.SIGALRM:
        return "frozen_until_watchdog"
    return "other"


def arm_mcp_stdio(run: Run, esc: bool):
    g = gateway(run)
    write_config(run, {"s1": {"command": PY, "args": [run.stage("quiet_mcp.py", "a.py")], "startupTimeoutMs": 5000}})
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    time.sleep(0.4)
    p.type("hi", gap=0.08)
    time.sleep(0.3)
    mark = p.size()
    t_enter = p.write(b"\r")
    t_spin = p.wait_for(b"Connecting to MCP servers", 3, start=mark)
    r = run.rec
    r.update(box_s=rel(p, t_box), enter_s=rel(p, t_enter), spinner_s=rel(p, t_spin))
    if esc:
        while time.monotonic() < t_enter + 1.5:
            time.sleep(0.01)
        t_esc = p.write(b"\x1b")
        t_int = p.wait_for(b"Interrupted", 5, start=mark)
        time.sleep(2.0)
        t_post = g.first("POST", "/v1/messages", after=t_enter)
        r.update(esc_s=rel(p, t_esc), interrupted_after_esc_s=None if t_int is None else round(t_int - t_esc, 3),
                 post_s=rel(p, t_post))
        run.exit(p, 10)
        delivery(run, g, p.t0)
        ok = t_int is not None and t_int - t_esc <= 1.0 and t_post is None
        return "interruptible" if ok else "other"
    deadline = time.monotonic() + 20
    t_post = None
    while t_post is None and time.monotonic() < deadline:
        t_post = g.first("POST", "/v1/messages", after=t_enter)
        time.sleep(0.02)
    t_reply = p.wait_for(b"pong-ok", 10, start=mark)
    r.update(post_s=rel(p, t_post), first_request_wait_s=None if t_post is None else round(t_post - t_enter, 3),
             reply_s=rel(p, t_reply))
    run.exit(p, 10)
    delivery(run, g, p.t0)
    post = r["post_s"]
    if post is not None and 5.0 <= post < 8.0 and r["box_s"] < 2.0:
        return "first_message_waited_timeout"
    return "other"


def arm_mcp_http_delete(run: Run):
    g = gateway(run)
    mcp = fakes.ClassicMcp(delete_answers=False)
    run.servers.append(mcp)
    write_config(run, {"s1": {"type": "http", "url": mcp.url}})
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_enter, t_reply, _ = run.turn(p, g)
    if t_reply is None:
        raise Invalid("the turn before the exit got no reply")
    t_exit_cmd, t_exit = run.exit(p, 35)
    r = run.rec
    r.update(box_s=rel(p, t_box), exit_s=None if t_exit is None else round(t_exit - t_exit_cmd, 3),
             mcp_events=[(rel(p, t), m) for t, m in list(mcp.events)])
    if not any(m == "POST initialize" for _, m in mcp.events):
        raise Invalid("the MCP handshake never reached the server")
    if t_exit is None:
        t_c = p.write(b"\x03")
        time.sleep(0.2)
        p.write(b"\x03")
        r["alive_5s_after_ctrl_c"] = p.wait_exit(5) is None
    delivery(run, g, p.t0)
    deleted = any(m == "DELETE" for _, m in mcp.events)
    return "exit_blocked" if t_exit is None and deleted else "other"


def arm_mcp_https_tls(run: Run):
    g = gateway(run)
    lis = silent(run)
    write_config(run, {"s1": {"type": "http", "url": "https://127.0.0.1:%d/mcp" % lis.port, "startupTimeoutMs": 5000}})
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    time.sleep(0.4)
    p.type("hi", gap=0.08)
    time.sleep(0.3)
    mark = p.size()
    t_enter = p.write(b"\r")
    time.sleep(15.0)
    t_post = g.first("POST", "/v1/messages", after=t_enter)
    t_esc = p.write(b"\x1b")
    t_int = p.wait_for(b"Interrupted", 5, start=mark)
    time.sleep(0.3)
    t_exit_cmd, t_exit = run.exit(p, 35)
    r = run.rec
    r.update(box_s=rel(p, t_box), post_within_15s=t_post is not None,
             interrupted_after_esc_s=None if t_int is None else round(t_int - t_esc, 3),
             exit_s=None if t_exit is None else round(t_exit - t_exit_cmd, 3),
             accepts_s=[rel(p, t) for t in lis.accepts], bytes_in=lis.bytes_in)
    if not lis.accepts:
        raise Invalid("the HTTPS listener saw no connection")
    delivery(run, g, p.t0)
    return "unbounded" if t_post is None and t_exit is None else "other"


def arm_mcp_stdio5_exit(run: Run):
    g = gateway(run)
    script = run.stage("ok_mcp.py", "b.py")
    write_config(run, {"s%d" % i: {"command": PY, "args": [script]} for i in range(1, 6)})
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    time.sleep(1.5)
    t_enter, t_reply, _ = run.turn(p, g)
    if t_reply is None:
        raise Invalid("the turn before the exit got no reply")
    t_exit_cmd, t_exit = run.exit(p, 15)
    run.rec.update(box_s=rel(p, t_box), exit_s=None if t_exit is None else round(t_exit - t_exit_cmd, 3))
    delivery(run, g, p.t0)
    e = run.rec["exit_s"]
    return "exit_paid_per_server" if e is not None and 0.95 <= e < 2.0 else "control_failed"


def arm_otlp(run: Run):
    g = gateway(run)
    col = silent(run)
    p = run.launch(g.url, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:%d" % col.port, "OTEL_EXPORTER_OTLP_TIMEOUT": "2000"})
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_enter, t_reply, _ = run.turn(p, g)
    if t_reply is None:
        raise Invalid("the turn before the exit got no reply")
    time.sleep(0.2)
    t_exit_cmd, t_exit = run.exit(p, 15)
    run.rec.update(box_s=rel(p, t_box), exit_s=None if t_exit is None else round(t_exit - t_exit_cmd, 3),
                   collector_accepts_s=[rel(p, t) for t in col.accepts], collector_bytes_in=col.bytes_in)
    delivery(run, g, p.t0)
    if not col.accepts:
        raise Invalid("the collector saw no connection")
    e = run.rec["exit_s"]
    return "exit_waited_export" if e is not None and 1.5 <= e < 4.0 else "other"


GO_ENV = {"GOPROXY": "off", "GOFLAGS": "-mod=mod", "GOTOOLCHAIN": "local", "GOTELEMETRY": "off"}


def go_repo(run: Run) -> str:
    work = run.dir / "work"
    path = work / "main.go"
    (work / "go.mod").write_text("module probe\n\ngo 1.22\n", encoding="utf-8")
    path.write_text('package main\n\nfunc main() {\n\tprintln("v0")\n}\n', encoding="utf-8")
    for cmd in (["git", "init", "-q", str(work)], ["git", "-C", str(work), "add", "-A"],
                ["git", "-C", str(work), "-c", "user.email=p@p", "-c", "user.name=p", "commit", "-qm", "init"]):
        subprocess.run(cmd, check=True, capture_output=True)
    return str(path)


def tool_gaps(run: Run, g: fakes.Gateway, p: fakes.Pty, t_enter: float, expect_posts: int, wait: float):
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        posts = [t for t, m, _ in list(g.events) if m == "POST" and t >= t_enter]
        if len(posts) >= expect_posts:
            break
        time.sleep(0.05)
    posts = [t for t, m, _ in list(g.events) if m == "POST" and t >= t_enter]
    run.rec["posts_s"] = [rel(p, t) for t in posts]
    gaps = [round(b - a, 3) for a, b in zip(posts, posts[1:])]
    run.rec["gaps_s"] = gaps
    return gaps


def arm_edit(run: Run, lsp: str):
    path = go_repo(run)
    turns = [fakes.sse_tool("Read", {"file_path": path}, "t0")]
    edits = 2 if lsp == "gopls" else 1
    for i in range(edits):
        turns.append(fakes.sse_tool("Edit", {"file_path": path, "old_string": '"v%d"' % i, "new_string": '"v%d"' % (i + 1)}, "t%d" % (i + 1)))
    turns.append(fakes.sse_text("pong-ok"))
    g = gateway(run, turns=turns)
    extra = dict(GO_ENV)
    extra.update({"GOPATH": str(run.dir / "home" / "go"), "GOMODCACHE": str(run.dir / "home" / "go" / "pkg" / "mod"),
                  "GOCACHE": str(run.dir / "home" / "gocache")})
    args = []
    if lsp == "quiet":
        fbin = run.dir / "srv" / "bin"
        fbin.mkdir()
        script = run.stage("quiet_lsp.py", "c.py")
        (fbin / "gopls").write_text("#!/bin/sh\nexec %s %s\n" % (PY, script), encoding="utf-8")
        (fbin / "gopls").chmod(0o755)
        extra["PATH"] = "%s:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" % fbin
    elif lsp == "gopls":
        if run.ctx.gopls is None:
            raise Invalid("no --gopls given")
        extra["PATH"] = "%s:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" % run.ctx.gopls.parent
    else:
        args = ["--no-lsp"]
    p = run.launch(g.url, extra, args)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_enter, _, _ = run.turn(p, g, wait=0.1)
    gaps = tool_gaps(run, g, p, t_enter, 2 + edits, 40)
    t_reply = p.wait_for(b"pong-ok", 10)
    run.rec.update(box_s=rel(p, t_box), reply_s=rel(p, t_reply))
    run.exit(p, 10)
    delivery(run, g, p.t0)
    if len(gaps) < 1 + edits:
        raise Invalid("the scripted turns did not all run")
    if lsp == "quiet":
        return "edit_waited_both_limits" if 13.5 <= gaps[1] < 17.0 else "other"
    if lsp == "gopls":
        return "first_edit_pays" if gaps[1] >= 0.3 and gaps[2] < 0.3 else "other"
    return "no_wait" if gaps[1] < 0.3 else "control_failed"


def bash_repo(ctx: Ctx, files: int) -> Path:
    template = ctx.out / "fixtures" / ("repo-%d" % files)
    with ctx.lock:
        if not (template / ".git").exists():
            shutil.rmtree(template, ignore_errors=True)
            template.mkdir(parents=True)
            for i in range(files):
                d = template / ("d%03d" % (i // 100))
                if i % 100 == 0:
                    d.mkdir(exist_ok=True)
                (d / ("f%05d.txt" % i)).write_text("x%d\n" % i, encoding="utf-8")
            (template / "README").write_text("probe\n", encoding="utf-8")
            # gc.auto=0: an automatic background repack would delete loose-object
            # directories while the copy below walks them.
            for cmd in (["git", "init", "-q", str(template)], ["git", "-C", str(template), "config", "gc.auto", "0"],
                        ["git", "-C", str(template), "config", "maintenance.auto", "false"],
                        ["git", "-C", str(template), "add", "-A"],
                        ["git", "-C", str(template), "-c", "user.email=p@p", "-c", "user.name=p", "commit", "-qm", "init"]):
                subprocess.run(cmd, check=True, capture_output=True)
    return template


def arm_bash(run: Run, files: int):
    template = bash_repo(run.ctx, files)
    work = run.dir / "work"
    shutil.rmtree(work)
    subprocess.run(["cp", "-cR", str(template), str(work)], check=True)
    commands = ["echo probe-0", "touch p-1.txt", "echo probe-2", "touch p-3.txt", "echo probe-4", "touch p-5.txt"]
    turns = [fakes.sse_tool("Bash", {"command": c}, "t%d" % i) for i, c in enumerate(commands)]
    turns.append(fakes.sse_text("pong-ok"))
    g = gateway(run, turns=turns)
    p = run.launch(g.url)
    t_box = run.box(p, 10)
    if t_box is None:
        raise Invalid("input box never appeared")
    t_enter, _, _ = run.turn(p, g, wait=0.1)
    gaps = tool_gaps(run, g, p, t_enter, 7, 40)
    t_reply = p.wait_for(b"pong-ok", 10)
    run.rec.update(box_s=rel(p, t_box), reply_s=rel(p, t_reply), files=files)
    run.exit(p, 10)
    delivery(run, g, p.t0)
    if len(gaps) < 6:
        raise Invalid("the scripted Bash calls did not all run")
    echo, touch = [gaps[i] for i in (0, 2, 4)], [gaps[i] for i in (1, 3, 5)]
    floor, diff = min(gaps[:6]), round(statistics.median(touch) - statistics.median(echo), 3)
    run.rec.update(echo_gaps_s=echo, touch_gaps_s=touch, floor_s=floor, touch_minus_echo_s=diff)
    log = run.dir / "subject.log"
    if log.exists():
        text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text(encoding="utf-8", errors="replace"))
        run.rec["bash_fc_lines"] = [line for line in text.splitlines() if "bash_fc" in line][:12]
    if files >= 1000:
        return "observation_paid" if diff >= 0.15 and min(echo) >= 0.10 else "other"
    return "floor_seen" if floor >= 0.10 else "other"


DISPATCH = {
    "C0-pre": arm_c0, "C0-post": arm_c0, "P-splash": arm_splash, "P-stdio5-exit": lambda r: arm_mcp_stdio5_exit(r),
    "S-models-5s": lambda r: arm_models(r, 5.0, 15), "S-models-stall": lambda r: arm_models(r, None, 35),
    "S-models-warm": arm_models_warm, "S-kg-stall": arm_kg,
    "K-keys-0s": lambda r: arm_keys(r, 0.0), "K-keys-5s": lambda r: arm_keys(r, 5.0), "K-keys-stall": lambda r: arm_keys(r, None),
    "M-stdio-stall": lambda r: arm_mcp_stdio(r, False), "M-stdio-stall-esc": lambda r: arm_mcp_stdio(r, True),
    "M-http-delete-stall": arm_mcp_http_delete, "M-https-tls-stall": arm_mcp_https_tls,
    "E-otlp-stall": arm_otlp,
    "T-edit-silent-lsp": lambda r: arm_edit(r, "quiet"), "T-edit-nolsp": lambda r: arm_edit(r, "none"),
    "T-edit-gopls": lambda r: arm_edit(r, "gopls"),
    "T-bash-mixed-1": lambda r: arm_bash(r, 1), "T-bash-mixed-20k": lambda r: arm_bash(r, 20000),
}
assert set(DISPATCH) == set(ARMS)


def run_one(ctx: Ctx, arm: str, index: int) -> dict:
    run = Run(ctx, arm, index)
    started = time.time()
    try:
        verdict = DISPATCH[arm](run)
        run.rec["invalid_reason"] = None
    except Invalid as exc:
        verdict = "invalid"
        run.rec["invalid_reason"] = str(exc)
    except Exception as exc:
        verdict = "invalid"
        run.rec["invalid_reason"] = "harness exception: %r" % exc
        run.rec["traceback"] = traceback.format_exc()
    finally:
        run.finish()
    fields = VERDICTS.get(verdict, VERDICTS["other"])
    run.rec.update(verdict=verdict, level=fields[4], started=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(started)),
                   wall_s=round(time.time() - started, 3))
    run.rec["observation"] = {k: v for k, v in zip(FIELDS, fields[:4]) if v is not None}
    write_json(run.dir / "record.json", run.rec)
    with ctx.lock:
        with open(ctx.out / "runs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(run.rec, ensure_ascii=False) + "\n")
    print("%-20s #%d %-28s %s" % (arm, index, verdict, run.rec.get("invalid_reason") or ""), flush=True)
    return run.rec


# ---------------------------------------------------------------- commands


def versions(ctx: Ctx, tag: str) -> dict:
    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "tag": tag}
    home = ctx.out / "probe-home"
    home.mkdir(parents=True, exist_ok=True)
    ctx.sb.write_text(SB_PROFILE, encoding="utf-8")
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TMPDIR": "/tmp", "GOTELEMETRY": "off"}
    boxed = ["/usr/bin/sandbox-exec", "-f", str(ctx.sb)]
    if ctx.bin:
        r = subprocess.run(boxed + [str(ctx.bin), "--version"], capture_output=True, text=True, timeout=30, env=env)
        out["subject"] = {"path": str(ctx.bin), "sha256": sha256_file(ctx.bin), "version": r.stdout.strip()}
    if ctx.rg:
        out["rg"] = {"path": str(ctx.rg), "sha256": sha256_file(ctx.rg)}
    if ctx.gopls:
        r = subprocess.run(boxed + [str(ctx.gopls), "version"], capture_output=True, text=True, timeout=60, env=env)
        out["gopls"] = {"path": str(ctx.gopls), "sha256": sha256_file(ctx.gopls), "version": r.stdout.strip()}
    out["go"] = {"path": "/opt/homebrew/bin/go", "sha256": sha256_file("/opt/homebrew/bin/go")} if os.path.exists("/opt/homebrew/bin/go") else None
    out["python"] = {"path": PY, "version": sys.version.split()[0]}
    out["witness"] = {str(p.relative_to(REPO)): sha256_file(p) for p in sorted(HERE.rglob("*.py"))}
    out["sandbox_profile_sha256"] = hashlib.sha256(SB_PROFILE.encode()).hexdigest()
    return out


def do_probe(ctx: Ctx) -> int:
    ctx.out.mkdir(parents=True, exist_ok=True)
    v = versions(ctx, "probe")
    write_json(ctx.out / "probes" / "versions.json", v)
    print(json.dumps(v, ensure_ascii=False, indent=1))
    return 0


def do_matrix(ctx: Ctx) -> int:
    a = ctx.args
    ctx.out.mkdir(parents=True, exist_ok=True)
    ctx.sb.write_text(SB_PROFILE, encoding="utf-8")
    arms = [x for x in (a.arms.split(",") if a.arms else list(ARMS)) if x]
    unknown = [x for x in arms if x not in ARMS]
    if unknown:
        raise SystemExit("unknown arms: " + ", ".join(unknown))
    gate = load_card_gate()
    card_path = Path(a.card).resolve()
    card_bytes = card_path.read_bytes()
    card = json.loads(card_bytes)
    card_sha = hashlib.sha256(card_bytes).hexdigest()
    try:
        provenance = gate.card_provenance(card_path)
        accounting = gate.check(card, card_sha, ctx.out, [HOST], MODE, arms, a.runs, a.deviation)
    except gate.GateError as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return 2
    if provenance.get("pushed") is not True:
        print("warning: the card's commit is not on an upstream branch; the freeze is dated by a local commit only",
              file=sys.stderr)
    stamp = time.strftime("%Y%m%dT%H%M%S") + "-%d" % os.getpid()
    shutil.copyfile(card_path, ctx.out / "card-frozen.json")
    before = versions(ctx, "before")
    write_json(ctx.out / ("versions-before-%s.json" % stamp), before)
    with open(ctx.out / "frozen-sha256.txt", "w", encoding="utf-8") as f:
        for name, digest in before["witness"].items():
            f.write("%s  %s\n" % (digest, name))
    manifest = {"stamp": stamp, "card": provenance, "card_sha256": card_sha, "accounting": accounting,
                "tools": [HOST], "mode": MODE, "conditions": arms, "runs": a.runs, "parallel": a.parallel,
                "deviation": a.deviation, "dispatched": {}, "invalid": {}}
    mpath = ctx.out / ("manifest-%s.json" % stamp)
    write_json(mpath, manifest)
    mlock = threading.Lock()

    def charge(arm, verdict=None):
        key = gate.cell_key(HOST, MODE, arm)
        with mlock:
            if verdict is None:
                manifest["dispatched"][key] = manifest["dispatched"].get(key, 0) + 1
            elif verdict == "invalid":
                manifest["invalid"][key] = manifest["invalid"].get(key, 0) + 1
            write_json(mpath, manifest)

    def dispatch(arm, index):
        charge(arm)
        rec = run_one(ctx, arm, index)
        charge(arm, rec["verdict"])
        return rec

    def plan(group):
        return [(arm, i) for i in range(1, a.runs + 1) for arm in arms if ARMS[arm] == group]

    results = []
    for arm, i in plan("baseline"):
        results.append(dispatch(arm, i))
    if any(r["verdict"] in ("control_failed", "invalid") for r in results):
        print("a baseline control did not pass; fault cells are not run", file=sys.stderr)
        manifest["stopped"] = "baseline control failed"
        write_json(mpath, manifest)
        return 1
    with ThreadPoolExecutor(max_workers=max(1, a.parallel)) as pool:
        results += list(pool.map(lambda job: dispatch(*job), plan("pool")))
    for arm, i in plan("precise") + plan("post"):
        results.append(dispatch(arm, i))
    after = versions(ctx, "after")
    write_json(ctx.out / ("versions-after-%s.json" % stamp), after)
    manifest["subject_sha256_unchanged"] = before.get("subject", {}).get("sha256") == after.get("subject", {}).get("sha256")
    manifest["witness_unchanged"] = before["witness"] == after["witness"]
    manifest["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(mpath, manifest)
    return 0


def load_runs(out: Path) -> list[dict]:
    path = out / "runs.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


KEY_NUMBERS = ("box_s", "echo_lag_s", "first_request_wait_s", "exit_s", "sigterm_exit_s", "interrupted_after_esc_s",
               "floor_s", "touch_minus_echo_s")


def do_summarize(ctx: Ctx) -> int:
    runs = load_runs(ctx.out)
    by_arm = defaultdict(list)
    for r in runs:
        by_arm[r["arm"]].append(r)
    lines = ["# witness/stall 汇总", "",
             "每格的判定计数，后面是单侧 95% Wilson 界（z=1.645，`skills/repo-quake/references/measurement.md`），"
             "分母不含 invalid。3/3 的下界只有 0.53：小样本只分三档（稳定出现、时有时无、稳定不出现），不给比率。", "",
             "| 组 | N（有效） | 判定 | Wilson 界 | 等级 | invalid | 关键数字 |", "|---|---:|---|---|---|---:|---|"]
    for arm in ARMS:
        rs = by_arm.get(arm, [])
        if not rs:
            continue
        valid = [r for r in rs if r["verdict"] != "invalid"]
        counts = Counter(r["verdict"] for r in valid)
        verdict_text = "; ".join("%s %d/%d" % (v, c, len(valid)) for v, c in counts.most_common())
        bounds = "; ".join("%s %.2f–%.2f" % ((v,) + wilson(c, len(valid))) for v, c in counts.most_common())
        levels = ",".join(r.get("level") or "-" for r in valid)
        nums = []
        for key in KEY_NUMBERS:
            vals = [r[key] for r in valid if isinstance(r.get(key), (int, float))]
            if vals:
                nums.append("%s %s" % (key, "/".join("%.3f" % v for v in vals)))
        invalid = len(rs) - len(valid)
        lines.append("| %s | %d | %s | %s | %s | %d | %s |" % (arm, len(valid), verdict_text or "-", bounds or "-",
                                                             levels, invalid, "; ".join(nums)))
    lines += ["", "invalid 的原因：", ""]
    for r in runs:
        if r["verdict"] == "invalid":
            lines.append("- %s #%d：%s" % (r["arm"], r["index"], r.get("invalid_reason")))
    for path in sorted(ctx.out.glob("manifest-*.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        lines += ["", "manifest `%s`：卡片提交 `%s`（已推送：%s），被测二进制前后一致：%s，证人前后一致：%s，偏离：%s" % (
            path.name, (m.get("card") or {}).get("commit", "?")[:12], (m.get("card") or {}).get("pushed"),
            m.get("subject_sha256_unchanged"), m.get("witness_unchanged"), m.get("deviation") or "无")]
    (ctx.out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def do_egress(ctx: Ctx) -> int:
    a = ctx.args
    predicate = 'eventMessage CONTAINS "deny(1) network-outbound"'
    r = subprocess.run(["log", "show", "--style", "ndjson", "--start", a.start, "--end", a.end, "--predicate", predicate],
                       capture_output=True, text=True, timeout=900)
    hits = []
    for line in r.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = item.get("eventMessage", "")
        m = re.search(r"Sandbox: ([^()]+)\((\d+)\) deny\(1\) network-outbound (\S+)", msg)
        if m and m.group(1) in {"metacodes", "sandbox-exec", "python3", "Python", "gopls", "go", "git", "rg"}:
            hits.append({"time": item.get("timestamp"), "process": m.group(1), "target": m.group(3)})
    summary = Counter("%s -> %s" % (h["process"], h["target"]) for h in hits)
    out = {"window": [a.start, a.end], "denials": len(hits), "by_target": dict(summary), "first": hits[:20]}
    write_json(ctx.out / "egress.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


LSREGISTER = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"


def do_lsregister(ctx: Ctx) -> int:
    r = subprocess.run([LSREGISTER, "-dump"], capture_output=True, text=True, timeout=600)
    root = str(ctx.out)
    paths = sorted({line.split("path:", 1)[1].strip() for line in r.stdout.splitlines() if "path:" in line and root in line})
    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "registrations_under_evidence_root": paths}
    write_json(ctx.out / "lsregister.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


EXPORT_TOP = ["summary.md", "manifest-*.json", "versions-before-*.json", "versions-after-*.json", "card-frozen.json",
              "frozen-sha256.txt", "egress.json", "lsregister.json", "matrix.log", "runs.jsonl", "loopback.sb"]
DENY = [r"/Users/[A-Za-z0-9._-]+", r"/home/[A-Za-z0-9._-]+", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"]


def do_export(args) -> int:
    src, dst = Path(args.src).resolve(), Path(args.dst).resolve()
    before = {str(p): sha256_file(p) for p in sorted(src.rglob("*")) if p.is_file() and not p.is_symlink()}
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    copied = []
    for pattern in EXPORT_TOP:
        for p in sorted(src.glob(pattern)):
            copied.append(p)
    copied += sorted(src.glob("runs/*/*/record.json"))
    copied += sorted(src.glob("probes/*.json"))
    replace = [(str(src), "<EVIDENCE_ROOT>"), (str(Path.home()), "<HOME>"), ("/private/tmp", "<TMP>")]
    replace += [tuple(x.split("=", 1)) for x in (args.replace or [])]
    for p in copied:
        text = p.read_text(encoding="utf-8", errors="replace")
        for old, new in replace:
            text = text.replace(old, new)
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    after = {str(p): sha256_file(p) for p in sorted(src.rglob("*")) if p.is_file() and not p.is_symlink()}
    if before != after:
        print("the evidence root changed during the export", file=sys.stderr)
        return 2
    hits = []
    for p in sorted(dst.rglob("*")):
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            for pat in DENY + list(args.deny or []):
                for m in re.finditer(pat, text):
                    hits.append("%s: %s" % (p.relative_to(dst), m.group(0)))
    manifest_digest = hashlib.sha256("\n".join("%s %s" % kv for kv in sorted(before.items())).encode()).hexdigest()
    note = ["# 公开副本说明（witness/stall/stall.py export 生成）", "",
            "- 源证据目录：`<EVIDENCE_ROOT>`，共 %d 个文件；导出前后哈希清单一致，清单摘要 sha256 `%s`。" % (len(before), manifest_digest),
            "- 复制了 %d 个文本文件，只在副本上脱敏：本机路径换成占位符（`<EVIDENCE_ROOT>`、`<HOME>`、`<TMP>`）。" % len(copied),
            "- 没有复制：被测程序的临时 HOME、状态目录、工作目录、调试日志（`subject.log`）、终端原始字节（`raw.bin`、`raw-index.jsonl`）和按键记录（`writes.jsonl`）。由它们得出的数字在 `record.json` 里。"]
    (dst / "EXPORT.md").write_text("\n".join(note) + "\n", encoding="utf-8")
    audit = subprocess.run([PY, str(REPO / "skills" / "repo-quake" / "scripts" / "audit_artifacts.py"), str(dst)],
                           capture_output=True, text=True)
    print(audit.stdout.strip())
    if hits:
        print("forbidden strings in the copy:\n" + "\n".join(hits[:40]), file=sys.stderr)
        return 1
    return 0 if audit.returncode == 0 else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["probe", "matrix", "summarize", "egress", "lsregister", "export"])
    p.add_argument("--out")
    p.add_argument("--bin")
    p.add_argument("--rg")
    p.add_argument("--gopls")
    p.add_argument("--card")
    p.add_argument("--arms")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--parallel", type=int, default=5)
    p.add_argument("--deviation")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--src")
    p.add_argument("--dst")
    p.add_argument("--replace", action="append")
    p.add_argument("--deny", action="append")
    args = p.parse_args(argv)
    if args.action == "export":
        return do_export(args)
    if not args.out:
        raise SystemExit("--out is required")
    ctx = Ctx(args)
    if args.action in ("probe", "matrix") and not ctx.bin:
        raise SystemExit("--bin is required")
    if args.action == "matrix" and not args.card:
        raise SystemExit("--card is required: freeze and commit the experiment card first")
    return {"probe": do_probe, "matrix": do_matrix, "summarize": do_summarize, "egress": do_egress,
            "lsregister": do_lsregister}[args.action](ctx)


if __name__ == "__main__":
    sys.exit(main())
