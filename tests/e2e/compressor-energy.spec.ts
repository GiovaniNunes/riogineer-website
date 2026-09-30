import { expect, test } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const requirements = JSON.parse(
  execFileSync(
    resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      "import json; from benchmarks.compressor_energy.compare_production import reference, requirements; print(json.dumps(requirements(reference()['cases'][0]['inputs'])))",
    ],
    { encoding: 'utf8' },
  ),
);

test('rigorous compressor uses the normal validated workflow and distinguishes fluid power', async ({
  page,
}) => {
  test.setTimeout(60000);
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page
    .getByLabel('requirements.json — explicit units and development assumptions')
    .fill(JSON.stringify(requirements));
  for (const [operation, label] of [
    ['validate-requirements', 'Validate requirements'],
    ['build-flowsheet', 'Generate PFD'],
    ['calculate', 'Run engineering calculation'],
  ]) {
    const pending = page.waitForResponse(`**/api/digital-engineer/${operation}`);
    await page.getByRole('button', { name: label, exact: true }).click();
    expect((await pending).status()).toBe(200);
  }
  await expect(page.getByRole('status')).toContainText('Calculation complete');
  const result = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  expect(result.schema_version).toBe('1.8');
  expect(result.equipment[0].model.id).toBe('rigorous_isentropic_pr');
  const d = result.equipment[0].thermodynamics;
  expect(d.ps.capability).toBe('flash_PS');
  expect(d.ph.capability).toBe('flash_PH');
  expect(d.actual_outlet.temperature_K).toBeCloseTo(376.43259014901105, 6);
  expect(d.fluid_power_W).toBeCloseTo(375283.3155875835, 5);
  const view = page.getByRole('region', { name: 'Rigorous compressor results', exact: true });
  await expect(view).toContainText('rigorous_isentropic_pr@1.0');
  await expect(view).toContainText('Actual fluid power (W)');
  await expect(view).toContainText('Mechanical losses and driver power are not calculated');
  await expect(page.locator('svg [data-symbol="compressor"]')).toBeVisible();
  await expect(
    page.getByRole('region', { name: 'Compression and network work', exact: true }),
  ).toHaveCount(0);
});
