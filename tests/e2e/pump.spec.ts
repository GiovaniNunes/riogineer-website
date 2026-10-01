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
test('M18 canonical table, PFD, download, identity and stale rejection', async ({ page }) => {
  test.setTimeout(90000);
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 18 pump reference' }).click();
  const r = await run(page);
  expect(r.schema_version).toBe('1.12');
  await expect(page.locator('[data-symbol="pump"]')).toBeAttached();
  const panel = page.getByRole('region', { name: 'Liquid pump results' });
  await expect(panel).toContainText('110,622.860113');
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  for (const [name, value] of [
    ['Molar flow', '360'],
    ['Molecular mass', '51.10908'],
    ['methane — molar fraction', '0.5'],
    ['n_hexane — molar fraction', '0.5'],
    ['Density', '—'],
  ]) {
    const row = table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name, exact: true }) });
    for (const id of ['HYDROCARBON_FEED', 'PUMP_PRODUCT'])
      await expect(row.locator(`td[data-stream-id="${id}"]`)).toHaveText(value);
  }
  await expect(page.locator('svg g[data-stream-id="PUMP_PRODUCT"] text')).toHaveText(
    '2 — PUMP_PRODUCT',
  );
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download results', exact: true }).click();
  const stream = await (await download).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  expect(JSON.parse(Buffer.concat(chunks).toString())).toEqual(r);
  const editor = page.locator('#requirements');
  const input = JSON.parse(await editor.inputValue());
  input.equipment[0].parameters.outlet_pressure_Pa_abs = 20e6;
  await editor.fill(JSON.stringify(input));
  await expect(panel).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toBeDisabled();
  const identity = await run(page);
  if (identity.schema_version !== '1.12') throw Error('Wrong version');
  expect(identity.equipment[0].work_W).toBe(0);
  await expect(panel).toContainText('Unavailable — equal-pressure identity');
  input.equipment[0].parameters.outlet_pressure_Pa_abs = 20001000;
  await editor.fill(JSON.stringify(input));
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'positive_rise_below_floor',
  );
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});
