# Failure attribution: product, fixture, or grader

An unexpected result is not yet a finding. Before counting or publishing it,
assign it to exactly one of three ledgers: the product under test, the fixture
that delivered the experiment, or the grader that interpreted the evidence.
Each ledger has a different correction path.

| ledger | recognition | correction |
|---|---|---|
| product | The intended fault reached the intended seam, and the product's behavior violates its contract | Reproduce, minimize, and report the product behavior |
| fixture / setup | The browser, dependency, route, seed, or fault constructor was wrong, so the intended experiment did not occur | Mark `invalid setup`; fix the fixture and use a new frozen card when another run is justified |
| grader / adjudicator | The checker adds a rule the frozen contract did not contain, or misreads primary artifacts | Preserve the initial output and write a separate adjudication; do not manufacture a product run to settle a grader bug |

A side effect alone does not choose the product ledger. A malformed injected
error can make the harness respond in a way that produces duplicate requests;
those requests are evidence about the malformed fixture, not about the intended
product fault.

## Prove the fault's identity, not only its effect

Delivery proof has two halves:

1. **The intended semantics**: channel, fault type/code, payload, required
   parameters, injection point, timing, and occurrence count.
2. **The observable effect**: bytes, actions, state transitions, and side
   effects that followed from those semantics.

For an error-coded fault, construct it in a preflight and assert its code and
options before the run. For a stream fault, retain the protocol event names and
terminator. For a route fault, read the active route immediately before dispatch.
For an uncertain commit, prove both that input reached the app and that the
intended uncertainty was returned to the runner.

A real click followed by a `TypeError` is not an `ACTION_MAY_HAVE_COMMITTED`
delivery. More generally: **the presence of a wound does not prove the wound is
the one the experiment card named.**

## Success, sentinel, and exception are different paths

A minimal fault family often needs three rows, not two:

- normal success returns a result;
- a sentinel declines the operation without throwing (`undefined`, `null`,
  `false`, or an empty result, depending on the contract);
- an exception rejects or throws.

The public outcome may be the same by design, but the implementation reaches it
through different code. Measure detection, user-facing reporting, containment,
recovery, and reverification independently. A green application result can
coexist with a missing cache outcome, an absent warning, or a false recovery
claim. Include a later healthy operation to show that one failure did not poison
the next entry or cell.

## A missing field is not automatically missing evidence

Before classifying an absent field, ask in order:

1. Does the contract explicitly allow absence in this state? Then absence may be
   correct, not an observability defect.
2. Was an artifact required for adjudication lost by the harness? Then the run
   is `invalid setup` or ungraded, not a product finding.
3. Does the contract require an outcome that the product failed to produce?
   Then absence itself is a candidate product finding.

Do not write a checker that treats `field exists` as proof of health without
reading the contract. The same absence can mean three different things.

## Correction without contaminating the evidence

### When the fixture failed

- Keep the failed artifacts and count the attempt as `invalid setup`; do not
  quietly delete it or convert its side effects into a product defect.
- Do not retry under the same card. If another experiment is justified, fix the
  root cause, preflight the corrected fault, and freeze a new card with its own
  budget and a link to the invalid run.
- A new card is not a license to bypass an exhausted budget or select a nicer
  result. Its narrower claim and lineage must be explicit.

### When the grader failed

- Preserve the initial grader output unchanged, including its false alarm.
- Write a separate adjudication that names the wrong assertion, the correct
  contract source, and the primary artifacts supporting the new interpretation.
- Do not retro-edit the preregistration or rerun the product merely to make the
  grader agree. Another run is justified only for a new product question.

### When the finding survives

Re-verify the strongest claim end to end. A full-product reproduction and a
minimal function-level reproduction are two evidence layers for **one**
finding, not two findings to inflate a count.

## Final appeal checklist

- Can I name the exact fault type and prove that it arrived?
- Does every mechanical assertion map to the frozen rubric, or did the checker
  add a stronger condition?
- Have I separated business outcome, report outcome, and recovery outcome?
- Are invalid setup and grader corrections visible in the deviation log?
- Did I preserve raw output and keep correction history append-only?
