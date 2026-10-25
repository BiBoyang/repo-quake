# Focused real-browser uncertain-commit verification — 2026-10-25

## Why a separate experiment exists

The original U1 used a malformed `EngineError` and is invalid setup. This new two-cell card used the archived healthy C0 seed and a preflighted `EngineError('ACTION_MAY_HAVE_COMMITTED', ..., { retryable: false })`. It is not a retry or a budget extension of the original card.

## U1: valid uncertain commit

The real cached browser replay produced:

- `mode=agent-concluded`, `reason=action-uncertain`;
- one completed replayed action (`type`) out of two;
- `uncertainAction=tap button "Save Item"` in the executor's `replayedPrefix`;
- exactly one engine fault record, written after the real tap returned;
- one executor handoff, which verified the independent commit ledger and final UI instead of tapping again;
- exactly one `save-request` and one `save-committed` for `Uncertain 007`;
- final DOM `Saved Uncertain 007`, with the current input and one list item;
- passing test and `write=saved`.

Detection, reporting, containment, recovery and reverification are therefore independently supported for this fixture. No duplicate commit occurred.

## N1: healthy negative control

N1 replayed both actions with `self-finalized`, zero executor calls, `write=kept`, and exactly one correct commit. The healthy path returned after the injected fault.

## Grader correction

`results/matrix.json` retains the initial output, including the failed `U1-action-uncertain` check. That check incorrectly required `mode=missed`; a replay that completed one action before handoff is `agent-concluded`. The frozen task contract required the reason and handoff, not the wrong mode. `results/adjudication.json` and `deviation-log.md` record the correction without changing raw evidence or rerunning the product.

No upstream issue is warranted from these valid U1/N1 outcomes. Chrome and the loopback server were stopped; no model or external provider was used.
