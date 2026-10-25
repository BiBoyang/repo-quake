import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('agent context changes must not reuse the old flow', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('finish upgrade');
  await expect(screen.getByRole('status')).toContainText('Pro');
});
