import { web } from '@e2e-dev/web';
import { countingExecutor } from './executor.mjs';

export default {
  projectId: 'e2e-replay-pilot',
  targets: [
    {
      engine: web({ connect: { cdpEndpoint: async () => 'http://127.0.0.1:9222' } }),
      app: { url: 'http://127.0.0.1:4173' },
    },
  ],
  agents: {
    default: { executor: countingExecutor, context: process.env.E2E_AGENT_CONTEXT ?? 'A' },
  },
  cache: { mode: 'read-write', strict: false },
  workers: 1,
  retries: 0,
  timeout: 60000,
  launchTimeout: 60000,
};
