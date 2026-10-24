import { appendFile } from 'node:fs/promises';

function flatten(node, out = []) {
  if (!node) return out;
  out.push(node);
  for (const child of node.children ?? []) flatten(child, out);
  return out;
}

export const countingExecutor = {
  name: 'deterministic-upgrade-executor',
  version: '1.0.0',
  cache: 'inherit',
  async runStep(context) {
    const observation = await context.observe({ tree: true });
    const nodes = flatten(observation.tree);
    const target = nodes.find((node) =>
      node.role === 'button' && /^Upgrade Plan/.test(node.name ?? node.text ?? ''),
    );
    const event = {
      time: new Date().toISOString(),
      attemptId: context.attempt.attemptId,
      instruction: context.step.instruction,
      replayedPrefix: context.replayedPrefix ?? null,
      target: target ? { id: target.id, name: target.name ?? target.text } : null,
    };
    await appendFile(process.env.E2E_PILOT_CALLS, JSON.stringify(event) + '\n', 'utf8');
    if (!target) {
      return { status: 'failed', summary: 'No Upgrade Plan button found', errorCode: 'LOCATOR_NOT_FOUND' };
    }
    await context.actions.tap({ id: target.id });
    context.attachTranscript(`Deterministic executor selected ${target.name ?? target.text}`);
    return { status: 'passed', summary: `Tapped ${target.name ?? target.text}` };
  },
};
