import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('ambiguous controls must not be clicked blindly', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('finish upgrade');
  await expect(screen.getByRole('status')).toContainText('Pro');
});
