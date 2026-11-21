#!/usr/bin/env python3
"""Aggregate fault-injection runs without hiding invalid or ungraded trials.

Layout: <results>/<cell>/<run>/{meta.json,grade.json}

Legacy grades (level/detected/drift/notes) remain valid. New runs may also carry
reported/contained/recovered/reverified booleans. Optional metrics are reported
with their own denominator and an unknown count; missing fields are never
backfilled from L-levels.
"""
import json
import math
import os
import sys

OPTIONAL_METRICS = ("reported", "contained", "recovered", "reverified")
# One-sided 95% Wilson bounds: the gate in skills/repo-quake/references/measurement.md.
Z = 1.645


def wilson(k, n, z=Z):
    """Wilson score bounds for k/n; with z=1.645 each side is a one-sided 95% bound."""
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def is_invalid(grade):
    if grade is None:
        return False
    return grade.get("valid") is False or grade.get("level") == "INVALID"


def metric_count(runs, name):
    present = [grade.get(name) for _, _, grade in runs if isinstance(grade.get(name), bool)]
    return {
        "x": sum(value is True for value in present),
        "n": len(present),
        "unknown": sum(grade.get(name) is None for _, _, grade in runs),
    }


def summarize_cell(runs):
    valid = [(run, meta, grade) for run, meta, grade in runs if grade is not None and not is_invalid(grade)]
    invalid = sum(is_invalid(grade) for _, _, grade in runs)
    ungraded = sum(grade is None for _, _, grade in runs)
    detected = metric_count(valid, "detected")
    metrics = {"detected": detected}
    for name in OPTIONAL_METRICS:
        if any(grade.get(name) is not None for _, _, grade in valid):
            metrics[name] = metric_count(valid, name)
    return {
        "runs": len(runs),
        "graded": len(valid),
        "excluded": invalid,
        "ungraded": ungraded,
        "detected": detected["x"],
        "detected_bounds": [round(b, 4) for b in wilson(detected["x"], detected["n"])] if detected["n"] else None,
        "levels": ",".join("?" if grade is None else str(grade.get("level", "?")) for _, _, grade in runs) or "-",
        "metrics": metrics,
    }


def load_cells(results_dir):
    cells = {}
    for cell in sorted(os.listdir(results_dir)):
        cell_path = os.path.join(results_dir, cell)
        if not os.path.isdir(cell_path):
            continue
        for run in sorted(os.listdir(cell_path)):
            run_path = os.path.join(cell_path, run)
            meta_path = os.path.join(run_path, "meta.json")
            if not os.path.isfile(meta_path):
                continue
            grade_path = os.path.join(run_path, "grade.json")
            grade = read_json(grade_path) if os.path.isfile(grade_path) else None
            cells.setdefault(cell, []).append((run, read_json(meta_path), grade))
    return cells


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("usage: collect.py <results-dir>", file=sys.stderr)
        return 2
    results_dir = argv[1]
    cells = load_cells(results_dir)
    summary = {cell: summarize_cell(runs) for cell, runs in cells.items()}

    print("| cell | runs | graded | excluded | ungraded | detected | detected one-sided 95% (Wilson) | levels |")
    print("|---|---|---|---|---|---|---|---|")
    for cell, row in summary.items():
        bounds = row["detected_bounds"]
        bounds_text = f"{bounds[0]:.2f}–{bounds[1]:.2f}" if bounds else "-"
        print(
            f"| {cell} | {row['runs']} | {row['graded']} | {row['excluded']} "
            f"| {row['ungraded']} | {row['detected']}/{row['graded'] or '-'} | {bounds_text} | {row['levels']} |"
        )
    print("\nGate a claim on the lower bound, not on x/n (skills/repo-quake/references/measurement.md).")
    output = os.path.join(results_dir, "summary.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    excluded = sum(row["excluded"] for row in summary.values())
    ungraded = sum(row["ungraded"] for row in summary.values())
    if excluded:
        print(f"\n{excluded} invalid run(s) excluded from all metric denominators.", file=sys.stderr)
    if ungraded:
        print(f"\n{ungraded} run(s) missing grade.json — excluded from all metric denominators.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
