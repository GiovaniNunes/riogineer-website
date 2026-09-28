import { expect, test, type Page } from '@playwright/test';
async function run(page: Page) {
  for (const [op, name] of [
    ['validate-requirements', 'Validate requirements'],
    ['build-flowsheet', 'Generate PFD'],
    ['calculate', 'Run engineering calculation'],
  ]) {
    const pending = page.waitForResponse(`**/api/digital-engineer/${op}`);
    await page.getByRole('button', { name, exact: true }).click();
    expect((await pending).status()).toBe(200);
  }
  await expect(page.getByRole('status')).toContainText('Calculation complete');
}
test('compression reference: runtime P/T, process versus shaft work, nine stable streams', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 6 reference' }).click();
  await run(page);
  const f = JSON.parse(await page.getByLabel('flowsheet.json', { exact: true }).innerText());
  const r = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
  expect(f.case_id).toBe('MILESTONE_6_GAS_COMPRESSION');
  expect(r.case_id).toBe(f.case_id);
  expect(r.input_sha256).toBe(f.calculation.input_sha256);
  expect(r.requirements_sha256).toBe(f.requirements_sha256);
  expect(r.execution.equipment_order).toEqual(['SEP_1', 'COMPRESSOR_1', 'HEATER_1', 'SEP_2']);
  for (const id of [
    'FEED',
    'SEP_1',
    'COMPRESSOR_1',
    'COMPRESSED_GAS_SINK',
    'WATER_1_SINK',
    'HEATER_1',
    'SEP_2',
    'GAS_2_SINK',
    'OIL_PRODUCT_SINK',
    'WATER_2_SINK',
  ])
    await expect(page.locator(`svg [data-equipment-id="${id}"]`)).toBeVisible();
  await expect(page.locator('svg [data-symbol="compressor"]')).toBeVisible();
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  async function identity() {
    await expect(table.locator('thead [data-stream-id]')).toHaveCount(9);
    await expect(page.locator('svg g[data-stream-id]')).toHaveCount(9);
    for (const s of f.streams) {
      const label = `${s.engineering_number} — ${s.service.toUpperCase()}`;
      await expect(table.locator(`thead [data-stream-id="${s.id}"]`)).toHaveText(
        `${label}ID: ${s.id}`,
      );
      await expect(page.locator(`svg g[data-stream-id="${s.id}"] text`)).toHaveText(label);
    }
  }
  await identity();
  const t2s = 313.15 * Math.pow(3, (1.3 - 1) / 1.3),
    t2 = 313.15 + (t2s - 313.15) / 0.75;
  const gas = (22000 / 3600) * 2200 * (t2 - 313.15),
    shaft = gas / 0.98;
  const fmt = (v: number, n = 8) =>
    new Intl.NumberFormat('en-US', { maximumFractionDigits: n }).format(v);
  const expected: Record<string, number[]> = {
    FEED: [22000, 77000, 11000, 313.15],
    GAS_1: [22000, 0, 0, 313.15],
    OIL_1: [0, 77000, 550, 313.15],
    WATER_1: [0, 0, 10450, 313.15],
    HEATED_OIL: [0, 77000, 550, 333.15],
    GAS_2: [0, 3850, 0, 333.15],
    OIL_PRODUCT: [0, 73150, 55, 333.15],
    WATER_2: [0, 0, 495, 333.15],
    COMPRESSED_GAS: [22000, 0, 0, t2],
  };
  for (const [id, [methane, hexane, water, temp]] of Object.entries(expected)) {
    const total = methane + hexane + water;
    const entries: [string, number][] = [
      ['Total mass flow', total],
      ['Temperature', temp],
      ['Pressure', id === 'COMPRESSED_GAS' ? 6000000 : 2000000],
    ];
    for (const [c, v] of [
      ['methane', methane],
      ['n_hexane', hexane],
      ['water', water],
    ] as const)
      entries.push([`${c} — component mass flow`, v], [`${c} — mass fraction`, v / total]);
    for (const [name, value] of entries)
      await expect(
        table
          .getByRole('row')
          .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
          .locator(`td[data-stream-id="${id}"]`),
      ).toHaveText(fmt(value));
  }
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
    ).toHaveText(Array(9).fill('—'));
  const details = page.getByRole('table', { name: 'COMPRESSOR_1 compression values' });
  for (const [name, value] of [
    ['Inlet pressure (Pa absolute)', 2000000],
    ['Discharge pressure (Pa absolute)', 6000000],
    ['Pressure ratio (dimensionless)', 3],
    ['Inlet temperature (K)', 313.15],
    ['Isentropic discharge temperature (K)', t2s],
    ['Actual discharge temperature (K)', t2],
    ['Cp (J/(kg K))', 2200],
    ['k = Cp/Cv (dimensionless)', 1.3],
    ['Isentropic efficiency (dimensionless)', 0.75],
    ['Gas/process power W_gas (W)', gas],
    ['Mechanical efficiency (dimensionless)', 0.98],
    ['Shaft power W_shaft (W)', shaft],
    ['Mechanical loss (W)', shaft - gas],
    ['Heat duty (W)', 0],
    ['Total mass residual (kg/h)', 0],
    ['Energy residual (W)', 0],
    ['methane residual (kg/h)', 0],
    ['n_hexane residual (kg/h)', 0],
    ['water residual (kg/h)', 0],
  ] as const)
    await expect(
      details
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .getByRole('cell'),
    ).toHaveText(fmt(value, 6));
  const energy = page.getByRole('region', { name: 'Compression and network work' });
  await expect(energy).toContainText('mechanical losses outside this boundary');
  for (const value of [gas, shaft, 953883.333333333, gas + 953883.333333333])
    await expect(energy).toContainText(fmt(value, 6));
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await identity();
  expect(JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText())).toEqual(r);
  const pending = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  expect((await (await pending).json()).streams).toEqual(f.streams);
  await page.getByRole('button', { name: 'Run engineering calculation' }).click();
  await expect(page.getByRole('status')).toContainText('Calculation complete');
  await identity();
  await page.locator('#pfd-section').screenshot({ path: '.local/milestone-6-pfd.png' });
  await energy.screenshot({ path: '.local/milestone-6-energy.png' });
});
test('all earlier cases ↔ Milestone 6 clear validation and downstream artifacts', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await run(page);
  for (const name of [
    'Load Milestone 6 reference',
    'Load Milestone 4 reference',
    'Load Milestone 6 reference',
    'Load Milestone 5 reference',
    'Load Milestone 6 reference',
    'Restore reference',
  ]) {
    await page.getByRole('button', { name, exact: true }).click();
    await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
    await expect(page.getByLabel('results.json', { exact: true })).toHaveText('null');
    await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
    await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
    await run(page);
    const req = JSON.parse(
      await page
        .getByLabel('requirements.json — explicit units and development assumptions')
        .inputValue(),
    );
    const f = JSON.parse(await page.getByLabel('flowsheet.json', { exact: true }).innerText());
    const r = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
    expect(f.case_id).toBe(req.case_id);
    expect(r.case_id).toBe(req.case_id);
    expect(r.input_sha256).toBe(f.calculation.input_sha256);
    expect(r.requirements_sha256).toBe(f.requirements_sha256);
  }
});
