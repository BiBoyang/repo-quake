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
- `phase4-stream-retry-2026-11-15/` — redacted public copy of the phase-4 retest (Claude Code and codex interactive, 36 runs): records, screen captures, raw-byte analyses and delivery logs; request bodies, session files and raw terminal bytes stay private (`EXPORT.md`).
- `phase4-codex-retries-exhausted-2026-11-16/` — exploratory, not preregistered: codex 0.169.0 interactive with every attempt cut (F1/F6-always, 3 each, F0 before and after). All six attempts stay concatenated on the final screen 6/6. Includes the minimal repro and the comment posted to openai/codex#47538 (`upstream-repro/`).

## Artifact policy

Kept: experiment cards, source fixtures, prompt templates, independent witnesses, metadata, grades, compact logs and final reports.

Ignored by `.gitignore`: `node_modules`, Chrome profiles, `.e2e` output directories, temporary staging trees, built binaries, disposable cache directories, local HOME directories, process IDs and noisy browser logs. These remain on disk locally but are not intended for publication.
