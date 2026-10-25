import { test } from '@e2e-dev/web';
import { expect, unique } from 'e2e';

test('unique parameter collision is not recorded', async ({ app, agent, screen }) => {
  await app.open('/');
  const requestId = unique('same-value');
  await agent.act('finish upgrade', { params: { requestId, other: 'same-value' } });
  await expect(screen.getByRole('status')).toContainText('Pro');
});
