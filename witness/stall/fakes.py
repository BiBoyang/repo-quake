"""Loopback fakes and a timestamped pty driver for witness/stall, stdlib only.

Every server listens on 127.0.0.1 with an ephemeral port and records what it was
asked, with monotonic timestamps: that log is the delivery proof for the stall.
"""
from __future__ import annotations

import fcntl
import http.server
import json
import os
import pty
import select
import signal
import socket
import struct
import termios
import threading
import time

MODELS = b'{"data":[{"id":"claude-sonnet-4-5","max_tokens":8192,"max_input_tokens":200000}]}'
KEYS = b'{"data":[{"id":"k1","name":"probe key","api_key":"sk-metask-probe-1234"}]}'


def sse_text(text: str) -> bytes:
    return (
        b'data: {"type":"message_start","message":{"id":"m1","role":"assistant","model":"x","usage":{"input_tokens":1,"output_tokens":1}}}\n\n'
        b'data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n\n'
        + ('data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":%s}}\n\n' % json.dumps(text)).encode()
        + b'data: {"type":"content_block_stop","index":0}\n\n'
        b'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":5}}\n\n'
        b'data: {"type":"message_stop"}\n\n'
    )


def sse_tool(tool: str, tool_input: dict, tool_id: str) -> bytes:
    return (
        b'data: {"type":"message_start","message":{"id":"m1","role":"assistant","model":"x","usage":{"input_tokens":1,"output_tokens":1}}}\n\n'
        + ('data: {"type":"content_block_start","index":0,"content_block":{"type":"tool_use","id":"%s","name":"%s","input":{}}}\n\n' % (tool_id, tool)).encode()
        + ('data: {"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":%s}}\n\n' % json.dumps(json.dumps(tool_input))).encode()
        + b'data: {"type":"content_block_stop","index":0}\n\n'
        b'data: {"type":"message_delta","delta":{"stop_reason":"tool_use"},"usage":{"output_tokens":5}}\n\n'
        b'data: {"type":"message_stop"}\n\n'
    )


class Gateway:
    """Anthropic Messages gateway. `models_delay` / `keys_delay`: seconds before
    the answer, or None for an accepted request that is never answered."""

    def __init__(self, models_delay=0.0, keys_delay=0.0, turns=None):
        self.models_delay = models_delay
        self.keys_delay = keys_delay
        self.turns = turns or [sse_text("pong-ok")]
        self.turn_idx = 0
        self.events: list[tuple[float, str, str]] = []
        self.stopping = False
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _hold(self, delay):
                if delay is None:
                    while not outer.stopping:
                        time.sleep(0.05)
                    return False
                time.sleep(delay)
                return True

            def _send(self, body):
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(body)))
                self.send_header("connection", "close")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                outer.events.append((time.monotonic(), "GET", self.path))
                if self.path.startswith("/v1/models"):
                    if self._hold(outer.models_delay):
                        self._send(MODELS)
                        outer.events.append((time.monotonic(), "ANSWERED", self.path))
                elif "/keys" in self.path:
                    if self._hold(outer.keys_delay):
                        self._send(KEYS)
                        outer.events.append((time.monotonic(), "ANSWERED", self.path))
                else:
                    self.send_error(404)

            def do_POST(self):
                n = int(self.headers.get("content-length", 0))
                self.rfile.read(n)
                outer.events.append((time.monotonic(), "POST", self.path))
                if not self.path.startswith("/v1/messages"):
                    self.send_error(404)
                    return
                idx = min(outer.turn_idx, len(outer.turns) - 1)
                outer.turn_idx += 1
                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.send_header("connection", "close")
                self.end_headers()
                try:
                    self.wfile.write(outer.turns[idx])
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.port = self.srv.server_address[1]
        self.url = "http://127.0.0.1:%d/v1/messages" % self.port

    def first(self, method, prefix, after=0.0):
        for t, m, p in list(self.events):
            if m == method and p.startswith(prefix) and t >= after:
                return t
        return None

    def stop(self):
        self.stopping = True
        self.srv.shutdown()
        self.srv.server_close()


