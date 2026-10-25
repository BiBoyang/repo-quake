# Title

cache: a thrown store write loses the step's `not-written` outcome

# Body

### Problem

When a confirmed trace's `cache.store.write()` rejects, `settleStagedTraces` contains the exception but returns no outcome for that step. Consequently `step.cache.write` is omitted instead of reporting `not-written`.

The undefined-return path already reports `not-written`, so a remote/filesystem store that rejects is less observable than one that declines to write.

### Expected

A confirmed `kind=write` entry whose store cannot complete the write should retain an explicit outcome, normally:

```json
{ "write": "not-written" }
```

The test itself can still pass: the cache is disposable, and cache persistence failure should not turn an already verified application action into a second application attempt.

### Actual

Using npm `e2e@0.21.3`, three direct calls to `settleStagedTraces` with one confirmed staged write produced:

| store write behavior | `outcomes.get(0)` |
| --- | --- |
| returns `{ bytes: 128 }` | `saved` |
| returns `undefined` | `not-written` |
| throws `Error("EACCES")` | `undefined` |

The thrown case is contained; only the outcome is lost.

A full-runner/browser control showed the user-visible consequence. The application performed one save and the test passed, while the custom store logged that settlement reached `write` and threw. The resulting `.e2e/report.json` had no `step.cache.write`, and the console showed only:

```text
Tests  1 passed (1)
Cache  1 missed
```

There is therefore no report signal that the confirmed recording was not persisted.

### Minimal reproduction

The direct probe used this shape with a fresh context per row:

```ts
const context = {
  mode: 'read-write',
  store: {
    read: async () => ({ status: 'miss' }),
    write: async () => { throw new Error('EACCES'); },
  },
  staged: [{
    kind: 'write',
    keyHash: 'a'.repeat(64),
    stepIndex: 0,
    trace: {
      actions: [],
      executor: { name: 'contract-probe', version: '1.0.0' },
      summary: 'verified',
      startPath: '/',
    },
  }],
};

const outcomes = await settleStagedTraces(context, {
  lastVerifiedStepIndex: 1,
  implicatesUnconfirmed: true,
});

expect(outcomes.get(0)).toBe('not-written');
// e2e@0.21.3: actual undefined
```

Changing only `write` to `async () => undefined` makes the same assertion pass.

### Cause

In `packages/e2e/src/cache/context.ts`, the write branch sets `not-written` only when `write()` returns `undefined`. The surrounding catch swallows a rejection without setting an outcome:

https://github.com/tester-army/e2e/blob/69e123b17e04ed624df16d32f3b1ef95ce22c083/packages/e2e/src/cache/context.ts#L188-L223

The same empty-catch structure was present when main was read on 2026-10-25. The runtime reproduction above used the pinned npm release; main was source-inspected rather than rebuilt.

### Suggested direction

When settlement catches a read/write failure for a confirmed `kind=write` entry and no outcome was recorded, preserve `not-written` rather than dropping the entry's outcome. Add adjacent tests for both a returned `undefined` and a rejected write, while retaining existing `keep` and eviction behavior.

### Related

#1363 proposes counting explicit not-saved outcomes in the console summary. That is related but does not cover this case: a thrown write currently has no outcome for the summary to count.

Investigated and drafted with AI assistance. All reported runtime results came from deterministic local fixtures; no real model was called.
