import { appendFile } from 'node:fs/promises';

function flatten(node, out = []) {
  if (!node) return out;
  out.push(node);
  for (const child of node.children ?? []) flatten(child, out);
  return out;
}
function statusOf(observation) {
  const status = flatten(observation.tree).find((node) => node.role === 'status');
  return status?.text ?? status?.name ?? '';
}
function control(observation, role, name) {
  return flatten(observation.tree).find((node) => node.role === role && (node.name ?? node.text ?? '') === name);
}
async function log(value) {
  await appendFile(process.env.E2E_CALLS_LOG, JSON.stringify({ at: new Date().toISOString(), ...value }) + '\n', 'utf8');
}
async function serverEvents() {
  const response = await fetch('http://127.0.0.1:4173/events', { cache: 'no-store' });
  if (!response.ok) throw new Error(`witness returned ${response.status}`);
  return response.json();
}
async function waitForSaved(context, item, requireCommit) {
  for (let index = 0; index < 70; index += 1) {
    if (context.signal.aborted) throw new Error('verification aborted');
    if (requireCommit) {
      const events = await serverEvents();
      if (!events.some((event) => event.type === 'save-committed' && event.item === item)) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        continue;
      }
    }
    const observation = await context.observe({ tree: true });
    if (statusOf(observation) === `Saved ${item}`) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`saved state was not observed for ${item}`);
}

export const deterministicExecutor = {
  name: 'deterministic-semantic-executor',
  version: '1.0.0',
  cache: 'inherit',
  async runStep(context) {
    const item = context.step.params?.item;
    if (typeof item !== 'string' || item === '') {
      return { status: 'failed', summary: 'The item parameter is missing', errorCode: 'INVALID_ARGUMENT' };
    }
    await log({
      kind: 'call',
      runId: process.env.E2E_RUN_ID,
      attemptId: context.attempt.attemptId,
      item,
      replayedPrefix: context.replayedPrefix ?? null,
    });
    if (context.replayedPrefix?.stopReason === 'action-uncertain') {
      await waitForSaved(context, item, true);
      await log({ kind: 'verification', runId: process.env.E2E_RUN_ID, item, result: 'committed-once-not-repeated' });
      context.attachTranscript('Verified the independent commit ledger and final UI; did not repeat the uncertain tap.');
      return { status: 'passed', summary: `Verified the uncertain save of ${item} without repeating it` };
    }
    let observation = await context.observe({ tree: true });
    if (statusOf(observation) === `Saved ${item}`) {
      return { status: 'passed', summary: `Already saved ${item}` };
    }
    const input = control(observation, 'textbox', 'Item name');
    const save = control(observation, 'button', 'Save Item');
    if (!input || !save) {
      return { status: 'failed', summary: 'Item controls were not found', errorCode: 'LOCATOR_NOT_FOUND' };
    }
    await context.actions.type({ id: input.id }, item);
    await context.actions.tap({ id: save.id });
    await waitForSaved(context, item, false);
    context.attachTranscript(`Filled ${item}, tapped Save Item once, and observed the asynchronous saved state.`);
    return { status: 'passed', summary: `Saved ${item}` };
  },
};
