# Experiment runs

This directory keeps the source fixtures, preregistered experiment cards, independent witnesses, grades and reports produced while developing repo-quake. It is evidence, not a leaderboard. Small-N smoke runs prove only that a path occurred, not a stable rate.

Directory names are evidence anchors: the ledger, the reports and the records inside other runs cite them, so a run directory is never renamed. New phases use `phase<N>-<slug>-<date>/`. The four early phase directories have no date; the table below gives it.

## Numbered phases

| directory | date | what it holds | report |
|---|---|---|---|
| `phase0/` | 2026-09-30 | cold probes of both hosts (neither knows vercel/eve) and the probe prompt | [notes](../docs/phase0-notes.md) |
| `phase1/` | 2026-10-01 | grades and matrix log of the eve agent-dir matrix; the staging tree is not kept | [report](../docs/phase1-report.md) |
| `phase1p/` | 2026-10-01 | one hash-named directory per run of the pydantic-ai greeter matrix: guard, meta, prompt, report | [report](../docs/phase1p-report.md) |
| `phase2/` | 2026-10-02 | one hash-named directory per run of the examiner-skill matrix (skill-creator and eval-guide, 72 host runs) | [report](../docs/phase2-report.md) |
| (none) | 2026-10-15 | phase 3, the metacodes spike: its runs were never archived here | [disclosure](../docs/phase3-disclosure.md) |
| `phase4-stream-retry-2026-11-15/` | 2026-11-15 | redacted public copy of the phase-4 retest (Claude Code and codex interactive, 36 runs): records, screen captures, raw-byte analyses and delivery logs; request bodies, session files and raw terminal bytes stay private (`EXPORT.md`) | [report](../docs/phase4-report.md) |
| `phase4-codex-retries-exhausted-2026-11-16/` | 2026-11-16 | exploratory, not preregistered: codex 0.169.0 interactive with every attempt cut (F1/F6-always, 3 each, F0 before and after); all six attempts stay concatenated on the final screen 6/6; the minimal repro and the comment posted to openai/codex#47538 are in `upstream-repro/` | [report](../docs/phase4-report.md) |
| `phase5-metacodes-2026-11-16/` | 2026-11-16 | redacted public copy: metacodes 0.12.1-dev (main 1707da0c), TUI and headless, under once-faults on the main answer (108 planned runs) | [report](../docs/phase5-report.md) |
| `phase5-appendix-f4f5-2026-11-16/` | 2026-11-16 | the 2026-09-25 interactive appendix re-checked with the phase-4 witness: Claude Code 2.1.282 and codex 0.169.0 on clean length stops (60 planned runs) | [report](../docs/phase5-report.md) |
| `phase5-dsh-2026-11-16/` | 2026-11-16 | deepseek-harness 0.2.2-rc.3 headless on three wire protocols (72 planned runs) | [report](../docs/phase5-report.md) |
| `phase6-metacodes-stall-2026-11-21/` | 2026-11-21 | redacted public copy: metacodes main 53b3e285 (ReleaseSmall) under stalled dependencies, 21 arms × 3, 0 invalid | [report](../docs/phase6-report.md) |

Each preregistered directory carries `card-frozen.json`, byte-equal to its card in [`cards/`](../cards/README.md).

## Side experiments (2026-10-24/25)

- `smoke-2026-10-24/` — greeting-card healthy/fault/healthy smoke for the optimized runner, including detection without containment and output drift.
- `skill-up-main-2026-10-24/` — upstream `skill-up` regression at `ad5f533`, deterministic config-boundary checks, the whitespace-validation issue draft, and the issue and PR filed as `alibaba/skill-up#337` and `#338` (ledger RQ-F-034).
- `e2e-replay-2026-10-24/` — npm `e2e@0.21.3` replay smoke: first live recording, unchanged replay, and changed-control re-execution.
- `e2e-adversarial-2026-10-24/` — failed-assertion cache behavior, strict-cache, end-state drift, and corrupted cache entries. The extra D arm exceeded the original eight-run budget and is explicitly marked exploratory in `deviation-log.md`.
- `e2e-advanced-2026-10-25/` — two-goal replay and side-effect differential, changed finish control, and end-state recovery; includes setup deviations and a deferred uncertain/no-change plan.
- `e2e-deferred-2026-10-25/` — no-change recording behavior and direct `ACTION_MAY_HAVE_COMMITTED` evidence.
- `e2e-identity-2026-10-25/` — context/ambiguity attempts with a documented sequence of fixture errors and an actual 9-run budget overrun; only A1 is valid.
- `e2e-identity-reset-2026-10-25/` — corrected small-card reset with valid `target-ambiguous` and full `StepTraceSession` uncertain-commit evidence, plus a separate U1 verification card and overrun disclosure.
- `e2e-cache-write-contract-2026-10-25/` — three direct calls to `settleStagedTraces`: a store write that throws `EACCES` settles as `null` instead of the frozen `not-written`; the upstream repro and PR status for `tester-army/e2e#1371` / `#1372` (ledger RQ-F-001).
- `e2e-semantic-commit-2026-10-25/` — semantic cache and asynchronous commit audit with a deterministic executor in place of the model; nine local executions under a frozen card.
- `e2e-uncertain-verification-2026-10-25/` — focused real-browser re-check of an uncertain commit (`ACTION_MAY_HAVE_COMMITTED`), replacing the identity run's invalid U1.

## Before this repository

- `skill-quake-2026-09-25/` — raw runs of the skill-quake experiment: cells A, B-invalid-env and C, the claude and codex truncation cells, `summary-B.md` and `summary.json`. They came in with the umbrella merge on 2026-10-15 and sat at the top level as `results/` until 2026-11-21; the write-up is in [`docs/skill-quake/`](../docs/skill-quake/).

## Artifact policy

Kept: experiment cards, source fixtures, prompt templates, independent witnesses, metadata, grades, compact logs and final reports.

Ignored by `.gitignore`: `node_modules`, Chrome profiles, `.e2e` output directories, temporary staging trees, built binaries, disposable cache directories, local HOME directories, process IDs and noisy browser logs. These remain on disk locally but are not intended for publication.
