# tester-army/e2e replay-cache pilot — 2026-10-24

## Scope

Test the execution–cache–observation path with a deterministic local executor rather than a real model. The target is the **npm release** `e2e@0.21.3` with `@e2e-dev/web@0.15.3`, not the previously inspected `main` branch. No mobile, hosted browser, GitHub reporter, telemetry or real model calls were used.

The three browser runs were:

1. V1 first live execution, which should create a recording.
2. Unchanged V1, which should replay without another executor invocation.
3. V2 with only the button name changed, which should invalidate the recorded action and invoke the executor again.

## Results

| run | independent executor calls | cache evidence | test result |
|---|---:|---|---|
| V1 first | 1 total | `missed / no-entry`; `write=saved` | Passed; action recorded |
| V1 unchanged | 1 total | `self-finalized`; `replayedActions=1`; `write=kept` | Passed with no new executor call |
| V2 changed button | 2 total | `missed / target-not-found`; `replayedActions=0`; `write=saved` | Passed after a new live execution |

The third run used `Upgrade Plan v2`, and the executor's independent log confirms it was invoked again. No stale `Upgrade Plan` action was executed. The `modelCalls` field is zero throughout because this is a hand-rolled deterministic executor, not an LLM; the meaningful live-execution witness here is the independent `executor-calls.jsonl` counter.

## Terminology deviation from the preregistered card

The card used the general word “handoff”. Actual cache behavior was `missed / target-not-found`, because the mismatch occurred at action 1 of 1. `replayedPrefix` is therefore `null`: the executor ran from the top, rather than continuing a replayed prefix with `agent-concluded`. This is the correct behavior for the observed divergence and was not rewritten after the fact.

V2 also wrote `saved`, meaning the new action was recorded. A fourth run was not performed, so V2 replay is not claimed.

## Evidence

- `experiment-card.json`: frozen before the first run and unchanged afterward.
- `results/executor-calls.jsonl`: two independent live-executor records with distinct attempt IDs and different button names.
- `results/cache-observations.json`: cache fields for all three runs. Run 1 and run 2 fields were transcribed from immediate report inspection; run 3 additionally has `run-3.report.json` and `run-3.cache-entry.json` preserved.
- `run-*.variant.sha256`: run 1 and run 2 hashes match; run 3 differs, matching the V2 button change.
- Fixture source hash is unchanged after all runs, and every run exit code is zero.
- The local app server and temporary CDP Chrome have been stopped.

## Environment and limitations

- GitHub source downloads repeatedly failed, so the experiment used the pinned npm packages instead of a source checkout. This is an explicit target-version distinction, not a claim about `main`.
- The matching Playwright browser download also failed. A temporary local Google Chrome session over CDP was used instead; semantic observation and action execution succeeded.
- The custom executor is deterministic project code. This pilot tests the replay/cache harness, not model intelligence or natural-language robustness.
- Only one divergence class was covered: a renamed control. It does not establish behavior for model changes, multi-action partial replay, corrupted cache entries, mobile targets or strict-cache CI.
- The third run took about 14.9 seconds, longer than the first two. This report records the observation without attributing a performance bug.
- No upstream defect was confirmed, so no issue or PR is warranted from this pilot.

## Decision

The replay seam behaved as documented for this controlled case: unchanged input reused the recording, while a changed control prevented stale execution and triggered a fresh live step. A next experiment should choose a different cache seam—such as multi-action partial replay or explicit strict-cache behavior—rather than repeat this same smoke.
