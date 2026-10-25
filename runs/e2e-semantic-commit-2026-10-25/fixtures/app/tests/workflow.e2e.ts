import { writeFile } from 'node:fs/promises';
import { test } from '@e2e-dev/web';
import { expect, unique } from 'e2e';

const item = process.env.E2E_ITEM_VALUE ?? 'Unconfigured item';
const alias = process.env.E2E_ALIAS_VALUE ?? 'ordinary';
const route = process.env.E2E_ROUTE ?? '/';

test('asynchronous parameterized save', async ({ app, agent, screen, browser }) => {
  await app.open(route);
  await agent.act('save item {item}', { params: { item: unique(item), alias } });
  await expect(screen.getByRole('status')).toContainText(`Saved ${item}`);
  const dom = await browser.evaluate(() => ({
    path: location.pathname,
    status: document.querySelector('#status')?.textContent ?? null,
    input: document.querySelector('#item')?.value ?? null,
    items: Array.from(document.querySelectorAll('#items li')).map((node) => node.textContent),
  }));
  await writeFile(process.env.E2E_DOM_OUTPUT, JSON.stringify(dom, null, 2) + '\n', 'utf8');
});
