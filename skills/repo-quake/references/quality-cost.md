# Quality–cost evaluation

Quality without a cost axis invites buying pass rate through stronger models,
retries, more context and extra self-checks. Cost is also an attribution variable:
if the arms do not share retry/cache/billing conditions, neither the effect nor the
bill is cleanly attributable.

## Frozen contract

Add `cost_policy` to any card (it composes with fault, paired, memory and
metamorphic designs):

- `max_per_run` and `max_per_success`: finite non-negative limits in the card's
  declared accounting currency;
- `retry_policy`: preferably zero silent retries for comparison experiments;
  otherwise every authorized attempt gets its own receipt;
- `cache_policy`: cache read/create/input/output accounting and the conditions
  that invalidate cache;
- `billing_alignment`: byte-level alignment of model, prompt, retry and cache
  paths apart from treatment;
- `overrun`: `invalid`, `counted`, or `stop_and_report`, chosen before dispatch;
- `decision_rule`: the quality–cost rule that can reject an arm even at equal
  quality, including any registered cost margin.

The card's `budget.max_usd` caps the series; `cost_policy` governs per-sample and
adoption decisions. They are not interchangeable. For zero-price mock runs, use
zero limits and omit `budget.max_usd` rather than inventing provider prices.

## Metrics and stopping

Report cost per successful outcome (success denominator), marginal cost for the
next quality gain, and the quality–cost Pareto frontier. An arm inside the frontier
loses to an arm with equal quality at lower cost. Token totals alone are not cost:
include cache reads/creation at their actual rates and all retry attempts.

Stop at the pre-registered series or sample budget. Do not append funds because a
trend is promising, and do not relabel an overrun after seeing the result. An
intervention that changes tool schemas, prompts or ordering may also invalidate a
large cached prefix; that miss belongs to its treatment cost.

## Anti-patterns

- Comparing pass@k for one arm with single-attempt reliability for another.
- Letting a control silently reuse treatment-paid retries, judges or cache.
- Declaring a winner from quality alone when both arms lie on the same quality
  plateau but have different costs per success.
