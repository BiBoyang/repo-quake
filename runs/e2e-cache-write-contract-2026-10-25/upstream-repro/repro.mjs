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
