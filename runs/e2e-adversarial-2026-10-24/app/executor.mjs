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

export const countingExecutor = {
  name: 'deterministic-upgrade-executor',
  version: '1.0.0',
  cache: 'inherit',
  async runStep(context) {
    let observation = await context.observe({ tree: true });
    let status = statusOf(observation);
    let target;
    if (status === 'Enterprise') {
      target = flatten(observation.tree).find((node) => node.role === 'button' && (node.name ?? node.text) === 'Fix to Pro');
    } else if (status !== 'Pro') {
      target = flatten(observation.tree).find((node) => node.role === 'button' && /^Upgrade Plan/.test(node.name ?? node.text ?? ''));
    }
    const event = {
      time: new Date().toISOString(),
      attemptId: context.attempt.attemptId,
      instruction: context.step.instruction,
      replayedPrefix: context.replayedPrefix ?? null,
      observedStatus: status,
      target: target ? { id: target.id, name: target.name ?? target.text } : null,
    };
    await appendFile(process.env.E2E_PILOT_CALLS, JSON.stringify(event) + '\n', 'utf8');
    if (status === 'Pro') return { status: 'passed', summary: 'Already Pro; no action required' };
    if (!target) return { status: 'failed', summary: `No recovery action for status ${status}`, errorCode: 'LOCATOR_NOT_FOUND' };
    await context.actions.tap({ id: target.id });
    if (status !== 'Enterprise') {
      observation = await context.observe({ tree: true });
      status = statusOf(observation);
      if (status === 'Enterprise') {
        const repair = flatten(observation.tree).find((node) => node.role === 'button' && (node.name ?? node.text) === 'Fix to Pro');
        if (!repair) return { status: 'failed', summary: 'Enterprise reached but Fix to Pro is missing', errorCode: 'LOCATOR_NOT_FOUND' };
        await context.actions.tap({ id: repair.id });
      }
    }
    context.attachTranscript(`Deterministic executor selected ${target.name ?? target.text}`);
    return { status: 'passed', summary: `Tapped ${target.name ?? target.text}` };
  },
};
