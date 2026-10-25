# tester-army/e2e advanced cache and side-effect audit — 2026-10-25

## Scope

Test two-goal replay with an independent event server and a deterministic executor. The questions are not only whether a test passes, but whether live execution, replay and changed-state recovery have the same side effects. Target versions are npm `e2e@0.21.3` and `@e2e-dev/web@0.15.3`; no real model was called.

## Valid evidence

### Healthy differential (H1–H3)

- H1 first live run: `prepare` and `finish` were each called once and both recordings saved.
- H2 unchanged replay: both goals replayed with no new executor call.
- H3 `--no-cache`: both goals ran live again, producing the same event list.
- All three event lists are exactly `["prepare","finish"]` after independent server resets. This is side-effect equivalence, not merely a green test.

### Changed finish control (corrected V2)

- `prepare` self-finalized from its recording and was not repeated.
- `finish` returned `missed / target-not-found` and ran live with the new label.
- The final event list remained `["prepare","finish"]`, with no duplicated `prepare`.

### End-state drift (corrected V3)

- `prepare` replayed successfully.
- `finish` replayed, then returned `agent-concluded / end-mismatch` because the recorded `Pro` state was absent; `write=evicted`.
- The executor observed `Enterprise` and used `Fix to Pro`, producing `["prepare","finish","repair"]` and passing the final assertion.

These outcomes are consistent with the documented adaptive replay behavior and confirm no upstream defect in the tested paths.

## Invalid setup attempts (not product evidence)

- The first V2 attempt used a new empty cache directory, producing `no-entry` instead of a changed-control replay. It was replaced by a corrected run using the healthy cache.
- The first V3 attempt reused a cache that V2 had overwritten with `Finish Upgrade v2`, so it no longer represented the V1 baseline. It was replaced by a fresh V1 baseline and a corrected end-state run.

Both are preserved as `V2-invalid-setup.*` and `V3-invalid-setup.*` and are excluded from the conclusion.

## Budget and deferred work

The card allowed eight executions. Including both invalid setup attempts, the final count is exactly eight: H×3, invalid-V2×1, corrected-V2×1, invalid-V3×1, V3-baseline×1, corrected-V3×1. U1 (`ACTION_MAY_HAVE_COMMITTED`) and N (no-change) were deferred to a separate future experiment and are not claimed here. See `deviation-log.md`.

## Limitations

- The custom executor is deterministic code, not an LLM, so this is a harness/cache audit, not a model-robustness result.
- The two-button static workflow does not cover every asynchronous UI shape, real provider, mobile engine or distributed cache store.
- The experiments used npm releases, not `main`.
- No upstream issue or PR is warranted from these valid outcomes.

## Evidence

`experiment-card.json`, `tests-manifest.json`, executor logs, server event logs, variant hashes, cache evidence and full `report.json` files are retained in this directory. The local app server and temporary CDP Chrome have been stopped.
