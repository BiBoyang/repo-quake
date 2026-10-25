# tester-army/e2e semantic cache and asynchronous commit audit — 2026-10-25

## Scope and budget

Pinned targets were npm `e2e@0.21.3`, `@e2e-dev/web@0.15.3`, and local Chrome 156.0.8078.47. A deterministic executor replaced the model. The frozen card allowed nine local executions; all nine appear once in `execution-ledger.jsonl`, with no retries. C0 gated the matrix and every treatment materialized its own copy of the healthy seed.

## Valid outcomes

| cell | primary evidence | adjudication |
|---|---|---|
| C0 | One live executor call; `missed/no-entry`; `write=saved`; one entry | Healthy recording control passed |
| C1 | Zero executor calls; `self-finalized`; two replayed actions; `write=kept` | Cached replay substituted Beta correctly |
| C2 | One live call; no agent cache detail | No-cache semantic reference passed |
| W1 | `missed/wrong-context`, detail `/` versus `/other`; one live call | Detected, reported, recovered and final-DOM reverified |
| P1 | `notRecorded=param-collision`; zero cache entries | Collision reported; no unsafe recording persisted |
| R1 | CI=true; full replay; zero calls; byte-identical cache before/after | Defaulted CI cache remained read-only |
| F1 | Store read/read/write; write threw EACCES; test passed; one commit | Business effect contained, but cache write outcome absent; see below |
| N1 | Full replay; zero calls; `write=kept`; one commit | Healthy post-series negative control passed |

C0, C1 and C2 have exactly the same normalized server sequence:

1. `input {item}`
2. `save-request {item}`
3. `save-committed {item}`

Their normalized final DOM also matches: current input value, one current list item, and `Saved {item}`. This is a direct action/DOM/side-effect differential, not merely three green tests. See `results/semantic-differential.json`.

## New reproducible report-contract mismatch: F1

The custom store proves that settlement reached `write` after the application workflow and that `write` threw `EACCES`. The application committed exactly once, the test passed, and the exception was contained. However, `step.cache.write` was absent and the console printed only `Cache 1 missed`.

A separate three-call direct contract experiment at `runs/e2e-cache-write-contract-2026-10-25` reproduced the distinction:

- healthy write → `saved`;
- write returns `undefined` → `not-written`;
- write throws → `null`, although the public `CacheWrite` contract defines `not-written` for a confirmed trace the store did not write.

This is a reproducible cache-persistence **reporting** mismatch in `e2e@0.21.3`, not a duplicate-side-effect finding. Detection/containment and user-facing reporting must remain separate: the error was caught and business output was correct, but the cache outcome was not reported. Recovery of the cache write was not tested. An upstream issue draft exists but has not been posted.

## Invalid U1: not a product finding

The original U1 fixture omitted the required `EngineError` options argument. The intended uncertain-commit error became a `TypeError`, so replay handed off `action-failed`; the executor then repeated the save. Those duplicate requests are fixture-induced and are explicitly excluded from product conclusions. See `results/U1.classification.json` and `deviation-log.md`.

A separately preregistered corrected experiment confirmed the real uncertain-commit path: `agent-concluded/action-uncertain`, the exact tap named, and one request/commit. See `runs/e2e-uncertain-verification-2026-10-25/report.md`.

## Limits and stop decision

One execution per cell proves presence and behavior for these fixtures, not rates or broad coverage. The executor is deterministic; there was no real model, provider, mobile engine, remote cache or distributed backend. The asynchronous form is one local UI shape.

The matrix produced one new reproducible reporting mismatch and valid evidence for the other prioritized seams. The stop condition was therefore met: no further same-class cells were added. No public issue or PR was created.

Primary evidence: `experiment-card.json`, `task-contract.txt`, `execution-ledger.jsonl`, `results/matrix.json`, `results/semantic-differential.json`, per-cell reports, event ledgers, DOM snapshots, cache manifests and fault/store logs.
