# Experiment card

An experiment card freezes the claim, arms, witnesses, grading and stopping rules
before the first paid run. It is the pre-registration contract for a matrix, not a
report written after the results are known.

Start from `examples/experiment-card.json`, replace every example value, then run:

```bash
python3 skills/repo-quake/scripts/validate_card.py path/to/card.json
```

The validator checks structure, unique host/arm ids, control roles, prompt hash
shape, path reachability, a declared invalid policy, isolation, ethics, and whether
`budget.max_runs` can fund the planned matrix. `sampling.runs_overrides` can give an
arm (for example a repeated C0) a different run count. If the pristine original stays
reachable, `isolation.contamination` must state that exposure and its handling rather
than pretending the original is unreachable. The validator does **not** prove that the claim
is true, the prompt actually has that hash, or the witness is well designed.

## Semantics that must not drift

- `C0` is a healthy negative control. A positive control is a separate fault that
  must fire an existing detection path; not every injected fault is a control.
- Environment/setup failure is `INVALID` and leaves every metric denominator.
  A missing `grade.json` is `UNGRADED`, also outside every denominator. Neither is
  a detected or failed trial.
- `detected`, `reported`, `contained`, `recovered` and `reverified` are separate
  observations. Do not infer one from another or backfill old runs from L-levels.
- Optional metrics have their own denominator and `unknown` count. Old results
  remain old evidence; do not rewrite them with new fields.
- `invalid_rules` and `budget` are fixed before dispatch. A budget that cannot
  refuse an over-budget plan is not a budget.
- `ethics.production_contact` and `ethics.human_subjects` are explicit because
  fault injection and human studies have different consent and blast-radius needs.

## Source, template and delivered hashes

These hashes answer different questions and are not expected to match:

- `target.source_sha256` identifies the pristine target before mutation.
- `task.prompt_sha256` identifies the frozen prompt template in the card.
- Run-level `fixture_sha256` identifies the mutated fixture **before dispatch**.
- Run-level `prompt_sha256` identifies the rendered prompt, including that run's
  staging paths, **before dispatch**.

The run hashes therefore prove what was delivered; the card hashes prove what was
pre-registered. Do not compare them as if they were the same artifact.

## Optional design families

Legacy cards need no `design` field and retain their original meaning. New cards
may declare exactly one of these designs; each has a worked example under
`examples/` and a full playbook under `references/`:

- `design.kind=paired` with `design.paired`: two arms, balanced AB/BA order,
  exact McNemar, a frozen holdout and an explicit proxy-consumption chain.
- `design.kind=memory` with `design.memory`: independent write/retrieval/
  acceptance witnesses, named gold-shape corpora, shadow identity and split
  recall/reranking.
- `design.kind=metamorphic` with `design.metamorphic`: source/follow-up
  transforms, per-transform relations and an explicit N/A policy.

`cost_policy` is orthogonal to all three and to ordinary fault injection. It
freezes per-run/per-success ceilings, retry/cache accounting, billing alignment,
overrun handling and the quality–cost decision rule. It is a decision contract,
not a replacement for `budget.max_usd`.

The validator checks structural invariants only. It cannot prove that pairing
reset state, memory witnesses actually measure acceptance, a transform preserves
semantics, or billing was truly aligned. Those remain run-level evidence duties.

## Comparability

A card is comparable only when its claim, task, host/model/effort, arms, rubric and
sampling rules are explicitly aligned. A version bump is a new experiment, not a
silent continuation of the old matrix. Store the card next to the results and keep
its `schema_version`; later readers must be able to tell what changed.
