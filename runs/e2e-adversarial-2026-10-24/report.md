# tester-army/e2e adversarial cache audit — 2026-10-24

## Scope

Use deterministic local executors and a static app to test replay/cache behavior under failed assertions, strict mode, end-state drift and corrupted cache entries. Target versions are npm `e2e@0.21.3` and `@e2e-dev/web@0.15.3`, not `main`. No real model calls were made.

## Confirmatory arms within the original budget (8 runs)

| arm | setup and treatment | observed result | interpretation |
|---|---|---|---|
| H | Healthy record, then unchanged replay | First run saved; second run `self-finalized`, one replayed action, no new executor call | Healthy control behaved as expected |
| A | Later assertion intentionally failed, then corrected | Failed run left **zero cache entries**; corrected run invoked the executor again and saved a new entry | Unconfirmed actions did not poison the cache |
| B | Changed control under `--strict-cache` | `REPLAY_STALE`; no new executor call; cache-entry SHA-256 unchanged | Strict mode rejected stale replay without hidden live execution or rewrites |
| C | Same action changed the final state from Pro to Enterprise | `agent-concluded / end-mismatch`; replayed action did not self-finalize as success; `write=evicted`; executor used `Fix to Pro` and the final assertion passed | End-state drift was detected and recovered rather than silently accepted |

C is particularly useful because the old action still ran. The final assertion did not rely on the stale outcome: the cache explicitly reported that the recorded end state was missing, then handed control to the executor.

## Exploratory arm outside the original budget (2 additional runs)

D replaced a valid cache entry with `{"not":"a-trace"}`. The next run returned `missed / invalid-entry`, invoked the executor again and passed. This is consistent with graceful degradation, but **D was added after the eight budgeted runs and is exploratory only**. See `deviation-log.md`; the experiment card was not edited to legitimize the extra runs.

## Exit codes and evidence

- A1 returned 1 as the intentionally failed assertion; A2 returned 0.
- B2 returned 2 with `REPLAY_STALE`; B1 returned 0.
- H and C runs returned 0.
- Executor invocation logs, cache-entry hashes, active variant files, `report.json` copies and the frozen experiment card are preserved in this directory.
- The local app server and CDP Chrome have been stopped.

## Defect assessment

No upstream defect was confirmed in these cache paths. No issue or PR is warranted from this audit. These results do not prove that other replay paths—multi-action side effects, model/config changes, mobile engines or distributed cache stores—are safe.

## Process deviation

The original `max_runs=8` was exceeded by two exploratory runs. This is recorded as a methodology mistake, not hidden as part of the planned matrix. Future additional arms require a new frozen card before dispatch.
