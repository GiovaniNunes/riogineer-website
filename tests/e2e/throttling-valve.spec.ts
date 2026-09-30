import { expect, test, type Page } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
const requirements = JSON.parse(
  execFileSync(
    resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      "import json; from benchmarks.throttling_valve.compare_production import reference,requirements; print(json.dumps(requirements(reference()['cases'][0]['inputs'])))",
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
test('one valve outlet, rigorous states, recalculation and failed-result invalidation', async ({
  page,
}) => {
  test.setTimeout(120000);
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  await editor.fill(JSON.stringify(requirements));
  await run(page);
  const view = page.getByRole('region', { name: 'Rigorous throttling valve results', exact: true });
  await expect(view).toContainText('rigorous_isenthalpic_pr@1.0');
  await expect(view).toContainText('vapor_liquid');
  await expect(view).toContainText('flash_PH');
  await expect(view).toContainText('high_accuracy');
  await expect(view).toContainText('One overall outlet');
  await expect(page.locator('svg [data-symbol="throttling-valve"]')).toBeVisible();
  await expect(page.getByText('Calculated network duty:', { exact: false })).toHaveCount(0);
  await expect(page.getByRole('table', { name: 'Equipment balance checks' })).toHaveCount(0);
  const initial = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  expect(Object.keys(initial.streams)).toEqual(['FEED', 'PRODUCT']);
  expect(initial.equipment[0].thermodynamics.outlet.temperature_K).toBeCloseTo(291.74213865698, 6);
  await page
    .getByRole('figure', { name: 'Read-only process flow diagram' })
    .screenshot({ path: '/tmp/m16-pfd.png' });
  const changed = structuredClone(requirements);
  changed.equipment[0].parameters.outlet_pressure_Pa_abs = 1e7;
  await editor.fill(JSON.stringify(changed));
  await expect(view).toHaveCount(0);
  await expect(page.locator('[data-results-status="stale"]')).toBeVisible();
  await run(page);
  await expect(view).toContainText('304.210');
  const bad = structuredClone(requirements);
  bad.feeds[0].state.pressure_Pa_abs = 6e6;
  await editor.fill(JSON.stringify(bad));
  await expect(view).toHaveCount(0);
  await run(page, false);
  await expect(view).toHaveCount(0);
  await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'inlet_service_scope',
  );
});
