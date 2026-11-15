#!/usr/bin/env python3
"""Version and hash witness for the subjects, the mock and the harness (stdlib only).

Hashes what actually executes: a launcher is resolved through symlinks, and an npm
`codex.js` launcher is followed to the native binary it execve()s
(node_modules/@openai/codex-<platform>/vendor/<triple>/bin/codex). The interpreter that
runs a script launcher (node) is hashed too.

  version_witness.py collect --out before.json --tool claude=PATH --expect claude=2.1.282 \
      [--tool codex=PATH ...] [--file mock=PATH ...] [--node PATH] [--path-env PATH]
  version_witness.py compare before.json after.json      # exit 1 on any drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PLATFORM_PACKAGES = {
    ("darwin", "arm64"): ("@openai/codex-darwin-arm64", "aarch64-apple-darwin"),
    ("darwin", "x86_64"): ("@openai/codex-darwin-x64", "x86_64-apple-darwin"),
    ("linux", "aarch64"): ("@openai/codex-linux-arm64", "aarch64-unknown-linux-musl"),
    ("linux", "x86_64"): ("@openai/codex-linux-x64", "x86_64-unknown-linux-musl"),
}


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stat_line(path: Path) -> dict:
    st = path.stat()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def platform_key() -> tuple[str, str]:
    return sys.platform if sys.platform != "darwin" else "darwin", platform.machine()


def codex_native(launcher_real: Path, key: tuple[str, str] | None = None) -> Path | None:
    """The native binary an npm codex.js launcher hands over to, or None."""
    pkg_name, triple = PLATFORM_PACKAGES.get(key or platform_key(), (None, None))
    if not pkg_name:
        return None
    package_root = launcher_real.parent.parent
    candidates = [
        package_root / "node_modules" / pkg_name / "vendor" / triple / "bin" / "codex",
        package_root.parent / pkg_name.split("/")[1] / "vendor" / triple / "bin" / "codex",
        package_root / "vendor" / triple / "bin" / "codex",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def shebang(path: Path) -> str | None:
    try:
        with open(path, "rb") as handle:
            head = handle.read(256)
    except OSError:
        return None
    if not head.startswith(b"#!"):
        return None
    return head.split(b"\n", 1)[0][2:].decode("utf-8", "replace").strip()


def resolve_executed(launcher: str, key: tuple[str, str] | None = None) -> dict:
    path = Path(launcher)
    real = Path(os.path.realpath(path))
    info = {"launcher": str(path), "realpath": str(real), "realpath_sha256": sha256_file(real),
            "realpath_stat": stat_line(real), "shebang": shebang(real), "native": None}
    if real.name == "codex.js":
        native = codex_native(real, key)
        info["native"] = ({"path": str(native), "sha256": sha256_file(native), "stat": stat_line(native)}
                          if native else {"path": None, "error": "native codex binary not found next to codex.js"})
    elif info["shebang"] is None:
        info["native"] = {"path": str(real), "sha256": info["realpath_sha256"], "stat": info["realpath_stat"]}
    return info


def tool_version(launcher: str, path_env: str, home: Path) -> str:
    env = {"PATH": path_env, "HOME": str(home), "LANG": "en_US.UTF-8", "TERM": "dumb"}
    r = subprocess.run([launcher, "--version"], env=env, capture_output=True, text=True, timeout=30)
    return (r.stdout or r.stderr).strip()


def collect(tools: list[dict], path_env: str, node: str | None, files: dict[str, str]) -> dict:
    """tools: [{name, launcher, expected}]; files: {label: path}."""
    out = {"tools": {}, "files": {}, "runtime": {}}
    with tempfile.TemporaryDirectory(prefix="rq-version-home-") as tmp:
        for spec in tools:
            info = resolve_executed(spec["launcher"])
            info["version"] = tool_version(spec["launcher"], path_env, Path(tmp))
            info["expected"] = spec.get("expected")
            info["expected_ok"] = spec.get("expected") is None or spec["expected"] in info["version"]
            out["tools"][spec["name"]] = info
    for label, path in files.items():
        out["files"][label] = {"path": path, "sha256": sha256_file(path)}
    if node:
        node_real = os.path.realpath(shutil.which(node) or node)
        out["runtime"]["node"] = {"path": node_real, "sha256": sha256_file(node_real),
                                  "version": subprocess.run([node_real, "--version"], capture_output=True, text=True).stdout.strip()}
    tmux = shutil.which("tmux")
    if tmux:
        out["runtime"]["tmux"] = {"path": os.path.realpath(tmux),
                                  "version": subprocess.run([tmux, "-V"], capture_output=True, text=True).stdout.strip()}
    return out


def check_expected(snapshot: dict) -> None:
    bad = {name: info["version"] for name, info in snapshot["tools"].items() if not info["expected_ok"]}
    if bad:
        raise RuntimeError(f"version differs from the expected pin: {bad}")
    missing = {name for name, info in snapshot["tools"].items()
               if info.get("native") and info["native"].get("path") is None}
    if missing:
        raise RuntimeError(f"could not resolve the executed native binary for {sorted(missing)}")


def compare(before: dict, after: dict) -> list[str]:
    diffs = []
    for name in sorted(set(before["tools"]) | set(after["tools"])):
        a, b = before["tools"].get(name), after["tools"].get(name)
        if a is None or b is None:
            diffs.append(f"{name}: present only {'after' if a is None else 'before'}")
            continue
        for key in ("version", "realpath", "realpath_sha256"):
            if a.get(key) != b.get(key):
                diffs.append(f"{name}.{key}: {a.get(key)} -> {b.get(key)}")
        na, nb = a.get("native") or {}, b.get("native") or {}
        if na.get("sha256") != nb.get("sha256") or na.get("path") != nb.get("path"):
            diffs.append(f"{name}.native: {na.get('path')}@{na.get('sha256')} -> {nb.get('path')}@{nb.get('sha256')}")
    for label in sorted(set(before["files"]) | set(after["files"])):
        a, b = before["files"].get(label, {}), after["files"].get(label, {})
        if a.get("sha256") != b.get("sha256"):
            diffs.append(f"file {label}: {a.get('sha256')} -> {b.get('sha256')}")
    for label in sorted(set(before.get("runtime", {})) | set(after.get("runtime", {}))):
        a, b = before["runtime"].get(label, {}), after["runtime"].get(label, {})
        if a.get("sha256") != b.get("sha256") or a.get("version") != b.get("version"):
            diffs.append(f"runtime {label}: {a} -> {b}")
    return diffs


def text_report(snapshot: dict) -> str:
    lines = []
    for name, info in snapshot["tools"].items():
        lines += [f"[{name}]", f"version={info['version']}", f"expected={info['expected']}",
                  f"launcher={info['launcher']}", f"realpath={info['realpath']}",
                  f"realpath_sha256={info['realpath_sha256']}"]
        native = info.get("native") or {}
        if native.get("path") and native["path"] != info["realpath"]:
            lines += [f"native={native['path']}", f"native_sha256={native['sha256']}"]
        lines.append("")
    for label, item in snapshot["files"].items():
        lines.append(f"file {label} sha256={item['sha256']}")
    for label, item in snapshot.get("runtime", {}).items():
        lines.append(f"runtime {label} {item}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", required=True)
    c.add_argument("--tool", action="append", default=[], help="NAME=LAUNCHER")
    c.add_argument("--expect", action="append", default=[], help="NAME=VERSION")
    c.add_argument("--file", action="append", default=[], help="LABEL=PATH")
    c.add_argument("--node", default=None)
    c.add_argument("--path-env", default="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin")
    d = sub.add_parser("compare")
    d.add_argument("before")
    d.add_argument("after")
    args = p.parse_args(argv)
    if args.cmd == "compare":
        diffs = compare(json.loads(Path(args.before).read_text()), json.loads(Path(args.after).read_text()))
        print("\n".join(diffs) if diffs else "IDENTICAL")
        return 1 if diffs else 0
    expect = dict(item.split("=", 1) for item in args.expect)
    tools = [{"name": n, "launcher": l, "expected": expect.get(n)} for n, l in (t.split("=", 1) for t in args.tool)]
    files = dict(item.split("=", 1) for item in args.file)
    snapshot = collect(tools, args.path_env, args.node, files)
    out = Path(args.out)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out.with_suffix(".txt").write_text(text_report(snapshot), encoding="utf-8")
    print(text_report(snapshot), end="")
    return 0 if all(info["expected_ok"] for info in snapshot["tools"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
