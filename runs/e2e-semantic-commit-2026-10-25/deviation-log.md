# Deviation and invalid-setup log

- All nine executions in the frozen card were attempted exactly once. The execution ledger has nine entries; there was no budget overrun and no replacement run.
- U1 is `invalid setup`, not product evidence. `uncertain-engine.mjs` called `new EngineError(code, message)` without the required `{ retryable }` options object. The real taps happened, but constructing the intended error threw a `TypeError` instead. Replay therefore reported `action-failed`, and the executor repeated the save. The duplicate requests are preserved as fixture-induced behavior and are not attributed to e2e.
- U1 was not retried under this card. A new two-execution card with a separately frozen budget and an EngineError constructor preflight was created at `runs/e2e-uncertain-verification-2026-10-25`; its results do not alter this run's invalid classification.
- The initial experiment-card validation rejected prose in `controls.negative` and `controls.positive`. This happened before the first execution; the controls were changed to arm IDs and the card was then frozen. It is not a post-registration change.
- Chrome/CDP and the loopback server were stopped after the matrix. No real model, provider or third-party write was used.
