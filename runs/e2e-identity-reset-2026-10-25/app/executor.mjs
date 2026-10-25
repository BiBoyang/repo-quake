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

function button(observation, pattern) {
  return flatten(observation.tree).find((node) =>
    node.role === 'button' && pattern.test(node.name ?? node.text ?? ''),
  );
}

export const countingExecutor = {
  name: 'deterministic-upgrade-executor',
  version: '1.0.0',
  cache: 'inherit',
  async runStep(context) {
    const observation = await context.observe({ tree: true });
    const instruction = context.step.instruction;
    const status = statusOf(observation);
    let target;
    if (status === 'Enterprise') {
      target = button(observation, /^Fix to Pro$/);
    } else if (instruction === 'prepare upgrade') {
      target = button(observation, /^Prepare Upgrade$/);
    } else if (instruction === 'finish upgrade') {
      target = button(observation, /^Finish Upgrade/);
    } else if (instruction === 'noop') {
      target = button(observation, /^Noop$/);
    }
    const event = {
      time: new Date().toISOString(),
      attemptId: context.attempt.attemptId,
      instruction,
      observedStatus: status,
      replayedPrefix: context.replayedPrefix ?? null,
      target: target ? { id: target.id, name: target.name ?? target.text } : null,
    };
    await appendFile(process.env.E2E_PILOT_CALLS, JSON.stringify(event) + '\n', 'utf8');
    if (status === 'Pro') return { status: 'passed', summary: 'Already Pro; no action required' };
    if (!target) return { status: 'failed', summary: `No action for ${instruction} at status ${status}`, errorCode: 'LOCATOR_NOT_FOUND' };
    await context.actions.tap({ id: target.id });
    context.attachTranscript(`Deterministic executor selected ${target.name ?? target.text}`);
    return { status: 'passed', summary: `Tapped ${target.name ?? target.text}` };
  },
};
