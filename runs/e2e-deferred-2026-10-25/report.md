# tester-army/e2e deferred uncertain and no-change checks — 2026-10-25

## Scope

Complete the two deferred checks from the advanced cache audit, within a separate four-execution card. Target is npm `e2e@0.21.3` with `@e2e-dev/web@0.15.3`; no real model was called.

## Results

### Healthy baseline (H)

The two-goal workflow passed with `prepare` and `finish` each called once and both cache entries saved. This confirms the fixture and executor were healthy before the deferred treatments.

### No-change act (N1 and N2)

Both no-op runs returned:

- `mode=missed`, `reason=no-entry`;
- `write=no-change`;
- zero cache entries on disk;
- one new executor invocation per run, two in total.

A no-change act therefore does not create a recording, and the next identical run still executes live rather than replaying a nonexistent entry.

### Uncertain commit (U1)

`replayTrace` was invoked directly with an action that had already committed but threw `ACTION_MAY_HAVE_COMMITTED`. The outcome was:

- `completed: false`;
- `stopReason: "action-uncertain"`;
- `uncertainAction: "tap button \"Upgrade Plan\""`;
- exactly one committed action (`calls: 1`).

The action was not repeated blindly, and the response identifies the exact action whose commit state is uncertain. This is consistent with the documented hand-off contract: the next executor must verify current state before acting again.

## Limits

- U1 is a direct `replayTrace` test, not a full `StepTraceSession`, provider or real-model test.
- N covers one no-op action only; it does not establish every no-change form.
- No upstream defect was confirmed, so no issue or PR is warranted from these outcomes.
- The local app server and temporary CDP Chrome have been stopped.

## Evidence

`experiment-card.json`, `tests-manifest.json`, executor logs, cache reports and `results/U1.outcome.json` are retained in this directory. All four executions exited successfully.
