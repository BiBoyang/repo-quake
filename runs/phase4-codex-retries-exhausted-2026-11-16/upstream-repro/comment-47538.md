Reproduced on codex-cli 0.169.0 (macOS arm64, interactive TUI), with a custom Responses provider pointing at a local mock. On the two questions above: the TUI does not roll back the failed attempt's live text on `Reconnecting...`, and the stream shape is just "attempt 1 stops before `response.completed`, the retry starts the answer over". You can see it if you look during the retry, and it stays if the retries run out.

**When the retry succeeds** (9/9 runs, 3 each: socket closed mid-chunk, clean HTTP end without `response.completed`, and a 200-line answer cut at line 160)

- While the retry streams, attempt 1's text stays in the message, and attempt 2 starts again from line 1 directly below it, in the same cell, with no separator.
- When the retry completes, the message collapses to one copy. The saved session and the next request contain one copy.
- Both copies are on screen for as long as the retry takes to stream: about half a second for a short answer, about 30 s for the 200-line one (200 lines at 150 ms per delta).

**When the retries run out** (6/6 runs: 3 with the socket closed mid-chunk, 3 with a clean end without `response.completed`)

- Every attempt streams the same first half and is cut. The turn ends with `■ stream disconnected before completion: …`, and the final screen keeps all six attempts concatenated in one message (the original plus `Reconnecting... 1/5` to `5/5`).
- The saved session has no assistant message for that turn, so this is display-only, but it does not go away.

The copies are sequential, never interleaved, so the woven text in the original report probably has another cause (#30072).

**Code** (rust-v0.169.0; `on_stream_error` is unchanged on `main` today)

- An error with `will_retry: true` goes to `on_stream_error` ([`protocol.rs:223`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/protocol.rs#L223)), which only updates the status row ([`streaming.rs:517`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/streaming.rs#L517)). `stream_controller` keeps attempt 1's text, and `handle_streaming_delta` appends attempt 2's deltas to it ([`streaming.rs:728`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/streaming.rs#L728)).
- On success, `finalize_completed_assistant_message` consolidates from the completed item ([`streaming.rs:289`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/streaming.rs#L289)), so the final screen is clean.
- When the turn fails, `finalize_turn` ([`turn_runtime.rs:349`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/turn_runtime.rs#L349)) calls `flush_answer_and_plan_streams` ([`streaming.rs:71`](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/tui/src/chatwidget/streaming.rs#L71)) with no completed message, so the concatenated stream becomes the transcript cell.

That matches the analysis earlier in this thread.

Expected: the message shows one attempt at a time. When `Reconnecting...` starts a retry, the failed attempt's text is cleared or visibly marked as discarded.

**Repro**

<details><summary><code>retry_dup_mock.py</code> (Python 3, stdlib only)</summary>

```python
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
```

</details>

```sh
python3 retry_dup_mock.py          # add --always to cut every attempt
MOCK_API_KEY=x codex \
  -c model_provider=mock \
  -c 'model_providers.mock.name="Mock"' \
  -c 'model_providers.mock.base_url="http://127.0.0.1:8765/v1"' \
  -c 'model_providers.mock.wire_api="responses"' \
  -c 'model_providers.mock.env_key="MOCK_API_KEY"' \
  -c 'model="mock-model"'
```

Send any prompt. Lines `[01]`–`[20]` stream, `Reconnecting... 1/5` flashes in the status row, and `[01]` starts again under `[20]` in the same message. Both copies stay for about 6 s; when `[40]` arrives, the message collapses to one copy. With `--always`, every retry adds another copy, and the turn ends with the error and all six copies on screen.

How I looked: the screen was captured every 30 ms in a 110×400 tmux window. Attempt 1's text carries a marker that only the failed attempt emits, so the copies can be told apart. Network access was limited to localhost.

