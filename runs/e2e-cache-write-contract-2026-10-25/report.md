# Cache write-throw settlement contract — 2026-10-25

## Scope

Three direct, in-memory calls to `settleStagedTraces` in npm `e2e@0.21.3`. Each cell staged one confirmed `kind=write` trace and forced the store write by returning a read miss. No browser, model, network or filesystem cache was used. C0 and C1 had to pass before T1 could run; both controls passed.

## Results

| cell | store behavior | frozen expected outcome | actual | contained |
|---|---|---|---|---|
| C0 | return `{bytes:128}` | `saved` | `saved` | yes |
| C1 | return `undefined` | `not-written` | `not-written` | yes |
| T1 | throw `EACCES` | `not-written` | `null` | yes |

The exception did not escape, but the step's outcome disappeared. `results/matrix.json` and the per-cell store ledgers are the primary evidence.

## Cross-evidence and classification

The full-browser F1 cell in `runs/e2e-semantic-commit-2026-10-25` independently reached the same seam. Its application made one request and one commit, the test passed, and the store logged read/read/write before the deliberate write throw. Its `report.json` likewise omitted `step.cache.write`.

This is a reproducible **cache write reporting contract mismatch** in `e2e@0.21.3`: `CacheWrite` documents `not-written` for a confirmed trace the store did not write, and the undefined-return control produces it, but a thrown write produces no outcome. It is not evidence of duplicate business side effects, and it does not make the cache-write failure itself unexpected—the injected fault was deliberate.

Main-source review on 2026-10-25 found the same empty catch structure at main HEAD `69e123b17e04ed624df16d32f3b1ef95ce22c083` (the latest commit returned for `context.ts` was `689620d728d04202757ffd11ed001b512b68044a`); main was not rebuilt or executed. See `upstream-main-review.md`.

The related #1363 console-tally request does not subsume this case: here the outcome is missing before any tally can consume it.

## Disposition

`cache-write-throw-issue-draft.md` is ready for human review. No issue, PR, comment or other public write has been made. A minimal fix direction is to preserve `not-written` when a confirmed `kind=write` settlement catches a read/write failure, with regression tests covering both `undefined` and thrown writes; the exact behavior for every store failure remains a maintainer decision.
