#!/usr/bin/env python3
"""Stream-retry display matrix runner (repo-quake phase 4).

Question: after a mid-stream failure and an automatic retry, does what the CLI shows
match what it stores and sends next? Subjects talk only to a loopback mock started by
this runner; see README.md for the decision table and the verifier fixes.

Subcommands:
  probe      start each TUI once, gate-check the first screen, exit
  matrix     run tool x condition x N (interactive via tmux, or non-interactive)
  regrade    re-grade every run from its evidence files into regrade.jsonl
  summarize  write summary.md from runs.jsonl
  egress     list sandbox-denied outbound connections of subject processes
  lsregister list LaunchServices registrations of Claude Code URL handlers
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grading  # noqa: E402
import version_witness  # noqa: E402

PROMPT = "写一份三节分析报告，主题：流式输出的完整性判定。直接输出报告全文，不要调用任何工具。"
FOLLOWUP = "好的，谢谢。"
DEFAULT_CONDITIONS = ["F0-pre", "F0-tag", "F1-once", "F6-once", "FLONG-once", "F0-post"]
BASELINE = ("F0-pre", "F0-tag")
DEFAULT_PATH_ENV = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
SANDBOX_PROFILE = (
    "(version 1)(allow default)(deny network-outbound)"
    '(allow network-outbound (remote ip "localhost:*"))'
)
LSREGISTER = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
DANGER = re.compile(
    r"(?i)press enter|\[enter\]|migrate now|update now|update available|upgrade now|"
    r"npm install|installing|do you trust|trust this folder|\(y/n\)|\[y/n\]|"
    r"log in to continue|sign in to continue|select an option|migration required|"
    r"do you want to use this api key|enter to confirm"
)


def now_ms() -> int:
    return int(time.time() * 1000)


def iso(ms: int | None = None) -> str:
    t = dt.datetime.fromtimestamp((ms if ms is not None else now_ms()) / 1000, dt.timezone.utc)
    return t.isoformat(timespec="milliseconds")


def sh(*args, check=False, timeout=30, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True, check=check, timeout=timeout, env=env)


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return str(Path(path).resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


# ---------------- subjects ----------------
class Tool:
    name = "base"
    ready_re = r"$^"
    banner_re = r"$^"
    endpoint = "cc"
    session_globs = ("**/*.jsonl",)

    def __init__(self, binary: str, expected: str | None):
        self.binary = binary
        self.expected = expected

    def env(self, home: Path) -> dict:
        return {}

    def seed(self, home: Path, cwd: Path, base_url: str) -> None:
        home.mkdir(parents=True, exist_ok=True)

    def argv(self, base_url: str, mode: str, prompt: str | None) -> list[str]:
        raise NotImplementedError

    def gate(self, screen: str) -> tuple[bool, list[str]]:
        visible = "\n".join(line for line in screen.splitlines() if line.strip())
        ready = bool(re.search(self.ready_re, visible, re.M))
        danger = [line.strip() for line in visible.splitlines() if DANGER.search(line)]
        return ready, danger


class Claude(Tool):
    name = "claude"
    ready_re = r"\? for shortcuts|❯|>\s*$"
    banner_re = r"Claude Code v\d+\.\d+\.\d+"
    endpoint = "anthropic"
    session_globs = ("claude-config/projects/**/*.jsonl",)

    def env(self, home):
        return {"CLAUDE_CONFIG_DIR": str(home / "claude-config"), "DISABLE_AUTOUPDATER": "1"}

    def seed(self, home, cwd, base_url):
        cfg = home / "claude-config"
        cfg.mkdir(parents=True, exist_ok=True)
        seed = {
            "hasCompletedOnboarding": True,
            "theme": "dark",
            "customApiKeyResponses": {"approved": [], "rejected": ["mock"]},
            "projects": {str(cwd): {"hasTrustDialogAccepted": True, "lastGracefulShutdown": True}},
        }
        write_json(cfg / ".claude.json", seed)

    def argv(self, base_url, mode, prompt):
        settings = {
            "env": {
                "ANTHROPIC_BASE_URL": base_url,
                "ANTHROPIC_API_KEY": "mock",
                "ANTHROPIC_MODEL": "mock-model",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "API_TIMEOUT_MS": "60000",
            },
            "model": "mock-model",
            # keep the subject from registering a claude-cli:// handler with LaunchServices
            "disableDeepLinkRegistration": "disable",
        }
        args = [self.binary, "--bare", "--settings", json.dumps(settings, separators=(",", ":"))]
        if mode == "noninteractive":
            args += ["-p", prompt]
        return args


class Codex(Tool):
    name = "codex"
    ready_re = r"Ask Codex to do anything|›"
    banner_re = r"OpenAI Codex \(v\d"
    endpoint = "responses"
    session_globs = ("codex/sessions/**/*.jsonl",)

    def env(self, home):
        return {"CODEX_HOME": str(home / "codex"), "MOCK_API_KEY": "mock"}

    def seed(self, home, cwd, base_url):
        (home / "codex").mkdir(parents=True, exist_ok=True)

    def argv(self, base_url, mode, prompt):
        cfg = [
            "-c", "check_for_update_on_startup=false",
            "-c", "model_provider=mock",
            "-c", 'model_providers.mock.name="Mock"',
            "-c", f'model_providers.mock.base_url="{base_url}/v1"',
            "-c", 'model_providers.mock.wire_api="responses"',
            "-c", 'model_providers.mock.env_key="MOCK_API_KEY"',
            "-c", 'model="mock-model"',
        ]
        if mode == "noninteractive":
            return [self.binary, "exec", "--skip-git-repo-check", *cfg, prompt]
        return [self.binary, *cfg]


class Kimi(Tool):
    name = "kimi"
    ready_re = r"── input ──|Ask anything|Type your message|No session yet|❯|>\s*$"
    banner_re = r"Welcome to Kimi Code"
    endpoint = "cc"
    session_globs = (".kimi-code/sessions/**/*.jsonl",)

    def env(self, home):
        return {"KIMI_DISABLE_TELEMETRY": "1", "KIMI_CODE_TRUST_WORKSPACE": "1"}

    def seed(self, home, cwd, base_url):
        cfg = home / ".kimi-code"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "config.toml").write_text(
            'default_model = "mock"\n\n[providers.mock]\ntype = "kimi"\napi_key = "mock"\n'
            f'base_url = "{base_url}/v1"\n\n[models."mock"]\nprovider = "mock"\n'
            'model = "mock-model"\nmax_context_size = 131072\n', encoding="utf-8")
        (cfg / "tui.toml").write_text(
            'theme = "dark"\nauto_session_title = false\n\n[notifications]\nenabled = false\n\n'
            '[upgrade]\nauto_install = false\n', encoding="utf-8")

    def argv(self, base_url, mode, prompt):
        return [self.binary, "-p", prompt] if mode == "noninteractive" else [self.binary]


class Fake(Tool):
    """Calibration subject (tests/fixtures/stream-retry/fake_tui.py)."""
    name = "fake"
    ready_re = r"FAKE>"
    banner_re = r"FAKE TUI v1"
    endpoint = "cc"
    session_globs = ("fake-sessions/*.jsonl",)

    def __init__(self, binary, expected, fake_mode="retract"):
        super().__init__(binary, expected)
        self.fake_mode = fake_mode

    def env(self, home):
        return {"FAKE_MODE": self.fake_mode, "FAKE_SESSIONS": str(home / "fake-sessions")}

    def argv(self, base_url, mode, prompt):
        args = [sys.executable, "-I", self.binary, "--base-url", base_url]
        if mode == "noninteractive":
            args += ["--print", prompt]
        return args


TOOL_CLASSES = {"claude": Claude, "codex": Codex, "kimi": Kimi, "fake": Fake}


# ---------------- mock ----------------
class Mock:
    def __init__(self, root: Path, node: str, script: Path, content: Path, port: int, delay: int,
                 long_delay: int, continuation: str, label: str):
        self.dir = root / f"mock-{label}"
        if self.dir.exists():
            raise RuntimeError(f"refusing to reuse mock directory {self.dir}")
        self.dir.mkdir(parents=True)
        self.token = secrets.token_hex(16)
        self.instance = secrets.token_hex(8)
        self.offset = 0
        self.entries: list[dict] = []
        self.bodies: dict[int, bytes] = {}
        env = {"PATH": os.environ.get("PATH", DEFAULT_PATH_ENV), "MOCK_CONTROL_TOKEN": self.token,
               "MOCK_INSTANCE": self.instance}
        ready_file = self.dir / "ready.json"
        self.stdout = (self.dir / "stdout.txt").open("a", encoding="utf-8")
        cmd = [node, str(script), "--port", str(port), "--delay", str(delay), "--long-delay", str(long_delay),
               "--continuation", continuation, "--logdir", str(self.dir), "--ready-file", str(ready_file),
               "--content", str(content)]
        self.proc = subprocess.Popen(cmd, stdout=self.stdout, stderr=subprocess.STDOUT, env=env,
                                     start_new_session=True)
        deadline = time.time() + 15
        while time.time() < deadline and not ready_file.exists():
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        if self.proc.poll() is not None or not ready_file.exists():
            self.stop()
            raise RuntimeError(f"mock did not start (see {self.dir / 'stdout.txt'})")
        self.ready = json.loads(ready_file.read_text(encoding="utf-8"))
        self.port = int(self.ready["port"])
        if port and self.port != port:
            self.stop()
            raise RuntimeError(f"mock bound {self.port}, asked for {port}")
        self.base_url = f"http://127.0.0.1:{self.port}"
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=3) as r:
                health = json.load(r)
        except Exception as exc:  # noqa: BLE001
            self.stop()
            raise RuntimeError(f"mock health check failed: {exc}") from exc
        if health.get("instance") != self.instance:
            self.stop()
            raise RuntimeError(f"port {self.port} answers as instance {health.get('instance')}, not ours")
        listeners = listener_pids(self.port)
        if listeners != {self.proc.pid}:
            self.stop()
            raise RuntimeError(f"listener pid mismatch on {self.port}: child={self.proc.pid}, lsof={sorted(listeners)}")

    def control(self, body: dict) -> dict:
        req = urllib.request.Request(f"{self.base_url}/__control", data=json.dumps(body).encode(), method="POST",
                                     headers={"content-type": "application/json", "x-mock-token": self.token})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)

    def refresh(self) -> list[dict]:
        path = self.dir / "delivery.jsonl"
        if not path.exists():
            return []
        with path.open("rb") as handle:
            handle.seek(self.offset)
            data = handle.read()
        cut = data.rfind(b"\n") + 1
        self.offset += cut
        new = [json.loads(line) for line in data[:cut].decode("utf-8").splitlines() if line.strip()]
        self.entries.extend(new)
        return new

    def body(self, seq: int) -> bytes:
        if seq not in self.bodies:
            path = self.dir / f"req-{seq}.json"
            self.bodies[seq] = path.read_bytes() if path.exists() else b""
        return self.bodies[seq]

    def stop(self) -> None:
        if self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        self.stdout.close()


def listener_pids(port: int) -> set[int]:
    out = sh("lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t").stdout
    return {int(x) for x in out.split() if x.strip().isdigit()}


def port_in_use(port: int) -> bool:
    return bool(port) and bool(listener_pids(port))


# ---------------- tmux (private server) ----------------
class Tmux:
    def __init__(self, root: Path, width: int, height: int):
        self.socket = f"rq-stream-{secrets.token_hex(4)}"
        self.conf = root / f"tmux-{self.socket}.conf"
        self.conf.write_text(
            # size comes from new-session -x/-y; `set -g window-size manual` crashes tmux 3.5a here
            "set -g default-shell /bin/sh\nset -g history-limit 50000\nset -g status off\n"
            "set -g remain-on-exit on\n",
            encoding="utf-8")
        self.width, self.height = width, height

    def cmd(self, *args, timeout=15) -> subprocess.CompletedProcess:
        return sh("tmux", "-L", self.socket, "-f", str(self.conf), *args, timeout=timeout)

    def new(self, name: str, cwd: Path, command: str) -> None:
        r = self.cmd("new-session", "-d", "-s", name, "-x", str(self.width), "-y", str(self.height), "-c", str(cwd), command)
        if r.returncode != 0:
            raise RuntimeError(f"tmux new-session failed: {r.stderr.strip()}")

    def pipe(self, name: str, raw: Path) -> None:
        raw.touch()
        index = raw.with_name(raw.stem + "-index.jsonl")
        tap = f"exec {shlex.quote(sys.executable)} -I -u {shlex.quote(str(HERE / 'rawtap.py'))} {shlex.quote(str(raw))} {shlex.quote(str(index))}"
        r = self.cmd("pipe-pane", "-o", "-t", name, tap)
        if r.returncode != 0:
            raise RuntimeError(f"tmux pipe-pane failed: {r.stderr.strip()}")

    def unpipe(self, name: str) -> None:
        self.cmd("pipe-pane", "-t", name)

    def capture(self, name: str, history: bool = False) -> str:
        args = ["capture-pane", "-p", "-t", name]
        if history:
            args += ["-S", "-", "-E", "-"]
        return self.cmd(*args).stdout

    def keys(self, name: str, *keys: str, literal: bool = False) -> None:
        self.cmd("send-keys", "-t", name, *(["-l"] if literal else []), *keys)

    def display(self, name: str, fmt: str) -> str:
        return self.cmd("display-message", "-p", "-t", name, fmt).stdout.strip()

    def kill(self, name: str) -> None:
        self.cmd("kill-session", "-t", name)

    def kill_server(self) -> None:
        self.cmd("kill-server")
        try:
            self.conf.unlink()
        except FileNotFoundError:
            pass


# ---------------- context ----------------
class Context:
    def __init__(self, args, tools: dict[str, Tool]):
        self.args = args
        self.out: Path = Path(args.out).resolve()
        self.tools = tools
        self.content = grading.Content(HERE / "content.json")
        self.exe_cache: dict[tuple, str] = {}
        self.mock: Mock | None = None
        self.tmux: Tmux | None = None
        self.pids: list[dict] = []
        self.views: dict[tuple, dict] = {}

    def home(self, tool: Tool, run_id: str) -> Path:
        return self.out / "homes" / tool.name / run_id

    def cwd(self, tool: Tool) -> Path:
        path = self.out / "cwd" / tool.name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def launch(self, tool: Tool, home: Path, mode: str, prompt: str | None) -> list[str]:
        env = {"PATH": self.args.path_env, "TERM": "xterm-256color", "LANG": "en_US.UTF-8", "HOME": str(home)}
        env.update(tool.env(home))
        argv = ["/usr/bin/env", "-i", *[f"{k}={v}" for k, v in env.items()]]
        if self.args.sandbox:
            argv += ["/usr/bin/sandbox-exec", "-p", SANDBOX_PROFILE]
        return argv + tool.argv(self.mock.base_url, mode, prompt)

    def executed(self, pid: int) -> dict:
        out = sh("lsof", "-a", "-p", str(pid), "-d", "txt", "-Fn").stdout
        paths = [line[1:] for line in out.splitlines() if line.startswith("n")]
        if not paths:
            return {"pid": pid, "path": None}
        exe = paths[0]
        try:
            st = os.stat(exe)
            key = (exe, st.st_size, st.st_mtime_ns)
            if key not in self.exe_cache:
                self.exe_cache[key] = version_witness.sha256_file(Path(exe))
            return {"pid": pid, "path": exe, "sha256": self.exe_cache[key]}
        except OSError as exc:
            return {"pid": pid, "path": exe, "error": str(exc)}


def request_view(ctx: Context, entry: dict, mark: str, tag: str | None) -> dict:
    key = (entry["seq"], mark, tag)
    if key in ctx.views:
        return ctx.views[key]
    witness = grading.request_witness(ctx.mock.body(entry["seq"]), entry.get("endpoint"), mark, tag)
    keep = ("seq", "started_ms", "body_ms", "first_byte_ms", "ended_ms", "endpoint", "fault", "fault_source", "stream",
            "aux", "tools_count", "profile", "tag_applied", "events_count", "bytes_sent", "ending", "witnesses",
            "continuation", "req_bytes", "req_sha256", "user_agent", "frame_delay_ms", "client_closed_first")
    view = {k: entry.get(k) for k in keep}
    view.update({k: witness[k] for k in ("has_mark", "assistant_messages", "assistant_marker_counts",
                                          "carries_partial", "carries_tag", "trailing_role", "partial_flag")})
    ctx.views[key] = view
    return view


def marked(ctx: Context, mark: str, tag: str | None, since_seq: int, start_ms: int | None = None,
           end_ms: int | None = None) -> list[dict]:
    out = []
    for entry in ctx.mock.entries:
        if entry["seq"] <= since_seq:
            continue
        view = request_view(ctx, entry, mark, tag)
        if not view["has_mark"]:
            continue
        if start_ms is not None and entry["started_ms"] < start_ms:
            continue
        if end_ms is not None and entry["started_ms"] >= end_ms:
            continue
        out.append(view)
    return out


def copy_requests(ctx: Context, views: list[dict], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for view in views:
        src = ctx.mock.dir / f"req-{view['seq']}.json"
        if src.exists():
            shutil.copy2(src, dest / src.name)


def conversation_witness(ctx: Context, home: Path, globs, mark: str, tag: str | None, profile: str,
                         started_ms: int) -> dict | None:
    found = []
    for pattern in globs:
        for path in sorted(home.glob(pattern)):
            try:
                st = path.stat()
                if st.st_size > 50_000_000 or st.st_mtime * 1000 < started_ms - 3000:
                    continue
                raw = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if mark not in raw:
                continue
            texts = grading.assistant_texts_in_file(raw)
            found.append((st.st_mtime, path, texts))
    if not found:
        return None
    _, path, texts = max(found, key=lambda item: item[0])
    joined = "\n".join(texts)
    full = ctx.content.full_markers(profile)
    allc = grading.counts(joined)
    return {
        "path": rel(path, ctx.out),
        "assistant_entries": len(texts),
        "all_assistant_counts": allc,
        "last_assistant_counts": grading.counts(texts[-1]) if texts else {},
        "tag_count": grading.tag_count(joined, tag),
        "full_present": all(allc.get(m, 0) >= 1 for m in full),
        "duplicated": any(allc.get(m, 0) > 1 for m in full),
        "stop_reasons": grading.stop_reasons_in_file(path.read_text(encoding="utf-8", errors="replace"))[-5:],
    }


# ---------------- interactive run ----------------
def run_interactive(ctx: Context, tool: Tool, condition: str, run_index: int) -> dict:
    a = ctx.args
    fault, kind = grading.split_condition(condition)
    profile = "long" if fault == "FLONG" else "short"
    mark = "RUN" + secrets.token_hex(8)
    tag = "〔x" + secrets.token_hex(3) + "〕" if (kind in ("once", "tag")) else None
    run_id = f"run-{run_index}-{mark}"
    ev = ctx.out / "runs" / tool.name / condition / run_id
    ev.mkdir(parents=True, exist_ok=False)
    home = ctx.home(tool, run_id)
    cwd = ctx.cwd(tool)
    tool.seed(home, cwd, ctx.mock.base_url)
    started = now_ms()
    ctx.mock.refresh()
    since_seq = max((e["seq"] for e in ctx.mock.entries), default=0)
    once = None
    if kind == "once":
        once = {"fault": fault, "match": mark, "tag": tag}
    elif kind == "tag":
        once = {"fault": "F0", "match": mark, "tag": tag}
    ctx.mock.control({"reset": True, "always": fault if kind == "always" else "F0", "profile": profile, "once": once})

    record = {"tool": tool.name, "expected_version": tool.expected, "mode": "interactive", "condition": condition,
              "run_index": run_index, "mark": mark, "tag": tag, "profile": profile, "started_at": iso(started),
              "mock": {"instance": ctx.mock.instance, "port": ctx.mock.port}, "invalid": None,
              "timeline": {}, "evidence_dir": rel(ev, ctx.out)}
    session = f"s{secrets.token_hex(3)}"
    flag = ev / ".go"
    raw_path = ev / "raw.bin"
    mid = None
    prefin = None
    overlap = None
    final_view = ""
    complete = None
    samples = []
    next_req = None
    followups: list[dict] = []
    t_enter = None
    t_followup = None
    exe = None
    timeout = False
    try:
        command = (f"while [ ! -e {shlex.quote(str(flag))} ]; do sleep 0.05; done; exec "
                   + shlex.join(ctx.launch(tool, home, "interactive", None)))
        ctx.tmux.new(session, cwd, command)
        ctx.tmux.pipe(session, raw_path)
        flag.touch()
        # gate 1: wait for the input box, refuse any confirmation prompt
        screen, ready, danger = "", False, []
        deadline = time.time() + a.gate_s
        while time.time() < deadline:
            screen = ctx.tmux.capture(session)
            ready, danger = tool.gate(screen)
            if danger or ready:
                break
            time.sleep(0.25)
        time.sleep(0.5)
        screen = ctx.tmux.capture(session)
        ready, danger = tool.gate(screen)
        (ev / "gate.txt").write_text(screen, encoding="utf-8")
        if danger or not ready:
            raise SetupError(f"input gate: ready={ready}, danger={danger}")
        pid = int(ctx.tmux.display(session, "#{pane_pid}") or 0)
        exe = ctx.executed(pid) if pid else None
        ctx.pids.append({"pid": pid, "tool": tool.name, "run": run_id})
        # type, then gate 2 before Enter: the typed prompt is on screen, nothing would eat the key
        ctx.tmux.keys(session, f"{mark} {PROMPT}", literal=True)
        typed = wait_for(lambda: (lambda s: s if mark in grading.compact(s) else None)(ctx.tmux.capture(session)), 10)
        ready, danger = tool.gate(typed or "")
        (ev / "prompt-gate.txt").write_text(typed or "", encoding="utf-8")
        if not typed or danger:
            raise SetupError(f"prompt gate: typed={bool(typed)}, danger={danger}")
        ctx.tmux.keys(session, "Enter")
        t_enter = now_ms()

        last_marker = ctx.content.last_marker(profile)
        first_partial = ctx.content.partial_markers(profile)[0]
        last_screen, last_change = "", time.time()
        last_req_count, last_req_change = 0, time.time()
        last_sample = None
        begin = time.time()
        done_reason = None
        next_slow = 0.0
        reqs, main = [], []
        while True:
            t = time.time()
            screen = ctx.tmux.capture(session)
            if screen != last_screen:
                last_screen, last_change = screen, t
            c = grading.compact(screen)
            tags_on = c.count(tag) if tag else 0
            visible = grading.counts(screen)
            sample = (tags_on, len(visible), sum(visible.values()), visible.get(first_partial, 0),
                      max(visible) if visible else None, tuple(grading.notices(screen, ctx.content)))
            if sample != last_sample:
                samples.append({"t_ms": now_ms(), "tag_on_screen": sample[0], "distinct_markers": sample[1],
                                "total_markers": sample[2], "first_partial_count": sample[3],
                                "max_marker": sample[4], "notices": list(sample[5])})
                last_sample = sample
            if tag and tags_on and visible.get(first_partial, 0) >= 2 and overlap is None:
                # the failed partial and a second copy of its first paragraph are on screen together
                overlap = {"text": screen, "ts_ms": now_ms(), "tag_count": tags_on,
                           "first_partial_count": visible.get(first_partial, 0), "total_markers": sum(visible.values())}
                (ev / "overlap.txt").write_text(screen, encoding="utf-8")
                write_json(ev / "overlap.json", {k: v for k, v in overlap.items() if k != "text"})
            if tag and tags_on and mid is None:
                mid = {"text": screen, "ts_ms": now_ms(), "trigger": "tag", "tag_count": tags_on}
                (ev / "mid.txt").write_text(screen, encoding="utf-8")
                write_json(ev / "mid.json", {k: v for k, v in mid.items() if k != "text"})
            if fault == "FLONG" and prefin is None and "【L150】" in c:
                prefin = {"text": screen, "ts_ms": now_ms(),
                          "complete": bool(re.search(tool.banner_re, screen)) and mark in c}
                (ev / "prefin.txt").write_text(screen, encoding="utf-8")
            # the screen is polled every poll_s; the mock log and pane state are slower
            slow = t >= next_slow
            if slow:
                next_slow = t + a.slow_poll_s
                ctx.mock.refresh()
                reqs = marked(ctx, mark, tag, since_seq)
                main = [r for r in reqs if not r["aux"] and r["stream"]]
            if len(reqs) != last_req_count:
                last_req_count, last_req_change = len(reqs), t
            settled = t - last_change >= a.settle_s
            final_visible = f"【{last_marker}】" in c
            if kind == "always":
                if main and t - last_req_change >= a.quiet_s and t - last_change >= a.quiet_s:
                    done_reason = "persistent fault went quiet"
            elif kind in ("pre", "post", "tag"):
                if main and final_visible and settled:
                    done_reason = "healthy answer displayed and settled"
            else:
                faulted = [r for r in main if r["fault_source"] == "once"]
                retried = faulted and any(r["seq"] > faulted[0]["seq"] and r["fault"] == "F0" and r["ending"] == "clean"
                                          for r in main)
                if retried and final_visible and settled:
                    done_reason = "retry displayed and settled"
                elif faulted and grading.no_retry_due(True, bool(retried), last_req_change, last_change, t, a.quiet_s):
                    done_reason = "no retry within the quiet window"
            if done_reason is None and slow and ctx.tmux.display(session, "#{pane_dead}") == "1":
                done_reason = "subject exited"
            if done_reason is None and t - begin > a.max_run_s:
                done_reason, timeout = "max run time reached", True
            if done_reason:
                break
            time.sleep(a.poll_s)
        record["timeline"]["done_reason"] = done_reason
        final_view = ctx.tmux.capture(session)
        (ev / "final-view.txt").write_text(final_view, encoding="utf-8")
        (ev / "final-history.txt").write_text(ctx.tmux.capture(session, history=True), encoding="utf-8")
        cfinal = grading.compact(final_view)
        complete = bool(re.search(tool.banner_re, final_view)) and mark in cfinal
        record["timeline"]["final_ms"] = now_ms()

        # next-turn witness: what does the client send after this turn?
        if a.followup and kind != "always" and ctx.tmux.display(session, "#{pane_dead}") != "1":
            ready, danger = tool.gate(ctx.tmux.capture(session))
            if ready and not danger:
                ctx.mock.control({"profile": "ack", "once": None, "always": "F0"})
                ctx.tmux.keys(session, FOLLOWUP, literal=True)
                typed = wait_for(lambda: (lambda s: s if grading.compact(FOLLOWUP) in grading.compact(s) else None)(ctx.tmux.capture(session)), 10)
                ready, danger = tool.gate(typed or "")
                if typed and not danger:
                    t_followup = now_ms()
                    ctx.tmux.keys(session, "Enter")

                    def followup_done():
                        ctx.mock.refresh()
                        got = [r for r in marked(ctx, mark, tag, since_seq, start_ms=t_followup - 200) if not r["aux"]]
                        return got or None
                    got = wait_for(followup_done, a.followup_s, step=0.5)
                    time.sleep(1.0)
                    ctx.mock.refresh()
                    followups = marked(ctx, mark, tag, since_seq, start_ms=t_followup - 200)
                    (ev / "followup-view.txt").write_text(ctx.tmux.capture(session), encoding="utf-8")
                    if got:
                        first = got[0]
                        full = ctx.content.full_markers(profile)
                        amc = first["assistant_marker_counts"]
                        next_req = {"seq": first["seq"], "carries_tag": first["carries_tag"],
                                    "assistant_messages": first["assistant_messages"],
                                    "assistant_marker_counts": amc,
                                    "full_present": all(amc.get(m, 0) >= 1 for m in full),
                                    "duplicated": any(amc.get(m, 0) > 1 for m in full)}
                else:
                    record["timeline"]["followup_skipped"] = f"typed={bool(typed)}, danger={danger}"
            else:
                record["timeline"]["followup_skipped"] = f"gate ready={ready}, danger={danger}"
    except SetupError as exc:
        record["invalid"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        record["invalid"] = f"harness exception: {type(exc).__name__}: {exc}"
    finally:
        try:
            ctx.tmux.unpipe(session)
            ctx.tmux.keys(session, "C-c")
            time.sleep(0.4)
            ctx.tmux.keys(session, "C-c")
            wait_for(lambda: ctx.tmux.display(session, "#{pane_dead}") == "1", 3, step=0.2)
        except Exception:  # noqa: BLE001
            pass
        ctx.tmux.kill(session)
        ctx.mock.control({"reset": True})
        time.sleep(0.2)
        ctx.mock.refresh()

    end_ms = t_followup - 200 if t_followup else None
    reqs = marked(ctx, mark, tag, since_seq, end_ms=end_ms)
    copy_requests(ctx, reqs + followups, ev / "requests")
    raw = raw_path.read_bytes() if raw_path.exists() else b""
    full_m = ctx.content.full_markers(profile)
    part_m = ctx.content.partial_markers(profile)
    needles = {"first_marker": f"【{full_m[0]}】", "partial_last": f"【{part_m[-1]}】",
               "first_new": f"【{full_m[len(part_m)]}】", "answer_last": f"【{full_m[-1]}】"}
    raw_info = grading.raw_analysis(raw, tag, ctx.content, grading.load_index(ev / "raw-index.jsonl"), needles)
    write_json(ev / "raw-analysis.json", raw_info)
    with (ev / "samples.jsonl").open("w", encoding="utf-8") as handle:
        for s in samples:
            handle.write(json.dumps(s, ensure_ascii=False) + "\n")
    conversation = conversation_witness(ctx, home, tool.session_globs, mark, tag, profile, started)
    obs = {"condition": condition, "mode": "interactive", "profile": profile, "tag": tag, "requests": reqs,
           "final": {"text": final_view, "complete": complete}, "mid": mid, "raw": raw_info,
           "next_request": next_req, "invalid": record["invalid"]}
    result = grading.grade(obs, ctx.content)
    retry_start = next((r["started_ms"] for r in reqs if not r["aux"] and r["fault"] == "F0" and r["stream"]
                        and any(f["seq"] < r["seq"] for f in reqs if f.get("fault_source") == "once" and not f["aux"])), None)
    record.update({
        "duration_s": round((now_ms() - started) / 1000, 1),
        "executed": exe,
        "requests": reqs, "followup_requests": followups,
        "display": {
            "mid": {"ts_ms": mid["ts_ms"], "tag_count": mid["tag_count"],
                    "lag_vs_retry_start_ms": (mid["ts_ms"] - retry_start) if retry_start else None} if mid else None,
            "overlap": {k: v for k, v in overlap.items() if k != "text"} if overlap else None,
            "prefin": {"ts_ms": prefin["ts_ms"], "complete": prefin["complete"],
                       "L_unique": sum(1 for k in grading.counts(prefin["text"]) if k.startswith("L"))} if prefin else None,
            "final_counts": grading.counts(final_view), "final_complete": complete,
            "final_tag_count": grading.tag_count(final_view, tag),
            "samples": len(samples),
            "tag_visible_ms": tag_window(samples),
        },
        "raw": raw_info, "conversation": conversation, "next_request": next_req,
        "timeline": {**record["timeline"], "enter_ms": t_enter, "followup_ms": t_followup, "timeout": timeout},
        "verdict": result["verdict"], "verdict_reason": result["reason"], "fields": result["fields"],
        "checks": result["checks"], "notices_final": result["notices_final"], "notices_raw": result["notices_raw"],
        "observation_inputs": {"condition": condition, "mode": "interactive", "profile": profile, "tag": tag,
                               "requests": reqs, "final": {"complete": complete}, "next_request": next_req,
                               "invalid": record["invalid"]},
    })
    write_json(ev / "record.json", record)
    with (ctx.out / "runs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def tag_window(samples: list[dict]) -> list[list[int]]:
    """[first_ms, last_ms] intervals during which the failed-attempt tag was on screen."""
    out, start = [], None
    for s in samples:
        if s["tag_on_screen"] and start is None:
            start = s["t_ms"]
        elif not s["tag_on_screen"] and start is not None:
            out.append([start, s["t_ms"]])
            start = None
    if start is not None:
        out.append([start, None])
    return out


class SetupError(RuntimeError):
    pass


def wait_for(predicate, timeout: float, step: float = 0.25):
    end = time.time() + timeout
    while time.time() < end:
        value = predicate()
        if value:
            return value
        time.sleep(step)
    return None


# ---------------- non-interactive run ----------------
def run_noninteractive(ctx: Context, tool: Tool, condition: str, run_index: int) -> dict:
    a = ctx.args
    fault, kind = grading.split_condition(condition)
    profile = "long" if fault == "FLONG" else "short"
    mark = "RUN" + secrets.token_hex(8)
    tag = "〔x" + secrets.token_hex(3) + "〕" if kind in ("once", "tag") else None
    run_id = f"run-{run_index}-{mark}"
    ev = ctx.out / "runs-noninteractive" / tool.name / condition / run_id
    ev.mkdir(parents=True, exist_ok=False)
    home = ctx.home(tool, run_id)
    cwd = ctx.cwd(tool)
    tool.seed(home, cwd, ctx.mock.base_url)
    started = now_ms()
    ctx.mock.refresh()
    since_seq = max((e["seq"] for e in ctx.mock.entries), default=0)
    once = {"fault": fault if kind == "once" else "F0", "match": mark, "tag": tag} if kind in ("once", "tag") else None
    ctx.mock.control({"reset": True, "always": fault if kind == "always" else "F0", "profile": profile, "once": once})
    record = {"tool": tool.name, "expected_version": tool.expected, "mode": "noninteractive", "condition": condition,
              "run_index": run_index, "mark": mark, "tag": tag, "profile": profile, "started_at": iso(started),
              "mock": {"instance": ctx.mock.instance, "port": ctx.mock.port}, "invalid": None,
              "evidence_dir": rel(ev, ctx.out)}
    lines = {"stdout": [], "stderr": []}
    lock = threading.Lock()
    last_out = [time.time()]
    code = None
    try:
        proc = subprocess.Popen(ctx.launch(tool, home, "noninteractive", f"{mark} {PROMPT}"), cwd=cwd,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)

        def reader(pipe, name):
            for raw_line in iter(pipe.readline, b""):
                with lock:
                    lines[name].append((now_ms(), raw_line.decode("utf-8", "replace")))
                    last_out[0] = time.time()
            pipe.close()

        threads = [threading.Thread(target=reader, args=(proc.stdout, "stdout"), daemon=True),
                   threading.Thread(target=reader, args=(proc.stderr, "stderr"), daemon=True)]
        for th in threads:
            th.start()
        begin = time.time()
        last_count, last_req_change = 0, begin
        while proc.poll() is None:
            t = time.time()
            ctx.mock.refresh()
            reqs = [r for r in marked(ctx, mark, tag, since_seq)]
            if len(reqs) != last_count:
                last_count, last_req_change = len(reqs), t
            main = [r for r in reqs if not r["aux"] and r["stream"]]
            faulted = [r for r in main if r["fault_source"] == "once"]
            retried = faulted and any(r["seq"] > faulted[0]["seq"] and r["fault"] == "F0" and r["ending"] == "clean" for r in main)
            if kind == "once" and faulted and grading.no_retry_due(True, bool(retried), last_req_change, last_out[0], t, a.quiet_s):
                code = "terminated_no_retry"
                break
            if t - begin > a.max_run_s:
                code = "terminated_timeout"
                break
            time.sleep(0.5)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        else:
            code = proc.returncode
        for th in threads:
            th.join(timeout=3)
    except Exception as exc:  # noqa: BLE001
        record["invalid"] = f"harness exception: {type(exc).__name__}: {exc}"
    ctx.mock.control({"reset": True})
    time.sleep(0.2)
    ctx.mock.refresh()
    reqs = marked(ctx, mark, tag, since_seq)
    copy_requests(ctx, reqs, ev / "requests")
    stdout = "".join(x for _, x in lines["stdout"])
    stderr = "".join(x for _, x in lines["stderr"])
    (ev / "stdout.txt").write_text(stdout, encoding="utf-8")
    (ev / "stderr.txt").write_text(stderr, encoding="utf-8")
    with (ev / "output-timeline.jsonl").open("w", encoding="utf-8") as handle:
        for name in ("stdout", "stderr"):
            for t_ms, text in lines[name]:
                handle.write(json.dumps({"stream": name, "t_ms": t_ms, "text": text}, ensure_ascii=False) + "\n")
    conversation = conversation_witness(ctx, home, tool.session_globs, mark, tag, profile, started)
    obs = {"condition": condition, "mode": "noninteractive", "profile": profile, "tag": tag, "requests": reqs,
           "final": {"text": stdout, "complete": None}, "mid": None, "raw": None, "stderr": stderr,
           "exit_code": code, "invalid": record["invalid"]}
    result = grading.grade(obs, ctx.content)
    record.update({
        "duration_s": round((now_ms() - started) / 1000, 1), "exit_code": code, "requests": reqs,
        "display": {"final_counts": grading.counts(stdout), "final_tag_count": grading.tag_count(stdout, tag)},
        "conversation": conversation,
        "verdict": result["verdict"], "verdict_reason": result["reason"], "fields": result["fields"],
        "checks": result["checks"], "notices_final": result["notices_final"], "notices_raw": [],
        "observation_inputs": {"condition": condition, "mode": "noninteractive", "profile": profile, "tag": tag,
                               "requests": reqs, "final": {"complete": None}, "exit_code": code,
                               "invalid": record["invalid"]},
    })
    write_json(ev / "record.json", record)
    with (ctx.out / "runs-noninteractive.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# ---------------- probe / matrix ----------------
def probe(ctx: Context, tool: Tool) -> dict:
    run_id = "probe-" + secrets.token_hex(4)
    home = ctx.home(tool, run_id)
    cwd = ctx.cwd(tool)
    tool.seed(home, cwd, ctx.mock.base_url)
    (ctx.out / "probes").mkdir(parents=True, exist_ok=True)
    session = f"p{secrets.token_hex(3)}"
    raw_path = ctx.out / "probes" / f"{tool.name}.raw.bin"
    flag = ctx.out / "probes" / f".{tool.name}.go"
    command = (f"while [ ! -e {shlex.quote(str(flag))} ]; do sleep 0.05; done; exec "
               + shlex.join(ctx.launch(tool, home, "interactive", None)))
    ctx.tmux.new(session, cwd, command)
    ctx.tmux.pipe(session, raw_path)
    flag.touch()
    screen, ready, danger = "", False, []
    deadline = time.time() + ctx.args.gate_s
    while time.time() < deadline:
        screen = ctx.tmux.capture(session)
        ready, danger = tool.gate(screen)
        if ready or danger:
            break
        time.sleep(0.25)
    time.sleep(1.0)
    screen = ctx.tmux.capture(session)
    ready, danger = tool.gate(screen)
    pid = int(ctx.tmux.display(session, "#{pane_pid}") or 0)
    exe = ctx.executed(pid) if pid else None
    ctx.pids.append({"pid": pid, "tool": tool.name, "run": run_id})
    (ctx.out / "probes" / f"{tool.name}.txt").write_text(screen, encoding="utf-8")
    ctx.tmux.unpipe(session)
    ctx.tmux.keys(session, "C-c")
    time.sleep(0.4)
    ctx.tmux.keys(session, "C-c")
    time.sleep(0.5)
    ctx.tmux.kill(session)
    flag.unlink(missing_ok=True)
    raw = raw_path.read_bytes() if raw_path.exists() else b""
    result = {"tool": tool.name, "ready": ready, "danger": danger, "banner": bool(re.search(tool.banner_re, screen)),
              "executed": exe, "raw": {k: v for k, v in grading.raw_analysis(raw, None, ctx.content).items()
                                       if k != "notices"}, "at": iso(), "tmux": [ctx.tmux.width, ctx.tmux.height],
              "sandbox": ctx.args.sandbox}
    write_json(ctx.out / "probes" / f"{tool.name}.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def harness_hashes() -> dict:
    files = ["mock.mjs", "content.json", "runner.py", "grading.py", "version_witness.py", "rawtap.py"]
    return {name: version_witness.sha256_file(HERE / name) for name in files}


def start_mock(ctx: Context, label: str) -> None:
    a = ctx.args
    if a.port and port_in_use(a.port):
        raise RuntimeError(f"port {a.port} is already in use; refusing to reuse a mock this runner did not start")
    ctx.mock = Mock(ctx.out, a.node, HERE / "mock.mjs", HERE / "content.json", a.port, a.delay, a.long_delay,
                    a.continuation, label)


def matrix(ctx: Context) -> int:
    a = ctx.args
    label = dt.datetime.now().strftime("%Y%m%dT%H%M%S") + f"-{os.getpid()}"
    tools = [ctx.tools[name] for name in a.tools]
    conditions = a.conditions.split(",") if a.conditions else DEFAULT_CONDITIONS
    for c in conditions:
        grading.split_condition(c)
    manifest_path = ctx.out / f"manifest-{label}.json"
    before = version_witness.collect(tools_spec(ctx), a.path_env, a.node, extra_files(ctx))
    write_json(ctx.out / f"versions-before-{label}.json", before)
    version_witness.check_expected(before)
    start_mock(ctx, label)
    ctx.tmux = Tmux(ctx.out, a.tmux_width, a.tmux_height) if a.mode == "interactive" else None
    started = now_ms()
    manifest = {"label": label, "started_at": iso(started), "argv": sys.argv, "mode": a.mode, "tools": a.tools,
                "conditions": conditions, "runs": a.runs, "harness_sha256": harness_hashes(),
                "mock": ctx.mock.ready, "tmux": [a.tmux_width, a.tmux_height] if ctx.tmux else None,
                "sandbox": a.sandbox, "quiet_s": a.quiet_s, "settle_s": a.settle_s, "poll_s": a.poll_s,
                "slow_poll_s": a.slow_poll_s,
                "followup": a.followup, "card": a.card, "card_sha256": version_witness.sha256_file(Path(a.card)) if a.card else None}
    write_json(manifest_path, manifest)
    status = 0
    try:
        for tool in tools:
            if a.mode == "interactive":
                probe_path = ctx.out / "probes" / f"{tool.name}.json"
                if not probe_path.exists():
                    raise RuntimeError(f"no probe for {tool.name}; run `runner.py probe` first")
                pdata = json.loads(probe_path.read_text(encoding="utf-8"))
                if not pdata.get("ready") or pdata.get("danger"):
                    raise RuntimeError(f"probe gate failed for {tool.name}: {pdata}")
            baseline_ok = True
            for condition in conditions:
                if not baseline_ok and condition not in BASELINE and not condition.startswith("F0"):
                    print(json.dumps({"tool": tool.name, "condition": condition, "skipped": "baseline failed"}), flush=True)
                    continue
                for i in range(1, a.runs + 1):
                    run = run_interactive if a.mode == "interactive" else run_noninteractive
                    rec = run(ctx, tool, condition, i)
                    if condition in BASELINE and rec["verdict"] not in ("healthy", "tag_visible"):
                        baseline_ok = False
                    print(json.dumps({"tool": tool.name, "condition": condition, "run": i, "verdict": rec["verdict"],
                                      "requests": len(rec["requests"]), "seconds": rec["duration_s"],
                                      "reason": rec["verdict_reason"]}, ensure_ascii=False), flush=True)
            if not baseline_ok:
                status = 3
    finally:
        if ctx.tmux:
            ctx.tmux.kill_server()
        ctx.mock.stop()
        after = version_witness.collect(tools_spec(ctx), a.path_env, a.node, extra_files(ctx))
        write_json(ctx.out / f"versions-after-{label}.json", after)
        diff = version_witness.compare(before, after)
        manifest.update({"ended_at": iso(), "versions_equal": not diff, "version_diff": diff, "pids": ctx.pids,
                         "status": status})
        write_json(manifest_path, manifest)
        if diff:
            print(json.dumps({"VERSION_DRIFT": diff}, ensure_ascii=False), flush=True)
            status = 4
    return status


def tools_spec(ctx: Context) -> list[dict]:
    return [{"name": t.name, "launcher": t.binary, "expected": t.expected} for t in ctx.tools.values()
            if t.name in ctx.args.tools and t.name != "fake"]


def extra_files(ctx: Context) -> dict:
    files = {f"harness:{k}": str(HERE / k) for k in ("mock.mjs", "content.json", "runner.py", "grading.py", "version_witness.py", "rawtap.py")}
    if ctx.args.card:
        files["card"] = ctx.args.card
    return files


def do_probe(ctx: Context) -> int:
    label = "probe-" + dt.datetime.now().strftime("%Y%m%dT%H%M%S") + f"-{os.getpid()}"
    start_mock(ctx, label)
    ctx.tmux = Tmux(ctx.out, ctx.args.tmux_width, ctx.args.tmux_height)
    ok = True
    try:
        for name in ctx.args.tools:
            result = probe(ctx, ctx.tools[name])
            ok &= bool(result["ready"]) and not result["danger"]
    finally:
        ctx.tmux.kill_server()
        ctx.mock.stop()
    return 0 if ok else 1


def do_regrade(ctx: Context) -> int:
    rows = []
    changed = 0
    for record_path in sorted(ctx.out.glob("runs*/**/record.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        obs = grading.load_observation(record_path.parent, ctx.content)
        result = grading.grade(obs, ctx.content)
        row = {"evidence_dir": rel(record_path.parent, ctx.out), "recorded": record.get("verdict"),
               "regraded": result["verdict"], "reason": result["reason"], "regraded_at": iso()}
        changed += row["recorded"] != row["regraded"]
        rows.append(row)
    path = ctx.out / "regrade.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"regraded": len(rows), "changed": changed, "written": str(path)}, ensure_ascii=False))
    return 0


def do_egress(ctx: Context) -> int:
    a = ctx.args
    names = {"claude", "codex", "node", "kimi", "env", "sandbox-exec"}
    predicate = 'eventMessage CONTAINS "deny(1) network-outbound"'
    r = sh("log", "show", "--style", "ndjson", "--start", a.start, "--end", a.end, "--predicate", predicate, timeout=600)
    hits = []
    for line in r.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = item.get("eventMessage", "")
        m = re.search(r"Sandbox: ([^()]+)\((\d+)\) deny\(1\) network-outbound (\S+)", msg)
        if m and m.group(1) in names:
            hits.append({"time": item.get("timestamp"), "process": m.group(1), "pid": int(m.group(2)), "target": m.group(3)})
    summary = {}
    for h in hits:
        key = f"{h['process']} -> {h['target']}"
        summary[key] = summary.get(key, 0) + 1
    out = {"window": [a.start, a.end], "denials": len(hits), "by_target": summary, "first": hits[:20]}
    write_json(ctx.out / "egress.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def do_lsregister(ctx: Context) -> int:
    r = sh(LSREGISTER, "-dump", timeout=300)
    paths = sorted({line.split("path:", 1)[1].strip() for line in r.stdout.splitlines()
                    if "path:" in line and "Claude Code URL Handler" in line})
    out = {"at": iso(), "claude_url_handler_paths": paths}
    write_json(ctx.out / "lsregister.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def parse_pairs(items: list[str] | None, what: str) -> dict:
    out = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--{what} expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def build_tools(args) -> dict[str, Tool]:
    bins = parse_pairs(args.bin, "bin")
    expect = parse_pairs(args.expect, "expect")
    tools = {}
    for name in args.tools:
        if name not in TOOL_CLASSES:
            raise SystemExit(f"unknown tool {name}")
        binary = bins.get(name) or shutil.which(name)
        if not binary:
            raise SystemExit(f"no binary for {name}: pass --bin {name}=PATH")
        if name == "fake":
            tools[name] = Fake(binary, expect.get(name), args.fake_mode)
        else:
            tools[name] = TOOL_CLASSES[name](binary, expect.get(name))
    return tools


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("action", choices=["probe", "matrix", "regrade", "summarize", "egress", "lsregister"])
    p.add_argument("--out", required=True, help="evidence root (outside the public repo)")
    p.add_argument("--tools", nargs="+", default=["claude", "codex"])
    p.add_argument("--mode", choices=["interactive", "noninteractive"], default="interactive")
    p.add_argument("--conditions", default=None, help="comma list, default " + ",".join(DEFAULT_CONDITIONS))
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--bin", action="append", help="NAME=PATH (default: PATH lookup)")
    p.add_argument("--expect", action="append", help="NAME=VERSION; version must appear in `--version` output")
    p.add_argument("--node", default=shutil.which("node") or "node")
    p.add_argument("--path-env", default=DEFAULT_PATH_ENV, help="PATH given to subjects under env -i")
    p.add_argument("--port", type=int, default=0, help="0 = ephemeral; a busy port is refused")
    p.add_argument("--delay", type=int, default=20, help="frame delay (ms), short answers")
    p.add_argument("--long-delay", type=int, default=150, help="frame delay (ms), long answers")
    p.add_argument("--continuation", choices=["restart", "continue", "documented"], default="restart")
    p.add_argument("--tmux-width", type=int, default=110)
    p.add_argument("--tmux-height", type=int, default=400)
    p.add_argument("--quiet-s", type=float, default=60.0)
    p.add_argument("--settle-s", type=float, default=3.0)
    p.add_argument("--poll-s", type=float, default=0.03, help="screen capture interval")
    p.add_argument("--slow-poll-s", type=float, default=0.3, help="mock log / pane state interval")
    p.add_argument("--gate-s", type=float, default=30.0)
    p.add_argument("--max-run-s", type=float, default=300.0)
    p.add_argument("--followup-s", type=float, default=60.0)
    p.add_argument("--no-followup", dest="followup", action="store_false")
    p.add_argument("--no-sandbox", dest="sandbox", action="store_false")
    p.add_argument("--card", default=None, help="experiment card to hash into the manifest")
    p.add_argument("--fake-mode", default="retract")
    p.add_argument("--start", help="egress: window start (local time, `log show` format)")
    p.add_argument("--end", help="egress: window end")
    args = p.parse_args(argv)
    if args.quiet_s < grading.MIN_QUIET_S:
        raise SystemExit(f"--quiet-s must be >= {grading.MIN_QUIET_S}")
    Path(args.out).mkdir(parents=True, exist_ok=True)
    if args.action in ("summarize",):
        import summarize
        return summarize.main([args.out])
    tools = build_tools(args) if args.action in ("probe", "matrix") else {}
    ctx = Context(args, tools)
    if args.action == "probe":
        return do_probe(ctx)
    if args.action == "matrix":
        return matrix(ctx)
    if args.action == "regrade":
        return do_regrade(ctx)
    if args.action == "egress":
        if not args.start or not args.end:
            raise SystemExit("egress needs --start and --end")
        return do_egress(ctx)
    return do_lsregister(ctx)


if __name__ == "__main__":
    sys.exit(main())
