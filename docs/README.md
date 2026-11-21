# Docs

Most documents here are in Chinese. The phase table in the top-level
[README](../README.md) gives a one-line headline for each phase.

## Phases

| phase | notes | report | disclosure |
|---|---|---|---|
| 0 | [phase0-notes.md](phase0-notes.md) | — | — |
| 1 | — | [phase1-report.md](phase1-report.md) | — |
| 1′ | — | [phase1p-report.md](phase1p-report.md) | — |
| 2 | [phase2-notes.md](phase2-notes.md) | [phase2-report.md](phase2-report.md) | — |
| 3 | — | (a spike; no separate report) | [phase3-disclosure.md](phase3-disclosure.md) |
| 4 | — | [phase4-report.md](phase4-report.md) | [phase4-disclosure.md](phase4-disclosure.md) |
| 5 | — | [phase5-report.md](phase5-report.md) | [phase5-disclosure.md](phase5-disclosure.md) |
| 6 | — | [phase6-report.md](phase6-report.md) | [phase6-disclosure.md](phase6-disclosure.md) |

Notes are working records written during a phase; a report gives the results.
A disclosure follows `skills/repo-quake/references/disclosure-template.md`:
access and contact, hash manifest, preregistration and deviations, integrity
statements, and the posting-gate record. Disclosures started with phase 3.

## Method

- [detection-model.md](detection-model.md): the three-factor detection model, the
  known evaluation failures re-read through it, and the witness principle
  applied to the evaluation stack.
- [eval-evidence-guide.md](eval-evidence-guide.md): failure attribution, the three
  ledgers, independent outcomes and publication read-back, with examples.

## Other directories

- [pr-drafts/](pr-drafts/): the phase-2 upstream PRs (anthropics/skills #1949,
  microsoft/eval-guide #16): the drafts and diffs, an independent verification
  report, and the prompts that handed them to an external agent.
- [process/](process/README.md): contracts, dispatch prompts, executor logs and
  reviews of the 2026-10-30 tasks, plus the phase-4 execution prompt template.
- [skill-quake/](skill-quake/): labeled snapshots of the skill-quake bundle's
  docs (alignment, replication runbook, the 2026-09-27 article, upstream issue
  drafts). Their paths are those of the skill-quake repository at the time; the
  raw runs they cite as `results/` are in
  [`runs/skill-quake-2026-09-25/`](../runs/skill-quake-2026-09-25/).
