"""A stand-in TUI for calibrating witness/stall's clocks, no network.

  fake_subject.py START_DELAY FREEZE_ON FREEZE_S

Prints a banner and the empty-input-box text after START_DELAY seconds, then
echoes keys in raw mode. When the draft first equals FREEZE_ON it sleeps
FREEZE_S seconds before echoing again (the input thread blocked). Enter on
"/exit" leaves.
"""
import os
import sys
import termios
import time
import tty

start_delay, freeze_on, freeze_s = float(sys.argv[1]), sys.argv[2], float(sys.argv[3])
time.sleep(start_delay)
out = sys.stdout.buffer
out.write(b"metacodes v0.0.0-fake\r\n")
out.write(b'> Try "fix typecheck errors"\r\n')
out.flush()
fd = sys.stdin.fileno()
saved = termios.tcgetattr(fd)
tty.setraw(fd)
draft = b""
frozen = False
try:
    while True:
        ch = os.read(fd, 1)
        if not ch:
            break
        if ch in (b"\r", b"\n"):
            if draft == b"/exit":
                break
            draft = b""
            out.write(b"\r\n")
            out.flush()
            continue
        draft += ch
        if not frozen and freeze_on and draft.decode("latin-1") == freeze_on:
            frozen = True
            time.sleep(freeze_s)
        out.write(b"\r> " + draft)
        out.flush()
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, saved)
