# Metamorphic evaluation

When a correct output cannot be enumerated, assert a relation instead of a golden
string: for source input `x` and transformed input `g(x)`, the outputs must satisfy
`R(f(x), f(g(x)))`. A violated relation is a counterexample; a preserved relation
is not proof of correctness.

## Frozen contract

Declare `design.kind=metamorphic` and `design.metamorphic`:

- `source_case`: the pinned input and why its path reaches the mechanism;
- `follow_ups`: unique transforms, each with its own expected `relation`;
- `outcome_relation`: the user-/system-level property that must survive;
- `na_policy`: transforms that are invalid for a protocol or capability must be
  N/A, not silently counted as passes or failures.

Keep the ordinary controls and invalid ledger. A transform must preserve the
semantic task while changing the representation under test. If both source and
follow-up are broken in the same way, a weak relation can pass; include a control
that can distinguish shared faults from genuine invariance.

## Agent/stream example: delta chunking

The semantic provider response is fixed. Change only transport segmentation:

- one event per logical token;
- line-aligned batches;
- random byte boundaries inside and outside UTF-8 code points;
- boundaries around tool-call arguments, escape sequences and terminal events.

The relation is not byte-identical timing or chunk count. Depending on the claim,
it is equivalence of final conversation text, parsed tool calls, stop reason,
integrity verdict, or rendered terminal state. Record illegal UTF-8 splits as N/A
when the wire contract forbids them rather than forcing a false result.

## Dual implementation and fault injection

Two independent implementations can serve as each other's differential witness,
but agreement is not a gold oracle: shared assumptions fail together. Conversely,
every metamorphic relation supplies a fault-injection map. Apply the transform at
protocol boundaries, then check the relation at the user-visible or persisted
boundary, not only inside the parser.

Report source/follow-up hashes, relation outcomes, invalid/N/A transforms and a
minimal counterexample pair. Do not replace the relation with aggregate similarity
after seeing inconvenient mismatches.
