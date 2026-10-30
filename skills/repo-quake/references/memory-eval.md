# Agent memory evaluation

Memory is not a single retrieval score. It is a chain of **write × retrieval ×
acceptance**. An end-to-end miss cannot indict retrieval until the other two
layers have witnesses.

## Frozen contract

Declare `design.kind=memory` and `design.memory`:

- `layers.write`: gold facts/relations that should have been persisted, including
  contradiction, synonym and supplementation cases;
- `layers.retrieval`: gold-at-1, gold-in-top-k/MRR and the injected candidate set;
- `layers.acceptance`: open, verify/trust and final-answer traces;
- `corpora`: named slices with distinct `gold_shape` values (for example atomic
  turn versus whole-session). Never average them into one opaque accuracy;
- `shadow`: byte-level proof that shadow/control and treatment inputs differ only
  by the registered intervention;
- `write_before_enable=true`: create and verify the question's gold state before
  enabling the memory mechanism;
- `recall_rerank_split=true`: presence/recall and candidate ranking are different
  mechanisms, judged separately.

The ordinary card still fixes host/model, arms, invalid rules, budget and the
primary metric. Dev/threshold fitting, judge calibration and holdout validation
must be disjoint; a judge model swap requires recalibration.

## Execution and attribution

Use three ledgers, not one score:

1. **Write ledger**: expected facts, persisted facts, false writes and relation
   labels. If the gold is absent, stop attributing downstream failure to recall.
2. **Retrieval ledger**: full-corpus recall before any small reranker/judge,
   candidate order, and the actual injected subset. A reranker cannot recover a
   gold that lexical recall never supplied.
3. **Acceptance ledger**: whether the model opened the memory, checked the gold,
   and used it. An injected memory that was never opened is a consumption failure,
   not proof that the memory content was useless.

Keep shadow prompts byte-identical apart from treatment. Pin ambient memory,
automatic recall, judges, hooks and historical stores on both arms. Do not let a
previous treatment populate the control's memory. Report each corpus separately
and record unknown/unmeasurable layers as unknown, never false.

## High-value failure cases

- A small judge rejects paraphrased but relevant memories from a narrow window.
- Gold-at-1 improves offline, but the agent does not read results in rank order.
- Whole-session scores hide an atomic-fact regression.
- A control accidentally uses the same built-in judge or default recall as the
  treatment.
