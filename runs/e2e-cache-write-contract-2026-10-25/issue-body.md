## What happened

When a confirmed trace's `cache.store.write()` rejects, `settleStagedTraces` contains the exception but returns no outcome for that step. `step.cache.write` is therefore omitted instead of `not-written`.

The undefined-return path already reports `not-written`. I expected a rejected write to produce the same explicit outcome while keeping cache persistence best-effort and the test green.

## Minimal reproduction

In a new directory:

```sh
npm init -y
npm pkg set type=module
npm install e2e@0.21.3
# Save the script below as repro.mjs, then run:
node repro.mjs
```

```js
import { settleStagedTraces } from './node_modules/e2e/dist/cache/context.js';

async function outcome(behavior) {
  const context = {
    mode: 'read-write',
    store: {
      read: async () => ({ status: 'miss' }),
      write: async () => {
        if (behavior === 'throw') throw new Error('EACCES');
        return behavior === 'saved' ? { bytes: 128 } : undefined;
      },
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
  const writes = await settleStagedTraces(context, {
    lastVerifiedStepIndex: 1,
    implicatesUnconfirmed: true,
  });
  return writes.get(0);
}

for (const behavior of ['saved', 'undefined', 'throw']) {
  console.log(`${behavior} -> ${String(await outcome(behavior))}`);
}
```

Actual output:

```text
saved -> saved
undefined -> not-written
throw -> undefined
```

Expected the last line to be `throw -> not-written`.

## Versions

- `e2e 0.21.3`
- `@e2e-dev/web 0.15.3` (full-runner witness only; the defect is in core cache settlement)
- Node `v25.4.0`
- `Darwin 27.2.0 arm64`
- Engine: **not engine specific**

## Anything else

In a full-runner/browser control, the application made one save, the test passed, and the custom store logged the write rejection. The report omitted `step.cache.write`; the console showed only `Tests 1 passed` and `Cache 1 missed`.

From the code, the write branch maps a returned `undefined` to `not-written`, but the catch handles a rejection without recording an outcome:

https://github.com/tester-army/e2e/blob/69e123b17e04ed624df16d32f3b1ef95ce22c083/packages/e2e/src/cache/context.ts#L188-L223

I saw the same structure on main on 2026-10-25. The reproduction used the pinned npm release; main was source-inspected, not rebuilt.

`not-written` is already the documented outcome for a store that did not write a confirmed recording:

https://github.com/tester-army/e2e/blob/69e123b17e04ed624df16d32f3b1ef95ce22c083/docs/cache.mdx#L48-L57

Related: #939 introduced cache-outcome reporting so automation could consume settlement results; an absent outcome removes that signal. #1363 proposes counting explicit not-saved outcomes, but cannot cover a rejection that never gets one.

If you’d like, I can open a small PR with a regression test and docs update.

Investigated and drafted with AI assistance. All runtime results came from deterministic local fixtures; no real model was called.
