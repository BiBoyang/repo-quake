import { appendFile } from 'node:fs/promises';
import { web } from '@e2e-dev/web';
import { defineEngine, EngineError } from 'e2e/engine';

export function auditedWeb() {
  const base = web({ connect: { cdpEndpoint: async () => 'http://127.0.0.1:9222' } });
  const { capabilities: _capabilities, ...spec } = base;
  return defineEngine({
    ...spec,
    async perform(ref, action, operation) {
      await base.perform(ref, action, operation);
      if (process.env.E2E_UNCERTAIN_TAP === '1' && action.kind === 'tap') {
        await appendFile(process.env.E2E_FAULT_LOG, JSON.stringify({
          at: new Date().toISOString(),
          fault: 'commit-then-ACTION_MAY_HAVE_COMMITTED',
          action: action.kind,
        }) + '\n', 'utf8');
        throw new EngineError('ACTION_MAY_HAVE_COMMITTED', 'fixture committed the tap, then lost the outcome');
      }
    },
  });
}
