# tester-army/e2e identity reset: ambiguity and uncertain commit — 2026-10-25

## Valid outcomes

### A2: duplicated controls

- A1 recorded `Finish Upgrade` once and passed with `Pro`.
- A2 returned `target-ambiguous`, `replayedActions=0`, and did not replay the stale button blindly. The executor selected the correct `Finish Upgrade`; the event log contains only `finish`, not `enterprise`.
- `write=saved`, so the new flow was recorded, but no additional run was used to validate it.

### U1: uncertain commit

`StepTraceSession` with an action that committed once and then threw `ACTION_MAY_HAVE_COMMITTED` returned:

- `mode=missed`;
- `reason=action-uncertain`;
- `detail=at action 1 of 1, tap button "Upgrade Plan"`;
- `calls=1`.

This confirms the handoff names the uncertain action and does not blindly repeat the commit. The first-action miss has no `replayedPrefix`; the evidence is read from `session.info`, as intended by the implementation.

## Deviations and setup failures

`deviation-log.md` records a config/executor syntax issue, an incorrect U1 assertion, and the fact that the original A1/A2/U1 card reached four attempts before the final verification, exceeding its `max_runs=3` by one. The final verification used a separate card with a fresh budget, not an edit to the old budget. No upstream issue or PR is justified from these valid outcomes.

## Evidence

- `results/A1.report.json`: healthy baseline.
- `results/A2.report.json`: `target-ambiguous` with no wrong-button side effect.
- `results/U1-verification.outcome.json`: `action-uncertain` with exactly one commit.
- `deviation-log.md`: all setup failures and the overrun disclosure.

The local app server and temporary CDP Chrome have been stopped. No new commits or pushes were made for these artifacts.