class Silent:
    """Accepts TCP connections on 127.0.0.1, reads what arrives, never answers."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(64)
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.accepts: list[float] = []
        self.bytes_in = 0
        self.conns = []
        self.stopping = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while not self.stopping:
            try:
                conn, _ = self.sock.accept()
            except (socket.timeout, OSError):
                continue
            self.accepts.append(time.monotonic())
            self.conns.append(conn)
            threading.Thread(target=self._drain, args=(conn,), daemon=True).start()

    def _drain(self, conn):
        try:
            while not self.stopping:
                data = conn.recv(65536)
                if not data:
                    return
                self.bytes_in += len(data)
        except OSError:
            return

    def stop(self):
        self.stopping = True
        for conn in self.conns:
            try:
                conn.close()
            except OSError:
                pass
        self.sock.close()


class ClassicMcp:
    """Streamable HTTP MCP server with a classic session (MCP-Session-Id).
    Everything is answered except DELETE when `delete_answers` is False."""

    def __init__(self, delete_answers=False):
        self.events: list[tuple[float, str]] = []
        self.stopping = False
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def reply(self, code, obj=None, headers=None):
                body = json.dumps(obj).encode() if obj is not None else b""
                self.send_response(code)
                if obj is not None:
                    self.send_header("Content-Type", "application/json")
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_DELETE(self):
                outer.events.append((time.monotonic(), "DELETE"))
                if not delete_answers:
                    while not outer.stopping:
                        time.sleep(0.05)
                    return
                self.reply(200)

            def do_GET(self):
                outer.events.append((time.monotonic(), "GET"))
                self.reply(405)

            def do_POST(self):
                n = int(self.headers.get("Content-Length", "0"))
                msg = json.loads(self.rfile.read(n))
                method, rid = msg.get("method"), msg.get("id")
                outer.events.append((time.monotonic(), "POST %s" % method))
                if method == "server/discover":
                    return self.reply(400, {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": "Bad Request: not initialized"}})
                if method == "initialize":
                    return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "s", "version": "1"}}}, {"Mcp-Session-Id": "session-1"})
                if method is None or str(method).startswith("notifications/"):
                    return self.reply(202)
                if method == "tools/list":
                    return self.reply(200, {"jsonrpc": "2.0", "id": rid, "result": {"tools": []}})
                return self.reply(200, {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}})

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.port = self.srv.server_address[1]
        self.url = "http://127.0.0.1:%d/mcp" % self.port

    def stop(self):
        self.stopping = True
        self.srv.shutdown()
        self.srv.server_close()


class Pty:
    """The subject on a pseudo-terminal. Every output chunk and every key written
    is timestamped (time.monotonic()). Answers DA1 the way a terminal without the
    Kitty keyboard protocol does; sends nothing else unasked."""

    DA1_QUERY = b"\x1b[c"
    DA1_ANSWER = b"\x1b[?62;22c"

    def __init__(self, argv, env, cwd, rows=30, cols=100):
        self.t0 = time.monotonic()
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.chdir(cwd)
                os.execve(argv[0], argv, env)
            finally:
                os._exit(127)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.buf = bytearray()
        self.chunks: list[tuple[float, int]] = []
        self.writes: list[tuple[float, str, str | None]] = []
        self.lock = threading.Lock()
        self.exit_status = None
        self.exit_t = None
        self._da1_seen = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        while True:
            try:
                ready, _, _ = select.select([self.fd], [], [], 0.05)
            except (OSError, ValueError):
                return
            if not ready:
                continue
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                data = b""
            if not data:
                return
            now = time.monotonic()
            with self.lock:
                self.buf += data
                self.chunks.append((now, len(self.buf)))
                da1 = self.buf.count(self.DA1_QUERY)
            while self._da1_seen < da1:
                self._da1_seen += 1
                self.write(self.DA1_ANSWER, note="DA1 answer")

    def write(self, data: bytes, note: str | None = None) -> float:
        t = time.monotonic()
        try:
            os.write(self.fd, data)
        except OSError:
            pass
        self.writes.append((t, data.decode("latin-1"), note))
        return t

    def type(self, text: str, gap: float = 0.06) -> float:
        last = 0.0
        for ch in text:
            last = self.write(ch.encode())
            time.sleep(gap)
        return last

    def size(self) -> int:
        with self.lock:
            return len(self.buf)

    def arrival(self, end_index: int):
        with self.lock:
            for t, size in self.chunks:
                if size >= end_index:
                    return t
        return None

    def wait_for(self, needle: bytes, timeout: float, start: int = 0):
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                idx = self.buf.find(needle, start)
            if idx >= 0:
                return self.arrival(idx + len(needle))
            if time.monotonic() >= deadline or self.poll_exit():
                with self.lock:
                    idx = self.buf.find(needle, start)
                return self.arrival(idx + len(needle)) if idx >= 0 else None
            time.sleep(0.01)

    def poll_exit(self) -> bool:
        if self.exit_status is not None:
            return True
        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
        except ChildProcessError:
            return True
        if pid == 0:
            return False
        self.exit_status = status
        self.exit_t = time.monotonic()
        return True

    def wait_exit(self, timeout: float):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.poll_exit():
                return self.exit_t
            time.sleep(0.01)
        return None

    def signal(self, sig) -> float:
        t = time.monotonic()
        try:
            os.kill(self.pid, sig)
        except ProcessLookupError:
            pass
        return t

    def kill(self):
        if not self.poll_exit():
            self.signal(signal.SIGKILL)
            self.wait_exit(5)
        try:
            os.close(self.fd)
        except OSError:
            pass

    def rel(self, t):
        return None if t is None else round(t - self.t0, 3)
