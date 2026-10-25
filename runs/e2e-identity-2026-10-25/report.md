# tester-army/e2e identity and ambiguity audit — 2026-10-25

## Outcome

No valid A2 result was obtained, and no upstream defect was confirmed. The experiment stopped after the actual run count reached **9**, exceeding the original `max_runs=8` by one. No further execution was performed.

## Valid evidence

Only the A1 healthy baseline passed with `finish` and `Pro`, producing one event and no ambiguity. All later attempts were invalid setup, not product evidence:

- config/executor syntax errors;
- healthy baseline fixture mismatch;
- wrong-context baseline executor ambiguity;
- A2 button-label mismatch;
- baseline entry eviction;
- restoration from a V2 trace instead of a V1 trace;
- active `page.html` not refreshed after changing the button name.

The active variant at the final attempt still served `Upgrade Plan` while the baseline recorded `Finish Upgrade`. Therefore the final `target-not-found` cannot be interpreted as `target-ambiguous` or as a replay defect.

## Budget and deferred work

The frozen card allowed 8 executions. Corrections and baseline restorations accumulated to 9. This is explicitly recorded as a budget/pre-registration deviation. U1 (`StepTraceSession` with `ACTION_MAY_HAVE_COMMITTED`), wrong-context and param-collision were not executed and are not claimed in this report. No new card was opened to bypass the overrun.

## Evidence and disclosure

`deviation-log.md` contains the complete correction history and the overrun disclosure. Invalid attempts are preserved separately with suffixes such as `*-invalid-setup.*`, `A2-no-entry.*`, and `A2-v2-baseline.*`. The local app server and temporary CDP Chrome have been stopped.

## Recommended reset

A future experiment should start from a new frozen card with a smaller matrix, rather than continue this correction chain. The baseline should be rebuilt from a known-good single-button page, its entry hash verified before the treatment, and the active page variant re-read from disk immediately before dispatch.
