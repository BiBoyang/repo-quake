import { replayTrace } from './node_modules/e2e/dist/agent/replay.js';
import { AgentError } from './node_modules/e2e/dist/agent/error.js';

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
  observe: async () => screen,
  actions: {
    tap: async () => {
      calls += 1;
      throw new AgentError('ACTION_MAY_HAVE_COMMITTED', 'the click committed but its outcome is unknown');
    },
  },
};
const trace = {
  actions: [{ name: 'tap', summary: 'tap button "Upgrade Plan"', target: { role: 'button', name: 'Upgrade Plan' } }],
  executor: { name: 'deterministic-upgrade-executor', version: '1.0.0' },
  summary: 'Tapped Upgrade Plan',
  startPath: '/',
  endPath: '/',
  endAnchors: [{ role: 'status', name: 'Pro' }],
};
const outcome = await replayTrace(host, trace, { initial: screen });
const evidence = { outcome, calls };
console.log(JSON.stringify(evidence, null, 2));
if (outcome.completed !== false) throw new Error(`Expected incomplete replay, got ${JSON.stringify(outcome)}`);
if (outcome.stopReason !== 'action-uncertain') throw new Error(`Expected action-uncertain, got ${outcome.stopReason}`);
if (!outcome.uncertainAction?.includes('Upgrade Plan')) throw new Error('Missing uncertain action detail');
if (calls !== 1) throw new Error(`Expected exactly one committed action, got ${calls}`);
