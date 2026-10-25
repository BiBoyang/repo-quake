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

function buttons(observation) {
  return flatten(observation.tree).filter((node) =>
    node.role === 'button' && /^Upgrade Plan|^Prepare Upgrade|^Finish Upgrade/.test(node.name ?? node.text ?? ''),
  );
}

export const countingExecutor = {
  name: 'deterministic-upgrade-executor',
  version: '1.0.0',
  cache: 'inherit',
  async runStep(context) {
    const observation = await context.observe({ tree: true });
    const status = statusOf(observation);
    const matches = buttons(observation);
    const event = {
      time: new Date().toISOString(),
      attemptId: context.attempt.attemptId,
      instruction: context.step.instruction,
      params: context.step.params ?? null,
      observedStatus: status,
      replayedPrefix: context.replayedPrefix ?? null,
      matches: matches.map((node) => ({ id: node.id, name: node.name ?? node.text }),
    };
    await appendFile(process.env.E2E_PILOT_CALLS, JSON.stringify(event) + '\n', 'utf8');
    if (status === 'Pro') return { status: 'passed', summary: 'Already Pro; no action required' };
    if (matches.length > 1) {
      return { status: 'failed', summary: 'Ambiguous upgrade controls', errorCode: 'LOCATOR_AMBIGUOUS' };
    }
    const target = matches[0];
    if (!target) return { status: 'failed', summary: `No action for ${context.step.instruction} at status ${status}`, errorCode: 'LOCATOR_NOT_FOUND' };
    await context.actions.tap({ id: target.id });
    context.attachTranscript(`Deterministic executor selected ${target.name ?? target.text}`);
    return { status: 'passed', summary: `Tapped ${target.name ?? target.text}` };
  },
};
