# Paired experiments

Use pairing when the question is causal: did this treatment change the outcome on
**the same task**, rather than on a luckier sample? Independent A/B groups are a
last resort when state cannot be reset or paired fixtures would contaminate one
another.

## Frozen contract

Declare `design.kind=paired` and `design.paired` in the experiment card. Freeze:

- one primary metric and two arms; every other visible byte stays aligned;
- `pairs_planned`, one stable pair id per task, and a balanced AB/BA
  `order_schedule` generated before dispatch;
- target/model/scorer pins, task-set hash and a holdout with opening conditions;
- `statistic=exact_mcnemar`, invalid/rerun rules and the total budget;
- a written `proxy_chain`: upstream metric → injected → opened → trusted → final
  behavior. Every arrow is a consumption assumption with its own witness.

The current validator requires equal runs per arm per host and exactly two arms.
Do not squeeze an unbalanced historical dataset into this contract; register a
different analysis instead.

## Execution and analysis

Reset state between arms. The treatment is everything the model sees, including
judge wording and advice, not only the feature flag. Do not silently retry one arm,
share a cache the other arm cannot use, or let the first arm's files teach the
second.

Build the 2×2 table per pair: both pass, only control passes, only treatment
passes, both fail. Only the two discordant cells carry treatment information;
concordant pairs document coverage but do not enter McNemar's statistic. Report
pair-level raw outcomes, invalid count, discordant count and an interval alongside
the p-value. A significant proxy metric authorizes an end-to-end confirmation, not
a launch. If the downstream does not open or trust the artifact, the proxy chain
has failed even when the upstream ranking improved.

## Anti-patterns

- Choosing AB/BA after seeing which order looks better.
- Counting retries as independent pairs.
- Combining old and new prompt/judge wording as one treatment.
- Reporting only the p-value or averaging incompatible task slices.
- Treating invalid as failure, or deleting pairs after their outcomes are known.
