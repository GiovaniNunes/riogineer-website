import { expect, test, type Page } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
const requirements = JSON.parse(
  execFileSync(
    resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      "import json; from benchmarks.two_stream_heat_exchanger.compare_production import reference,requirements; print(json.dumps(requirements(reference()['cases'][0]['inputs'])))",
    ],
    { encoding: 'utf8' },
  ),
);
async function run(page: Page, success = true) {
  for (const [operation, label] of [
    ['validate-requirements', 'Validate requirements'],
    ['build-flowsheet', 'Generate PFD'],
    ['calculate', 'Run engineering calculation'],
  ]) {
    const pending = page.waitForResponse(`**/api/digital-engineer/${operation}`);
    await page.getByRole('button', { name: label, exact: true }).click();
    const response = await pending;
    if (operation === 'calculate' && !success)
      expect(response.status()).toBeGreaterThanOrEqual(400);
    else expect(response.status()).toBe(200);
  }
}
test('four ports, both specification modes, atomic stale invalidation and failed service', async ({
  page,
}) => {
  test.setTimeout(120000);
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  await editor.fill(JSON.stringify(requirements));
  await run(page);
  const view = page.getByRole('region', {
    name: 'Rigorous two-stream heat exchanger results',
    exact: true,
  });
  await expect(view).toContainText('Mode A');
  await expect(view).toContainText('No material transfer');
  for (const role of ['hot_in', 'hot_out', 'cold_in', 'cold_out'])
    await expect(page.locator(`svg [data-port="${role}"]`)).toBeVisible();
  await page
    .getByRole('figure', { name: 'Read-only process flow diagram' })
    .screenshot({ path: '/tmp/m15-pfd.png' });
  const a = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  const d = a.equipment[0].thermodynamics;
  expect(d.hot_outlet.temperature_K).toBe(390);
  expect(d.cold_outlet.temperature_K).toBeCloseTo(323.4048867266808, 6);
  expect(d.Q_hot_W).toBeLessThan(0);
  expect(d.Q_cold_W).toBeGreaterThan(0);
  const b = structuredClone(requirements);
  delete b.equipment[0].parameters.hot_outlet_temperature_K;
  b.equipment[0].parameters.mode = 'specified_cold_outlet_temperature';
  b.equipment[0].parameters.cold_outlet_temperature_K = d.cold_outlet.temperature_K;
  await editor.fill(JSON.stringify(b));
  await expect(page.locator('[data-results-status="stale"]')).toBeVisible();
  await expect(view).toHaveCount(0);
  await run(page);
  await expect(view).toContainText('Mode B');
  const updated = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  expect(updated.equipment[0].thermodynamics.hot_outlet.temperature_K).toBeCloseTo(390, 6);
  const bad = structuredClone(requirements);
  bad.equipment[0].parameters.hot_outlet_temperature_K = 440;
  await editor.fill(JSON.stringify(bad));
  await expect(view).toHaveCount(0);
  await run(page, false);
  await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
  await expect(view).toHaveCount(0);
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'heat_direction',
  );
});
