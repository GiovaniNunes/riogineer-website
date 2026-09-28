import { expect, test, type Page } from '@playwright/test';
async function run(page: Page) {
  for (const [operation, name] of [
    ['validate-requirements', 'Validate requirements'],
    ['build-flowsheet', 'Generate PFD'],
    ['calculate', 'Run engineering calculation'],
  ]) {
    const pending = page.waitForResponse(`**/api/digital-engineer/${operation}`);
    await page.getByRole('button', { name, exact: true }).click();
    expect((await pending).status()).toBe(200);
  }
  await expect(page.getByRole('status')).toContainText('Calculation complete');
}
test('Milestone 5 sequential heater state, duty, identity, properties and regeneration', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 5 reference' }).click();
  await run(page);
  const flow = JSON.parse(await page.getByLabel('flowsheet.json', { exact: true }).innerText());
  const result = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  expect(flow.case_id).toBe('MILESTONE_5_SEQUENTIAL_PROCESS');
  expect(result.case_id).toBe(flow.case_id);
  expect(result.input_sha256).toBe(flow.calculation.input_sha256);
  expect(result.requirements_sha256).toBe(flow.requirements_sha256);
  expect(result.execution.equipment_order).toEqual(['SEP_1', 'HEATER_1', 'SEP_2']);
  for (const id of [
    'FEED',
    'SEP_1',
    'HEATER_1',
    'SEP_2',
    'GAS_1_SINK',
    'WATER_1_SINK',
    'GAS_2_SINK',
    'WATER_2_SINK',
    'OIL_PRODUCT_SINK',
  ])
    await expect(page.locator(`svg [data-equipment-id="${id}"]`)).toBeVisible();
  await expect(
    page.locator('svg [data-equipment-id="HEATER_1"] [data-symbol="heater"]'),
  ).toBeVisible();
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  async function identity() {
    await expect(table.locator('thead [data-stream-id]')).toHaveCount(8);
    for (const stream of flow.streams) {
      const label = `${stream.engineering_number} — ${stream.service.toUpperCase()}`;
      await expect(table.locator(`thead [data-stream-id="${stream.id}"]`)).toHaveText(
        `${label}ID: ${stream.id}`,
      );
      await expect(page.locator(`svg g[data-stream-id="${stream.id}"] text`)).toHaveText(label);
    }
  }
  await identity();
  const rows = [
    [
      'Total mass flow',
      ['110,000', '22,000', '77,550', '10,450', '77,550', '3,850', '73,205', '495'],
    ],
    [
      'Temperature',
      ['313.15', '313.15', '313.15', '313.15', '333.15', '333.15', '333.15', '333.15'],
    ],
    ['Pressure', Array(8).fill('2,000,000')],
    [
      'n_hexane — component mass flow',
      ['77,000', '0', '77,000', '0', '77,000', '3,850', '73,150', '0'],
    ],
    ['water — component mass flow', ['11,000', '0', '550', '10,450', '550', '0', '55', '495']],
    ['methane — component mass flow', ['22,000', '22,000', '0', '0', '0', '0', '0', '0']],
  ] as const;
  for (const [name, values] of rows)
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .locator('td[data-stream-id]'),
    ).toHaveText([...values]);
  for (const name of [
    'Molar flow',
    'Molecular mass',
    'Density',
    'Gas volumetric flow',
    'Oil volumetric flow',
    'Water volumetric flow',
    'methane — molar fraction',
    'n_hexane — molar fraction',
    'water — molar fraction',
  ])
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .locator('td[data-stream-id]'),
    ).toHaveText(Array(8).fill('—'));
  for (const c of ['methane', 'n_hexane', 'water']) {
    const row = table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: `${c} — mass fraction`, exact: true }) });
    for (const s of flow.streams)
      await expect(row.locator(`td[data-stream-id="${s.id}"]`)).toHaveText(
        new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 }).format(
          result.streams[s.id].component_mass_fractions[c],
        ),
      );
  }
  await expect(
    page
      .getByRole('table', { name: 'Equipment balance checks' })
      .getByRole('row')
      .filter({ hasText: 'HEATER_1' }),
  ).toContainText('953,883.333333');
  await expect(
    page
      .getByRole('listitem')
      .filter({ hasText: 'Heating does not cause or predict downstream separator recoveries:' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await identity();
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('PFD ready');
  const regenerated = JSON.parse(
    await page.getByLabel('flowsheet.json', { exact: true }).innerText(),
  );
  expect(regenerated.streams).toEqual(flow.streams);
  await page.getByRole('button', { name: 'Run engineering calculation' }).click();
  await expect(page.getByRole('status')).toContainText('Calculation complete');
  await identity();
  await page.locator('#pfd-section').screenshot({ path: '.local/milestone-5-pfd.png' });
});
test('Bia ↔ Milestone 5 ↔ Milestone 4 clears cross-case artifacts', async ({ page }) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await run(page);
  for (const name of [
    'Load Milestone 5 reference',
    'Load Milestone 4 reference',
    'Load Milestone 5 reference',
    'Restore reference',
  ]) {
    await page.getByRole('button', { name, exact: true }).click();
    await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
    await expect(page.getByLabel('results.json', { exact: true })).toHaveText('null');
    await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
    await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
    await run(page);
  }
});
