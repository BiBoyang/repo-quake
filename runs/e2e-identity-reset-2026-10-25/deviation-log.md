# Deviation log

- U1 initially failed with a fixture syntax error in `JSON.parse` and is preserved as `U1-syntax-error.*`. It is not a product failure.
- U1 was moved to a separate single-execution card rather than increasing the original card's `max_runs=3`. The original card remains unchanged; U1 has its own `max_runs=1` budget.
- The standalone U1 card includes the already completed A1 baseline as its negative-control evidence, so no baseline run is repeated. Planned count is 2 including that existing baseline; only U1 is newly executed.
- U1's first assertion read `replayedPrefix.stopReason`, but for a first-action miss `replayedPrefix` is undefined by design. `A2-assertion-error.*` is preserved as a test bug, not a product defect. A separate verification card now checks `session.info.reason` and `session.info.detail` instead, with no further attempts after this one.

## Final execution count and separate verification card

The original A1/A2/U1 card had four attempts before the final verification (A1, A2, U1 syntax error, U1 assertion error), exceeding its `max_runs=3` by one. The final U1 evidence was produced only after creating the separate `experiment-card-u1-verification.json`, whose budget is 2 including the already completed baseline. That separate card used exactly one new execution. No further runs were started.
