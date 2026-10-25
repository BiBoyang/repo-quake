import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('no-change step is not recorded', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('noop');
  await expect(screen.getByRole('status')).toContainText('Idle');
});
