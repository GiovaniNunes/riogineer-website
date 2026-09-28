import { writeFile } from 'node:fs/promises';
import { test, expect } from '@playwright/test';

for (const reference of ['Load Milestone 4 reference', 'Restore reference']) {
  test(`${reference}: validation visibly succeeds before separate PFD generation`, async ({
    page,
  }) => {
    await page.goto('/digital-engineer');
    await page.getByText('Engineering data / Advanced', { exact: true }).click();
    await page.getByRole('button', { name: reference, exact: true }).click();
    const editor = page.getByLabel(
      'requirements.json — explicit units and development assumptions',
    );
    const original = JSON.parse(await editor.inputValue());
    const downstreamRequests: string[] = [];
    page.on('request', (request) => {
      if (/\/api\/digital-engineer\/(build-flowsheet|calculate)$/.test(request.url()))
        downstreamRequests.push(request.url());
    });
    const pending = page.waitForResponse('**/api/digital-engineer/validate-requirements');
    const validate = page.getByRole('button', { name: 'Validate requirements', exact: true });
    await validate.click();
    const response = await pending;
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Object.keys(body).sort()).toEqual(['requirements', 'validation']);
    expect(body.validation.status).toBe('valid');
    expect(body.requirements).toEqual(original);
    expect(JSON.parse(await editor.inputValue())).toEqual(original);
    await expect(page.getByRole('status')).toContainText('Requirements valid');
    await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeEnabled();
    const feedback = page.getByLabel('Requirements validation');
    await expect(feedback).toContainText('Requirements validated');
    await expect(feedback).toBeInViewport();
    await expect(validate).toBeDisabled();
    await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
    await expect(page.getByLabel('results.json', { exact: true })).toHaveText('null');
    await expect(page.getByRole('button', { name: 'Run engineering calculation' })).toBeDisabled();
    expect(downstreamRequests).toEqual([]);
    await feedback.getByRole('link', { name: 'Generate PFD', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeInViewport();
    expect(downstreamRequests).toEqual([]);
  });
}

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
    'Density',
    'Gas volumetric flow',
    'Oil volumetric flow',
    'Water volumetric flow',
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
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByLabel('Requirements validation')).toContainText('Requirements validated');
  const requirements = JSON.parse(await editor.inputValue());
  requirements.equipment.find(
    (e: { type: string }) => e.type === 'splitter',
  ).parameters.fractions.outlet_a = 0.8;
  await editor.fill(JSON.stringify(requirements));
  await expect(page.getByLabel('Requirements validation')).not.toContainText(
    'Requirements validated',
  );
  await expect(
    page.getByRole('button', { name: 'Validate requirements', exact: true }),
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'fractions must sum to one',
  );
  await expect(page.getByLabel('Requirements validation')).toContainText(
    'Requirements are not validated',
  );
  await expect(
    page.getByLabel('Requirements validation').getByRole('link', { name: 'Generate PFD' }),
  ).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});

