#!/usr/bin/env python3
"""Validate a repo-quake experiment card using only the Python standard library."""
import json
import math
import re
import sys

REQUIRED = (
    "schema_version", "id", "claim", "target", "task", "hosts", "arms", "controls",
    "witness", "grading", "sampling", "invalid_rules", "budget", "isolation", "ethics",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def require_fields(obj, fields, where, errors):
    if not isinstance(obj, dict):
        errors.append(f"{where} must be an object")
        return False
    for field in fields:
        if field not in obj:
            errors.append(f"{where}.{field} is required")
    return True


def validate(card):
    errors = []
    if not require_fields(card, REQUIRED, "card", errors):
        return errors, 0
    if card.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not text(card.get("id")):
        errors.append("id must be non-empty text")
    if not text(card.get("claim")):
        errors.append("claim must be non-empty text")

    if require_fields(card.get("target"), {"name", "version"}, "target", errors):
        for field in ("name", "version"):
            if not text(card["target"].get(field)):
                errors.append(f"target.{field} must be non-empty text")
        if "source_sha256" in card["target"] and not HEX64.match(str(card["target"]["source_sha256"])):
            errors.append("target.source_sha256 must be 64 lowercase hex characters")
    if require_fields(card.get("task"), {"prompt_sha256", "path_reachability"}, "task", errors):
        if not HEX64.match(str(card["task"].get("prompt_sha256"))):
            errors.append("task.prompt_sha256 must be 64 lowercase hex characters")
        if not text(card["task"].get("path_reachability")):
            errors.append("task.path_reachability must explain how the task reaches the fault")

    hosts = card.get("hosts")
    host_ids = []
    if not isinstance(hosts, list) or not hosts:
        errors.append("hosts must be a non-empty array")
        hosts = []
    for index, host in enumerate(hosts):
        where = f"hosts[{index}]"
        if require_fields(host, {"id", "name", "version", "model", "effort"}, where, errors):
            if text(host.get("id")):
                host_ids.append(host["id"])
            for field in ("id", "name", "version", "model", "effort"):
                if not text(host.get(field)):
                    errors.append(f"{where}.{field} must be non-empty text")
    if len(set(host_ids)) != len(host_ids):
        errors.append("host ids must be unique")

    arms = card.get("arms")
    arm_ids = []
    roles = []
    arm_roles = {}
    if not isinstance(arms, list) or not arms:
        errors.append("arms must be a non-empty array")
        arms = []
    for index, arm in enumerate(arms):
        where = f"arms[{index}]"
        if require_fields(arm, {"id", "fault", "role"}, where, errors):
            if text(arm.get("id")):
                arm_ids.append(arm["id"])
                arm_roles[arm["id"]] = arm.get("role")
            roles.append(arm.get("role"))
            if not text(arm.get("id")) or not text(arm.get("fault")):
                errors.append(f"{where}.id and fault must be non-empty text")
            if arm.get("role") not in {"treatment", "negative_control", "positive_control"}:
                errors.append(f"{where}.role has an unknown value")
    if len(set(arm_ids)) != len(arm_ids):
        errors.append("arm ids must be unique")
    if "treatment" not in roles:
        errors.append("at least one treatment arm is required")
    if "negative_control" not in roles:
        errors.append("at least one negative-control arm is required")

    if require_fields(card.get("controls"), {"negative"}, "controls", errors):
        for field, role in (("negative", "negative_control"), ("positive", "positive_control")):
            ref = card["controls"].get(field)
            if ref is None:
                continue
            if ref not in arm_ids:
                errors.append(f"controls.{field} references unknown arm '{ref}'")
            elif arm_roles.get(ref) != role:
                errors.append(f"controls.{field} references an arm whose role is not {role}")

    if require_fields(card.get("witness"), {"delivery", "checker", "blind_spots"}, "witness", errors):
        for field in ("delivery", "checker"):
            if not text(card["witness"].get(field)):
                errors.append(f"witness.{field} must be non-empty text")
        blind = card["witness"].get("blind_spots")
        if not isinstance(blind, list) or not blind or not all(text(item) for item in blind):
            errors.append("witness.blind_spots must be a non-empty array (use 'none known after calibration' if appropriate)")

    if require_fields(card.get("grading"), {"rubric", "primary_metric"}, "grading", errors):
        for field in ("rubric", "primary_metric"):
            if not text(card["grading"].get(field)):
                errors.append(f"grading.{field} must be non-empty text")

    runs_per_cell = None
    if require_fields(card.get("sampling"), {"runs_per_cell"}, "sampling", errors):
        runs_per_cell = card["sampling"].get("runs_per_cell")
        if not isinstance(runs_per_cell, int) or isinstance(runs_per_cell, bool) or runs_per_cell < 1:
            errors.append("sampling.runs_per_cell must be a positive integer")
            runs_per_cell = None
    overrides = card["sampling"].get("runs_overrides", {})
    if not isinstance(overrides, dict):
        errors.append("sampling.runs_overrides must be an object when present")
        overrides = {}
    run_counts = []
    for arm_id in arm_ids:
        count = overrides.get(arm_id, runs_per_cell or 0)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            errors.append(f"sampling.runs_overrides.{arm_id} must be a positive integer")
            count = 0
        run_counts.append(count)
    for arm_id in overrides:
        if arm_id not in arm_ids:
            errors.append(f"sampling.runs_overrides references unknown arm '{arm_id}'")
    planned = len(hosts) * sum(run_counts)

    rules = card.get("invalid_rules")
    if not isinstance(rules, list) or not rules or not all(text(rule) for rule in rules):
        errors.append("invalid_rules must be a non-empty array")
    if require_fields(card.get("budget"), {"max_runs"}, "budget", errors):
        max_runs = card["budget"].get("max_runs")
        if not isinstance(max_runs, int) or isinstance(max_runs, bool) or max_runs < 1:
            errors.append("budget.max_runs must be a positive integer")
        elif runs_per_cell is not None and max_runs < planned:
            errors.append(f"budget.max_runs={max_runs} cannot fund planned_runs={planned}")
        if "max_usd" in card["budget"] and (
            not isinstance(card["budget"]["max_usd"], (int, float))
            or isinstance(card["budget"]["max_usd"], bool)
            or not math.isfinite(card["budget"]["max_usd"])
            or card["budget"]["max_usd"] <= 0
        ):
            errors.append("budget.max_usd must be a positive number when present")

    if require_fields(card.get("isolation"), {"mode", "pristine_original_unreachable"}, "isolation", errors):
        if not text(card["isolation"].get("mode")):
            errors.append("isolation.mode must be non-empty text")
        pristine = card["isolation"].get("pristine_original_unreachable")
        if not isinstance(pristine, bool):
            errors.append("isolation.pristine_original_unreachable must be boolean")
        elif not pristine and not text(card["isolation"].get("contamination")):
            errors.append("isolation.contamination is required when the pristine original remains reachable")
    if require_fields(card.get("ethics"), {"production_contact", "human_subjects", "blast_radius"}, "ethics", errors):
        ethics = card["ethics"]
        for field in ("production_contact", "human_subjects"):
            if not isinstance(ethics.get(field), bool):
                errors.append(f"ethics.{field} must be boolean")
        if not text(ethics.get("blast_radius")):
            errors.append("ethics.blast_radius must describe the containment boundary")
        if ethics.get("human_subjects") and not text(ethics.get("consent")):
            errors.append("ethics.consent is required when human_subjects is true")
    return errors, planned


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("usage: validate_card.py <experiment-card.json>", file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as handle:
            card = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"validate_card: cannot read card: {exc}", file=sys.stderr)
        return 2
    errors, planned = validate(card)
    if errors:
        print("INVALID experiment card", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"VALID {card['id']}: planned_runs={planned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
