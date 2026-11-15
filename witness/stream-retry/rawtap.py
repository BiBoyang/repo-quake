#!/usr/bin/env python3
"""tmux pipe-pane tap: append the pane's output bytes to RAW and index each chunk.

  rawtap.py RAW INDEX      (stdin = pane output, as given by `tmux pipe-pane -o`)

INDEX is JSONL, one line per read: {"t_ms": wall-clock ms, "offset": byte offset in RAW,
"len": bytes}. The clock is the same one the mock stamps its delivery log with, so a
byte offset in RAW (the failed attempt's tag, a retry notice) maps to a time that can be
compared with the retry request's start. Stdlib only; never rewrites RAW.
"""
import json
import os
import sys
import time


def main() -> int:
    raw_path, index_path = sys.argv[1], sys.argv[2]
    offset = os.path.getsize(raw_path) if os.path.exists(raw_path) else 0
    with open(raw_path, "ab", buffering=0) as raw, open(index_path, "a", encoding="utf-8") as index:
        while True:
            chunk = os.read(0, 65536)
            if not chunk:
                return 0
            t_ms = int(time.time() * 1000)
            raw.write(chunk)
            index.write(json.dumps({"t_ms": t_ms, "offset": offset, "len": len(chunk)}) + "\n")
            index.flush()
            offset += len(chunk)


if __name__ == "__main__":
    sys.exit(main())
