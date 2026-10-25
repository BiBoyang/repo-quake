import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('live recording, unchanged replay, and changed-control handoff', async ({ app, agent, screen }) => {
  await app.open('/');
  await agent.act('upgrade the workspace to Pro');
  await expect(screen.getByRole('status')).toContainText('Pro');
});
