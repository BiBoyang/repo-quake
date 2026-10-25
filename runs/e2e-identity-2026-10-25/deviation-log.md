# Deviation log

## Setup failures

- H1 attempt 1 failed while importing the config because the newly written `executor.mjs` had a missing closing parenthesis in `matches.map(...)`. This was a fixture syntax error, not a product failure. It is preserved as `H1-config-error.*` and `H1-executor-syntax-error.*`.
- `??` was replaced with `||` while debugging, but that change was not the root cause and is not presented as a product fix.

## Param-collision deferred

Two setup failures would otherwise push the total beyond `max_runs=8`. The param-collision arm is deferred to a separate future experiment. Final count, including setup failures: **8** (H×3 including the failed attempts, C×2, A×2, U1×1).

## Healthy baseline deferred and single-button baseline separated

The healthy H arm expected the two-button prepare/finish workflow, but the initial `page-v1.html` was the single-button `Upgrade Plan` variant. That attempt is also a fixture mismatch, not a product failure. H is deferred; C and A now use a dedicated `page-single.html` for their baseline so their treatments cannot overwrite each other's baseline.

`page-single.html` now contains the intended two-button prepare/finish workflow for C. A separate `page-ambiguous.html` is used only for the duplicate-control treatment.

## wrong-context deferred

C1 hit `LOCATOR_AMBIGUOUS` because the executor treated the legitimate prepare/finish pair as ambiguous. It is preserved as `C1-invalid-setup.*`. The executor now filters candidates by instruction before applying the ambiguity check. The wrong-context arm is deferred to avoid another scope expansion; only A and U1 remain in this card.

## A2 label mismatch

The first A2 attempt used buttons named `Upgrade Plan` while the baseline recorded `Finish Upgrade`. It therefore exercised `target-not-found`, not `target-ambiguous`. It is preserved as `A2-invalid-setup.*`. The corrected A2 uses two buttons both named `Finish Upgrade`, so the intended ambiguity is actually exercised.

## Baseline eviction and restoration

The first failed A2 treatment evicted its baseline entry, so the following attempt returned `no-entry` rather than `target-ambiguous`. The A1 trace was restored from the saved valid trace copy, with only the button label aligned to `Finish Upgrade`, avoiding an extra baseline execution. `A2-no-entry.*` is preserved as another setup miss, not product evidence.

## Baseline trace source corrected

The previous restoration used the V2 `run-3.cache-entry.json`, which contains `Upgrade Plan v2`, so it was not a valid V1 baseline. `A2-v2-baseline.*` is excluded as another setup error. The baseline is now restored from the original V1 `B1.cache-entry.json`, with only the button label changed to `Finish Upgrade`. U1 is deferred to a separate experiment to keep the total at eight executions including setup failures.

## Active page was not refreshed and the budget was exceeded

The final A2 attempt used `page-ambiguous.html` after editing the buttons to `Finish Upgrade`, but `page.html` still served the older `Upgrade Plan` variant. This is another setup mismatch and makes the attempt invalid, not evidence of a product defect.

Recounting all attempts, including setup failures, the actual total is **9**, exceeding the preregistered `max_runs=8` by one. No additional execution will be performed. U1, wrong-context and param-collision remain unexecuted. The experiment card is not edited to hide this overrun.
