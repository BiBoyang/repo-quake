#!/usr/bin/env python3
"""Calibration subject for witness/stream-retry: a tiny alternate-screen chat "TUI".

It talks Chat Completions to the mock, streams the answer onto an alternate screen and
retries once when a stream ends without a terminator. FAKE_MODE picks the display policy:

  retract  drop the failed partial before retrying          -> grader must say retracted
  keep     leave the failed partial on screen, then retry   -> grader must say fork
  double   render every healthy answer twice                 -> a healthy control must fail

`--print PROMPT` is the non-interactive variant (append-only stdout). Stdlib only.
"""
import argparse
import http.client
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path


def stream(base: str, messages: list[dict]):
    url = urllib.parse.urlparse(base)
    conn = http.client.HTTPConnection(url.hostname, url.port, timeout=30)
    body = json.dumps({"model": "mock-model", "stream": True, "messages": messages,
                       "tools": [{"type": "function", "function": {"name": "noop", "parameters": {}}}]})
    finished = False
    try:
        conn.request("POST", "/v1/chat/completions", body, {"content-type": "application/json"})
        resp = conn.getresponse()
        while True:
            line = resp.readline()
            if not line:
                break
            line = line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                finished = True
                break
            choice = json.loads(data)["choices"][0]
            text = (choice.get("delta") or {}).get("content")
            if text:
                yield "delta", text
            if choice.get("finish_reason"):
                finished = True
    except Exception as exc:  # noqa: BLE001 - any transport error is a failed attempt
        yield "error", type(exc).__name__
        return
    finally:
        conn.close()
    yield ("done", None) if finished else ("error", "stream ended without a terminator")


def render(lines: list[str]) -> None:
    sys.stdout.write("\x1b[H\x1b[2J" + "FAKE TUI v1\r\n" + "".join(f"{line}\r\n" for line in lines) + "FAKE> ")
    sys.stdout.flush()


def answer(base: str, history: list[dict], transcript: list[str], mode: str, show) -> str:
    for attempt in range(1, 4):
        start = len(transcript)
        buf, result = "", None
        for kind, value in stream(base, history):
            if kind == "delta":
                buf += value
                transcript[start:] = buf.rstrip("\n").split("\n")
                show(transcript)
            else:
                result = kind
        if result == "done":
            if mode == "double":
                transcript.extend(buf.rstrip("\n").split("\n"))
            show(transcript)
            return buf
        if mode == "retract":
            del transcript[start:]
        transcript.append(f"Retrying ({attempt}/3)")
        show(transcript)
        time.sleep(0.4)
        transcript.pop()
        show(transcript)
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--print", dest="prompt")
    args = ap.parse_args()
    mode = os.environ.get("FAKE_MODE", "retract")
    sessions = Path(os.environ.get("FAKE_SESSIONS", "fake-sessions"))
    sessions.mkdir(parents=True, exist_ok=True)
    log = sessions / f"{os.getpid()}.jsonl"
    if args.prompt is not None:
        # append-only stdout: deltas are printed as they arrive, a failed attempt's text stays
        history = [{"role": "user", "content": args.prompt}]
        for attempt in range(1, 4):
            buf, result = "", None
            for kind, value in stream(args.base_url, history):
                if kind == "delta":
                    sys.stdout.write(value)
                    sys.stdout.flush()
                    buf += value
                else:
                    result = kind
            if result == "done":
                with log.open("a", encoding="utf-8") as h:
                    for m in history + [{"role": "assistant", "content": buf}]:
                        h.write(json.dumps(m, ensure_ascii=False) + "\n")
                return 0
            print(f"Retrying ({attempt}/3)", file=sys.stderr, flush=True)
        return 1
    sys.stdout.write("\x1b[?1049h")
    transcript: list[str] = []
    history: list[dict] = []
    render(transcript)
    for line in sys.stdin:
        prompt = line.rstrip("\n")
        if not prompt:
            render(transcript)
            continue
        transcript.append(f"> {prompt}")
        history.append({"role": "user", "content": prompt})
        render(transcript)
        text = answer(args.base_url, history, transcript, mode, render)
        history.append({"role": "assistant", "content": text})
        with log.open("w", encoding="utf-8") as h:
            for m in history:
                h.write(json.dumps(m, ensure_ascii=False) + "\n")
        render(transcript)
    return 0


if __name__ == "__main__":
    sys.exit(main())
