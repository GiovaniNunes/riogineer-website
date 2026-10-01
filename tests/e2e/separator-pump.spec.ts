import { test, expect, type Page } from '@playwright/test';
import { resultsSchema } from '../../src/lib/digital-engineer/contracts';
async function run(page: Page) {
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Run engineering calculation', exact: true }),
  ).toBeEnabled();
  const response = page.waitForResponse('**/api/digital-engineer/calculate');
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  const http = await response;
  expect(http.ok()).toBe(true);
  const r = resultsSchema.parse(await http.json());
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  return r;
}
test('M20 process, provenance, PFD, export, identity and unsupported scope', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 20 reference', exact: true }).click();
  const r = await run(page);
  expect(r.schema_version).toBe('1.14');
  if (r.schema_version !== '1.14') throw Error('Wrong schema');
  const panel = page.getByRole('region', { name: 'Separator-to-pump results' });
  await expect(panel).toContainText('8,068.1851575');
  await expect(panel).toContainText('SEP_PR_1 / liquid');
  await expect(panel).toContainText('PUMP_1 / outlet');
  await expect(page.locator('[data-symbol="pump"]')).toBeAttached();
  for (const [id, number] of [
    ['HYDROCARBON_FEED', 1],
    ['LIQUID_PRODUCT', 2],
    ['VAPOR_PRODUCT', 3],
    ['PUMP_PRODUCT', 4],
  ]) {
    await expect(page.locator(`svg g[data-stream-id="${id}"] text`)).toHaveText(
      `${number} — ${id}`,
    );
  }
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  const density = table
    .getByRole('row')
    .filter({ has: page.getByRole('rowheader', { name: 'Density', exact: true }) });
  await expect(density.locator('td[data-stream-id="PUMP_PRODUCT"]')).toHaveText('—');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download results', exact: true }).click();
  const stream = await (await download).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  expect(JSON.parse(Buffer.concat(chunks).toString())).toEqual(r);
  await page.locator('#pfd-section').screenshot({ path: '.local/m20-pfd.png' });
  const draft = JSON.parse(await page.locator('#requirements').inputValue());
  draft.feeds[0].state.temperature_K += 1;
  await page.locator('#requirements').fill(JSON.stringify(draft));
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Load Milestone 20 identity', exact: true }).click();
  await expect(panel).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toHaveCount(0);
  const identity = await run(page);
  if (identity.schema_version !== '1.14') throw Error('Wrong schema');
  expect(identity.equipment.find((e) => e.type === 'pump')!.work_W).toBe(0);
  await expect(panel).toContainText('Unavailable — equal-pressure identity');
  for (const label of ['alternate', 'scaled']) {
    await page.getByRole('button', { name: `Load Milestone 20 ${label}`, exact: true }).click();
    await run(page);
  }
  await page.getByRole('button', { name: 'Load Milestone 20 unsupported', exact: true }).click();
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'unsupported_qualified_tuple',
  );
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toHaveCount(0);
});
