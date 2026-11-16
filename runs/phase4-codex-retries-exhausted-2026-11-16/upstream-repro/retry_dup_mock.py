#!/usr/bin/env python3
"""Minimal OpenAI Responses mock for openai/codex#47538.

Attempt 1 streams the first half of the answer and closes the connection
without response.completed; later attempts stream the whole answer.
With --always every attempt is cut, so the retry budget runs out.

    python3 retry_dup_mock.py [--port 8765] [--always]
"""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LINES = [f"[{i:02d}] line {i:02d} of the answer" for i in range(1, 41)]
CUT = 20      # lines sent before the connection is cut
DELAY = 0.15  # seconds per delta, so the retry window is long enough to see


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    attempts = 0

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):  # model list
        body = json.dumps({"object": "list", "data": [
            {"id": "mock-model", "object": "model", "created": 0, "owned_by": "mock"}]}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        if "json_schema" in json.dumps(req.get("text", {})):  # thread-title side request
            return self.stream(['{"title": "retry test"}'], complete=True, delay=0)
        Handler.attempts += 1
        cut = ARGS.always or Handler.attempts == 1
        print(f"attempt {Handler.attempts}: {'cut after ' + str(CUT) + ' lines' if cut else 'complete'}", flush=True)
        self.stream(LINES[:CUT] if cut else LINES, complete=not cut, delay=DELAY)

    def stream(self, lines, complete, delay):
        n = Handler.attempts
        msg = {"id": f"msg_{n}", "type": "message", "role": "assistant"}
        resp = {"id": f"resp_{n}", "object": "response", "created_at": int(time.time()), "model": "mock-model"}
        text = "".join(f"{line}\n" for line in lines)
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("connection", "close")  # body ends when the socket closes
        self.end_headers()

        def send(kind, **data):
            self.wfile.write(f"event: {kind}\ndata: {json.dumps({'type': kind, **data})}\n\n".encode())
            self.wfile.flush()

        send("response.created", response={**resp, "status": "in_progress", "output": []})
        send("response.output_item.added", output_index=0, item={**msg, "status": "in_progress", "content": []})
        send("response.content_part.added", item_id=msg["id"], output_index=0, content_index=0,
             part={"type": "output_text", "text": ""})
        for line in lines:
            send("response.output_text.delta", item_id=msg["id"], output_index=0, content_index=0, delta=f"{line}\n")
            time.sleep(delay)
        if complete:
            done = {**msg, "status": "completed", "content": [{"type": "output_text", "text": text, "annotations": []}]}
            send("response.output_text.done", item_id=msg["id"], output_index=0, content_index=0, text=text)
            send("response.output_item.done", output_index=0, item=done)
            send("response.completed", response={**resp, "status": "completed", "output": [done],
                                                 "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}})
        self.close_connection = True


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--always", action="store_true", help="cut every attempt")
    ARGS = p.parse_args()
    ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()
