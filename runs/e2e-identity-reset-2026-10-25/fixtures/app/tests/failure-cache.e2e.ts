import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('failed later assertion does not poison the replay cache', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('upgrade the workspace to Pro');
  await expect(screen.getByRole('status')).toContainText(process.env.EXPECTED_STATUS ?? 'Pro');
});
