import { test, expect } from '@playwright/test';

test('Milestone 4 graph → seven numbered streams → branch/merge results', async ({ page }) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 4 reference' }).click();
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid');
  const built = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  const flowsheet = await (await built).json();
  expect(flowsheet.schema_version).toBe('1.2');
  await expect(page.getByRole('img', { name: 'Multi-equipment PFD' })).toBeVisible();
  for (const id of ['FEED', 'SEP_1', 'GAS_SINK', 'WATER_SINK', 'SPLIT_1', 'MIX_1', 'OIL_SINK'])
    await expect(page.locator(`svg [data-equipment-id="${id}"]`)).toBeVisible();
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  const ids = ['FEED', 'GAS', 'OIL', 'WATER', 'OIL_A', 'OIL_B', 'OIL_PRODUCT'];
  async function checkIdentity() {
    await expect(table.locator('thead [data-stream-id]')).toHaveCount(7);
    for (const id of ids) {
      const stream = flowsheet.streams.find((s: { id: string }) => s.id === id);
      const label = `${stream.engineering_number} — ${stream.service.toUpperCase()}`;
      await expect(page.locator(`svg g[data-stream-id="${id}"] text`)).toHaveText(label);
      await expect(table.locator(`thead [data-stream-id="${id}"]`)).toHaveText(`${label}ID: ${id}`);
    }
  }
  async function calculate() {
    const pending = page.waitForResponse('**/api/digital-engineer/calculate');
    await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
    const result = await (await pending).json();
    await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
    expect(result.execution.equipment_order).toEqual(['SEP_1', 'SPLIT_1', 'MIX_1']);
    expect(result.balances.mass.total_residual_kg_h).toBe(0);
    await checkIdentity();
  }
  await checkIdentity();
  await calculate();
  const rows = [
    [
      'Total mass flow',
      ['kg/h', '110,000', '22,000', '77,550', '10,450', '46,530', '31,020', '77,550'],
    ],
    ['Pressure', ['Pa absolute', ...Array(7).fill('2,000,000')]],
    ['Temperature', ['K', ...Array(7).fill('313.15')]],
    [
      'n_hexane — component mass flow',
      ['kg/h', '77,000', '0', '77,000', '0', '46,200', '30,800', '77,000'],
    ],
    ['water — component mass flow', ['kg/h', '11,000', '0', '550', '10,450', '330', '220', '550']],
    ['methane — component mass flow', ['kg/h', '22,000', '22,000', '0', '0', '0', '0', '0']],
  ] as const;
  for (const [name, expected] of rows)
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .getByRole('cell'),
    ).toHaveText([...expected]);
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
    ).toHaveText(Array(7).fill('—'));
  await expect(
    page.getByRole('table', { name: 'Equipment balance checks' }).getByRole('row'),
  ).toHaveCount(4);
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await checkIdentity();
  await calculate();
  const regeneration = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  expect((await (await regeneration).json()).streams).toEqual(flowsheet.streams);
  await calculate();
  await page
    .locator('[aria-labelledby="pfd-section-title"]')
    .screenshot({ path: '.local/milestone-4-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page
    .locator('[aria-labelledby="pfd-section-title"]')
    .screenshot({ path: '.local/milestone-4-mobile.png' });
});

test('Milestone 4 invalid split blocks PFD generation', async ({ page }) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 4 reference' }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const requirements = JSON.parse(await editor.inputValue());
  requirements.equipment.find(
    (e: { type: string }) => e.type === 'splitter',
  ).parameters.fractions.outlet_a = 0.8;
  await editor.fill(JSON.stringify(requirements));
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'fractions must sum to one',
  );
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});
