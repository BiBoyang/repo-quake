#!/usr/bin/env python3
"""Pre-dispatch gate for `runner.py matrix`: the experiment card is the contract.

A matrix starts only with a committed, valid card whose plan and budget cover it, or
with an explicit `--exploratory REASON` that the manifest records. Accounting reads
the manifests already in the evidence root, matched by card sha256, so the budget
spans every invocation under one card instead of resetting with each command.
stdlib only; the rules are in skills/repo-quake/references/experiment-card.md.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent.parent / "skills" / "repo-quake" / "scripts" / "validate_card.py"


class GateError(Exception):
    """The matrix must not start; the message says why."""


def load_validator():
    spec = importlib.util.spec_from_file_location("quake_validate_card", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cell_key(tool: str, mode: str, condition: str) -> str:
    return f"{tool}|{mode}|{condition}"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def card_provenance(card_path: Path) -> dict:
    """The card must be committed and unmodified, so git can date the freeze.

    Whether that commit is on the upstream branch is recorded, not required: only a
    push gives a timestamp the experimenter does not control."""
    path = card_path.resolve()
    where, name = path.parent, path.name
    tracked = _git(where, "ls-files", "--full-name", "--error-unmatch", "--", name)
    if tracked.returncode != 0:
        raise GateError(f"card {card_path} is not tracked by git; commit it before dispatch")
    rel = tracked.stdout.strip()
    if _git(where, "diff", "--quiet", "HEAD", "--", name).returncode != 0:
        raise GateError(f"card {rel} has changes that are not committed; commit them before dispatch")
    log = _git(where, "log", "-1", "--format=%H%x09%cI", "--", name)
    if log.returncode != 0 or "\t" not in log.stdout:
        raise GateError(f"card {rel} has no commit yet; commit it before dispatch")
    commit, committed_at = log.stdout.strip().split("\t", 1)
    upstream = _git(where, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    pushed = None
    if upstream.returncode == 0:
        pushed = _git(where, "merge-base", "--is-ancestor", commit, "@{upstream}").returncode == 0
    return {"path": rel, "commit": commit, "committed_at": committed_at,
            "upstream": upstream.stdout.strip() if upstream.returncode == 0 else None, "pushed": pushed}


def manifest_cells(manifest: dict) -> dict:
    """Runs a manifest dispatched, per cell. The runner counts each run before it
    starts, so a runner that died mid-matrix is still charged correctly; a manifest
    written before this gate existed has no counts and is charged its whole plan."""
    if isinstance(manifest.get("dispatched"), dict):
        return {k: int(v) for k, v in manifest["dispatched"].items()}
    runs = int(manifest.get("runs") or 0)
    mode = manifest.get("mode")
    return {cell_key(t, mode, c): runs for t in manifest.get("tools") or [] for c in manifest.get("conditions") or []}


def prior_usage(out: Path, card_sha: str) -> dict:
    dispatched, invalid, modes = Counter(), Counter(), {}
    for path in sorted(Path(out).glob("manifest-*.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GateError(f"cannot read {path.name} ({exc}); budget accounting needs every manifest")
        if manifest.get("card_sha256") != card_sha:
            continue
        dispatched.update(manifest_cells(manifest))
        invalid.update({k: int(v) for k, v in (manifest.get("invalid") or {}).items()})
        for tool in manifest.get("tools") or []:
            modes.setdefault(tool, set()).add(manifest.get("mode"))
    return {"dispatched": dispatched, "invalid": invalid, "modes": modes}


def check(card: dict, card_sha: str, out: Path, tools: list[str], mode: str, conditions: list[str], runs: int,
          deviation: str | None = None) -> dict:
    """Refuse (GateError) a matrix the card does not cover; otherwise return the
    accounting to store in the manifest."""
    validator = load_validator()
    errors, _ = validator.validate(card)
    if errors:
        raise GateError("card does not validate:\n" + "\n".join(f"- {e}" for e in errors))
    arm_runs = validator.runs_per_arm(card)
    reruns = validator.invalid_reruns(card)
    hosts = Counter(h["name"] for h in card["hosts"])

    refusals = []
    missing_tools = [t for t in tools if t not in hosts]
    if missing_tools:
        refusals.append("tools not among the card's hosts[].name: " + ", ".join(missing_tools))
    missing_conditions = [c for c in conditions if c not in arm_runs]
    if missing_conditions:
        refusals.append("conditions not among the card's arms[].id: " + ", ".join(missing_conditions))
    if refusals:
        raise GateError("; ".join(refusals))

    usage = prior_usage(out, card_sha)
    for tool in tools:
        used = usage["modes"].get(tool, set()) | {mode}
        if len(used) > hosts[tool]:
            refusals.append(f"{tool} would run in {len(used)} modes ({', '.join(sorted(used))}) "
                            f"but the card has {hosts[tool]} host(s) named {tool}")
    before = sum(usage["dispatched"].values())
    this_matrix = len(tools) * len(conditions) * runs
    max_runs = card["budget"]["max_runs"]
    if before + this_matrix > max_runs:
        refusals.append(f"budget.max_runs={max_runs}: {before} run(s) already dispatched under this card "
                        f"in {out}, this matrix adds up to {this_matrix}; freeze a new card to spend more")
    if refusals:
        raise GateError("; ".join(refusals))

    beyond = []
    for tool in tools:
        for condition in conditions:
            key = cell_key(tool, mode, condition)
            planned = arm_runs[condition]
            allowed = planned + min(usage["invalid"][key], planned * reruns)
            if usage["dispatched"][key] + runs > allowed:
                beyond.append(f"{key}: {usage['dispatched'][key]} dispatched + {runs} > {allowed} allowed "
                              f"({planned} planned, {usage['invalid'][key]} invalid)")
    if beyond and not (deviation and deviation.strip()):
        raise GateError("cells beyond the card's plan; pass --deviation REASON to run them as a recorded "
                        "deviation: " + "; ".join(beyond))
    return {"max_runs": max_runs, "dispatched_before": before, "this_matrix": this_matrix,
            "beyond_plan": beyond, "validator_sha256": hashlib.sha256(VALIDATOR.read_bytes()).hexdigest()}
