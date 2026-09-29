import { test, expect, type Page } from '@playwright/test';
async function calculate(page: Page) {
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid');
  const build = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  const f = await (await build).json();
  const result = page.waitForResponse('**/api/digital-engineer/calculate');
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  const response = await result;
  expect(response.ok()).toBe(true);
  const r = await response.json();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  await expect(
    page.getByRole('list', { name: 'Warnings and model limitations' }).getByRole('listitem'),
  ).toHaveText([
    ...new Set([...r.warnings.map((w: { message: string }) => w.message), ...r.limitations]),
  ]);
  return { f, r };
}
test('M9 real PT flash: PFD, table, phase result, identity and repeat/layout/regeneration', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 9 reference' }).click();
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid');
  await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
  const built = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  const f = await (await built).json();
  await expect(page.getByLabel('results.json', { exact: true })).toHaveText('null');
  expect(f.streams).toHaveLength(3);
  for (const id of ['HYDROCARBON_FEED', 'SEP_PR_1', 'VAPOR_PRODUCT_SINK', 'LIQUID_PRODUCT_SINK'])
    await expect(page.locator(`svg [data-equipment-id="${id}"]`)).toBeVisible();
  // A stroked horizontal SVG path has a zero-height geometry bounding box.
  await expect(page.locator('[data-symbol="equilibrium-separator-2phase"]')).toBeAttached();
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  for (const s of f.streams) {
    const label = `${s.engineering_number} — ${s.service}`;
    await expect(page.locator(`svg [data-stream-id="${s.id}"] text`)).toHaveText(label);
    await expect(table.locator(`thead [data-stream-id="${s.id}"]`)).toHaveText(
      `${label}ID: ${s.id}`,
    );
  }
  const pending = page.waitForResponse('**/api/digital-engineer/calculate');
  await page.getByRole('button', { name: 'Run engineering calculation' }).click();
  const response = await pending;
  expect(response.ok()).toBe(true);
  const r = await response.json();
  const energyWarning =
    'Isothermal/isobaric PT equilibrium does not calculate phase-change enthalpy, heat duty, shaft work or an energy balance.';
  // The source records remain intact; only the combined presentation removes duplicates.
  expect(r.warnings.some((w: { message: string }) => w.message === energyWarning)).toBe(true);
  expect(r.limitations).toContain(energyWarning);
  const warnings = page.getByRole('list', { name: 'Warnings and model limitations' });
  await expect(warnings.getByText(energyWarning, { exact: true })).toHaveCount(1);
  await expect(warnings.getByRole('listitem')).toHaveText([
    ...new Set([...r.warnings.map((w: { message: string }) => w.message), ...r.limitations]),
  ]);
  const panel = page.getByRole('region', { name: 'Separator thermodynamic results' });
  await expect(panel).toContainText('vapor_liquid');
  for (const text of [
    'peng_robinson@1.0',
    'success_two_phase',
    '0.534642510224',
    '534.642510224',
    '465.357489776',
    'Liquid x (mol/mol)',
    'Vapor y (mol/mol)',
  ])
    await expect(panel).toContainText(text);
  const ordered = [...f.streams].sort((a, b) => a.engineering_number - b.engineering_number);
  for (const id of f.components) {
    const cells = table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: `${id} — molar fraction`, exact: true }) })
      .getByRole('cell');
    for (let i = 0; i < ordered.length; i++) {
      const stream = r.streams[ordered[i].id];
      expect(Number((await cells.nth(i + 1).innerText()).replaceAll(',', ''))).toBeCloseTo(
        stream.properties.molar_composition.value[id],
        6,
      );
      if (ordered[i].id !== 'HYDROCARBON_FEED')
        expect(stream.properties.molar_composition.value[id]).toBeCloseTo(
          r.equipment[0].thermodynamics[ordered[i].id === 'VAPOR_PRODUCT' ? 'y' : 'x'][id],
          12,
        );
    }
  }
  for (const label of [
    'Density',
    'Gas volumetric flow',
    'Oil volumetric flow',
    'Water volumetric flow',
  ])
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name: label, exact: true }) })
        .getByRole('cell'),
    ).toHaveText([label === 'Density' ? 'kg/m3' : 'm3/h', '—', '—', '—']);
  await page
    .getByLabel('Read-only process flow diagram')
    .screenshot({ path: '.local/milestone-9-pfd.png' });
  await panel.screenshot({ path: '.local/milestone-9-thermodynamics.png' });
  let calls = 0;
  page.on('request', (req) => {
    if (req.url().endsWith('/calculate')) calls++;
  });
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await expect(panel).toContainText('0.534642510224');
  expect(calls).toBe(0);
  const repeat = page.waitForResponse('**/api/digital-engineer/calculate');
  await page.getByRole('button', { name: 'Run engineering calculation' }).click();
  const r2 = await (await repeat).json();
  expect(r2.streams).toEqual(r.streams);
  expect(r2.equipment).toEqual(r.equipment);
  expect(r2.input_sha256).toBe(r.input_sha256);
  await page.screenshot({ path: '.local/milestone-9-browser.png', fullPage: true });
  const regeneration = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  const f2 = await (await regeneration).json();
  expect(f2.streams).toEqual(f.streams);
  expect(f2.connections).toEqual(f.connections);
  await expect(panel).toHaveCount(0);
});
for (const earlier of [5, 6])
  test(`M${earlier} ↔ M9 clears all previous case results`, async ({ page }) => {
    await page.goto('/digital-engineer');
    await page.getByText('Engineering data / Advanced', { exact: true }).click();
    for (const milestone of [earlier, 9, earlier]) {
      await page.getByRole('button', { name: `Load Milestone ${milestone} reference` }).click();
      await expect(page.getByLabel('results.json', { exact: true })).toHaveText('null');
      await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
      await expect(
        page.getByRole('region', { name: 'Separator thermodynamic results' }),
      ).toHaveCount(0);
      const { r } = await calculate(page);
      expect(r.case_id).toBe(
        milestone === 9
          ? 'MILESTONE_9_PT_FLASH_SEPARATOR'
          : milestone === 6
            ? 'MILESTONE_6_GAS_COMPRESSION'
            : 'MILESTONE_5_SEQUENTIAL_PROCESS',
      );
      await expect(
        page.getByRole('region', { name: 'Separator thermodynamic results' }),
      ).toHaveCount(milestone === 9 ? 1 : 0);
    }
  });