test('completed Bia → Milestone 4 preserves active case at every boundary', async ({
  page,
}, testInfo) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const trace: Record<string, unknown> = {};
  async function operate(operation: string, button: string) {
    const pending = page.waitForResponse(`**/api/digital-engineer/${operation}`);
    await page.getByRole('button', { name: button, exact: true }).click();
    const response = await pending;
    expect(response.status()).toBe(200);
    const body = await response.json();
    trace[`${operation} request`] = response.request().postDataJSON();
    trace[`${operation} response`] = body;
    return body;
  }
  await operate('validate-requirements', 'Validate requirements');
  await operate('build-flowsheet', 'Generate PFD');
  await operate('calculate', 'Run engineering calculation');
  await expect(page.getByRole('status')).toContainText('Calculation complete');
  expect(
    JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText()).case_id,
  ).toBe('THREE_PHASE_SEPARATOR_DEV_001');
  await page.getByRole('button', { name: 'Load Milestone 4 reference' }).click();
  const requirements = JSON.parse(await editor.inputValue());
  trace['loaded requirements'] = requirements;
  expect(requirements.case_id).toBe('MILESTONE_4_BRANCH_MERGE');
  expect(requirements.profile).toBe('acyclic_development');
  expect(requirements.schema_version).toBe('1.1');
  async function snapshot(stage: string) {
    const flowsheet = JSON.parse(
      await page.getByLabel('flowsheet.json', { exact: true }).innerText(),
    );
    const results = JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText());
    trace[stage] = { requirements: JSON.parse(await editor.inputValue()), flowsheet, results };
    expect(JSON.parse(await editor.inputValue())).toEqual(requirements);
    return { flowsheet, results };
  }
  const loaded = await snapshot('after load');
  expect(loaded.flowsheet).toBeNull();
  expect.soft(loaded.results, 'switching cases must clear previous-case results').toBeNull();
  await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
  const validated = await operate('validate-requirements', 'Validate requirements');
  expect(trace['validate-requirements request']).toEqual(requirements);
  expect(validated.requirements).toEqual(requirements);
  await expect(page.getByLabel('Requirements validation')).toContainText('Requirements validated');
  const afterValidation = await snapshot('after validate');
  expect(afterValidation.flowsheet).toBeNull();
  expect.soft(afterValidation.results).toBeNull();
  const flowsheet = await operate('build-flowsheet', 'Generate PFD');
  expect(trace['build-flowsheet request']).toEqual(requirements);
  expect(flowsheet.case_id).toBe(requirements.case_id);
  expect(flowsheet.profile).toBe(requirements.profile);
  expect(flowsheet.schema_version).toBe('1.2');
  expect(flowsheet.equipment.map((e: { id: string }) => e.id).sort()).toEqual([
    'MIX_1',
    'SEP_1',
    'SPLIT_1',
  ]);
  expect(flowsheet.streams).toHaveLength(7);
  const built = await snapshot('after generate');
  expect(built.flowsheet).toEqual(flowsheet);
  expect.soft(built.results).toBeNull();
  for (const id of ['FEED', 'SEP_1', 'GAS_SINK', 'WATER_SINK', 'SPLIT_1', 'MIX_1', 'OIL_SINK'])
    await expect(page.locator(`svg [data-equipment-id="${id}"]`)).toBeVisible();
  const results = await operate('calculate', 'Run engineering calculation');
  expect(trace['calculate request']).toEqual(flowsheet);
  expect(results.case_id).toBe(requirements.case_id);
  expect(results.schema_version).toBe('1.5');
  expect(results.process_result_version).toBe('1.2');
  expect(results.requirements_sha256).toBe(flowsheet.requirements_sha256);
  expect(results.input_sha256).toBe(flowsheet.calculation.input_sha256);
  await expect(page.getByRole('status')).toContainText('Calculation complete');
  const calculated = await snapshot('after calculate');
  expect(calculated.results).toEqual(results);
  expect(calculated.flowsheet.streams).toEqual(flowsheet.streams);
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  await expect(table.locator('thead [data-stream-id]')).toHaveCount(7);
  for (const stream of flowsheet.streams) {
    const label = `${stream.engineering_number} — ${stream.service.toUpperCase()}`;
    await expect(table.locator(`thead [data-stream-id="${stream.id}"]`)).toHaveText(
      `${label}ID: ${stream.id}`,
    );
    await expect(page.locator(`svg g[data-stream-id="${stream.id}"] text`)).toHaveText(label);
  }
  await expect(
    table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: 'Total mass flow', exact: true }) })
      .getByRole('cell'),
  ).toHaveText(['kg/h', '110,000', '22,000', '77,550', '10,450', '46,530', '31,020', '77,550']);
  const tracePath = testInfo.outputPath('case-transition-trace.json');
  await writeFile(tracePath, JSON.stringify(trace, null, 2));
  await testInfo.attach('case-transition-trace', {
    path: tracePath,
    contentType: 'application/json',
  });
});
