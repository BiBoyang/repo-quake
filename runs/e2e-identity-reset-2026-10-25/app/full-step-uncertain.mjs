import { readFile } from 'node:fs/promises';
import { StepTraceSession } from './node_modules/e2e/dist/agent/step-cache.js';
import { AgentError } from './node_modules/e2e/dist/agent/error.js';

const entry = JSON.parse(await readFile(new URL('./baseline-trace.json', import.meta.url), 'utf8'));
const keyHash = '3c9cc78e1c7eb08360b971adf4ffce7ddc52e5ec96bd5bf6825e6d68392b8d50';
const screen = {
  kind: 'semantic',
  path: '/',
  viewport: { width: 1280, height: 720 },
  nodes: new Map([
    ['n5', { id: 'n5', role: 'button', name: 'Upgrade Plan' }],
    ['n6', { id: 'n6', role: 'status', name: 'Pro', text: 'Pro' }],
  ]),
};
let calls = 0;
const host = {
  traceEligible: true,
  signal: new AbortController().signal,
  remainingMs: () => 10000,
  replaying: () => undefined,
  observe: async () => screen,
  actions: {
    tap: async () => {
      calls += 1;
      throw new AgentError('ACTION_MAY_HAVE_COMMITTED', 'the click committed but its outcome is unknown');
    },
  },
};
const cache = {
  mode: 'read-write',
  replayEligible: true,
  strict: false,
  staged: [],
  store: {
    writable: true,
    read: async () => ({ status: 'hit', entry, bytes: JSON.stringify(entry).length }),
    write: async () => ({ bytes: 0 }),
    delete: async () => undefined,
  },
  claimKey: () => ({
    keyHash,
    context: entry.keyedBy ?? {
      cacheSchema: 'trace-1', policyVersion: '0.1', project: 'pilot', platform: 'web',
      engineName: 'web', engineSpiVersion: 1, appIdentity: 'local', agentContextDigest: 'ctx',
    },
    step: entry.payload.recordedFor ?? { testId: 'pilot', targetId: 'web', instructionDigest: 'x', paramsDigest: 'y', callIndex: 0, agent: 'default' },
  }),
};
const session = new StepTraceSession(host, {
  cache,
  instruction: 'upgrade the workspace to Pro',
  params: undefined,
  templates: [],
  executor: { name: 'deterministic-upgrade-executor', version: '1.0.0' },
  agent: { name: 'default', context: undefined },
  redact: (text) => text,
  redactCut: (text) => text,
  maxActions: 25,
  stepIndex: 0,
});
const verdict = await session.begin();
const info = session.info;
const evidence = { verdict, info, calls };
console.log(JSON.stringify(evidence, null, 2));
if (verdict !== undefined) throw new Error(`Expected handoff to executor, got ${JSON.stringify(verdict)}`);
if (!info || info.reason !== 'action-uncertain') throw new Error(`Expected action-uncertain, got ${JSON.stringify(info)}`);
if (!info.detail?.includes('Upgrade Plan')) throw new Error('Missing uncertain action detail');
if (calls !== 1) throw new Error(`Expected one committed action, got ${calls}`);
