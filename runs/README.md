# Experiment runs

This directory keeps the source fixtures, preregistered experiment cards, independent witnesses, grades and reports produced while developing repo-quake. It is evidence, not a leaderboard. Small-N smoke runs prove only that a path occurred, not a stable rate.

## Index

- `smoke-2026-10-24/` — greeting-card healthy/fault/healthy smoke for the optimized runner, including detection without containment and output drift.
- `skill-up-main-2026-10-24/` — upstream `skill-up` regression at `ad5f533`, deterministic config-boundary checks, the whitespace-validation issue draft, and the PR used for `alibaba/skill-up#337` / `#338`.
- `e2e-replay-2026-10-24/` — npm `e2e@0.21.3` replay smoke: first live recording, unchanged replay, and changed-control re-execution.
- `e2e-adversarial-2026-10-24/` — failed-assertion cache behavior, strict-cache, end-state drift, and corrupted cache entries. The extra D arm exceeded the original eight-run budget and is explicitly marked exploratory in `deviation-log.md`.

- `e2e-advanced-2026-10-25/` — two-goal replay and side-effect differential, changed finish control, and end-state recovery; includes setup deviations and a deferred uncertain/no-change plan.
- `e2e-deferred-2026-10-25/` — no-change recording behavior and direct `ACTION_MAY_HAVE_COMMITTED` evidence.
- `e2e-identity-2026-10-25/` — context/ambiguity attempts with a documented sequence of fixture errors and an actual 9-run budget overrun; only A1 is valid.
- `e2e-identity-reset-2026-10-25/` — corrected small-card reset with valid `target-ambiguous` and full `StepTraceSession` uncertain-commit evidence, plus a separate U1 verification card and overrun disclosure.

## Artifact policy

Kept: experiment cards, source fixtures, prompt templates, independent witnesses, metadata, grades, compact logs and final reports.

Ignored by `.gitignore`: `node_modules`, Chrome profiles, `.e2e` output directories, temporary staging trees, built binaries, disposable cache directories, local HOME directories, process IDs and noisy browser logs. These remain on disk locally but are not intended for publication.
