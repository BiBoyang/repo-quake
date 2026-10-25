import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('two-goal replay and side-effect differential', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('prepare upgrade');
  await expect(screen.getByRole('status')).toContainText('Ready');
  await agent.act('finish upgrade');
  await expect(screen.getByRole('status')).toContainText('Pro');
});
