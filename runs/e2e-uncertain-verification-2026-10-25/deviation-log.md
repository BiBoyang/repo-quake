# Adjudication deviation log

- The focused card funded exactly two executions, U1 and N1. Both ran once; no product execution was repeated.
- This card is separate from the original nine-cell experiment. The original malformed U1 remains `invalid setup`; the corrected fixture was preflighted before this new card by constructing `EngineError(..., { retryable: false })` and checking its code.
- U1 passed every substantive frozen check but the initial `grade.mjs` reported one failed check. The grader had added `mode === "missed"` to the `action-uncertain` assertion. That condition was not in the frozen task contract and contradicts the public semantics for a replay that finished one action before handoff: the correct mode is `agent-concluded`.
- `results/matrix.json` is preserved unchanged as the initial grader output. `results/adjudication.json` records the corrected interpretation from primary artifacts. No preregistration file, raw result or budget was edited after execution, and no new run was used to resolve the grader error.
