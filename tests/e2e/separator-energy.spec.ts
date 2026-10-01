import { test, expect, type Page } from '@playwright/test';
import { flowsheetSchema, resultsSchema } from '../../src/lib/digital-engineer/contracts';
async function run(page: Page) {
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid');
  const build = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  const f = flowsheetSchema.parse(await (await build).json());
  const response = page.waitForResponse('**/api/digital-engineer/calculate');
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  const http = await response;
  expect(http.ok()).toBe(true);
  const r = resultsSchema.parse(await http.json());
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  return { f, r };
}
async function checkMolecularTable(page: Page, r: ReturnType<typeof resultsSchema.parse>) {
  if (r.schema_version !== '1.11') throw new Error('Expected M17 result');
  const table = page.getByRole('table', { name: 'Engineering Stream Table' });
  const unit = r.equipment[0];
  const d = unit.thermodynamics;
  const format = new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 });
  async function cell(label: string, id: string, value: number | null) {
    const row = table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: label, exact: true }) });
    await expect(row.locator(`td[data-stream-id="${id}"]`)).toHaveText(
      value === null ? '—' : format.format(value),
    );
  }
  for (const [port, id] of Object.entries(unit.material_streams)) {
    const stream = r.streams[id];
    const props = stream.properties;
    const flow =
      port === 'inlet' ? d.F_mol_s : d.phases[port as 'vapor' | 'liquid'].molar_flow_mol_s;
    expect(props.molar_flow.value).not.toBeNull();
    expect(props.molar_flow.value!).toBeCloseTo(flow * 3.6, 9);
    await cell('Molar flow', id, props.molar_flow.value);
    const mw = flow ? stream.mass_flow_kg_h / (flow * 3.6) : null;
    if (mw !== null) expect(props.molecular_mass.value!).toBeCloseTo(mw, 9);
    else expect(props.molecular_mass.value).toBeNull();
    await cell('Molecular mass', id, props.molecular_mass.value);
    const z = port === 'inlet' ? d.inlet.z : d.phases[port as 'vapor' | 'liquid'].composition;
    for (const component of ['methane', 'n_hexane']) {
      const value = props.molar_composition.value?.[component] ?? null;
      if (z) expect(value!).toBeCloseTo(z[component], 11);
      else expect(value).toBeNull();
      await cell(`${component} — molar fraction`, id, value);
    }
    await cell('Density', id, null);
  }
}
for (const mode of ['PT', 'adiabatic PH'])
  test(`M17 ${mode}: real engine, phase energy and stale invalidation`, async ({ page }) => {
    await page.goto('/digital-engineer');
    await page.getByText('Engineering data / Advanced', { exact: true }).click();
    await page
      .getByRole('button', { name: `Load Milestone 17 ${mode} reference`, exact: true })
      .click();
    const { f, r } = await run(page);
    expect(f.schema_version).toBe('1.10');
    expect(r.schema_version).toBe('1.11');
    expect(f.streams).toHaveLength(3);
    await checkMolecularTable(page, r);
    await expect(page.getByRole('img', { name: 'Multi-equipment PFD' })).toContainText(
      mode === 'PT' ? 'PT energy · 2 phase' : 'PH energy · 2 phase',
    );
    await expect(page.locator('[data-symbol="equilibrium-separator-2phase"]')).toBeAttached();
    const panel = page.getByRole('region', { name: 'Separator energy results' });
    await expect(panel).toContainText(mode === 'PT' ? 'Calculated heat duty' : 'Imposed zero duty');
    await expect(panel).toContainText('Mass balance: passed');
    if (mode !== 'PT') await expect(panel).toContainText('Calculated temperature');
    await expect(
      page.getByRole('table', { name: 'Separator phase energy and material outlets' }),
    ).toContainText('Enthalpy flow (W)');
    // Engineering edits invalidate both the dedicated panel and current stream results.
    const editor = page.locator('#requirements');
    const changed = JSON.parse(await editor.inputValue());
    changed.equipment[0].parameters.separator_pressure_Pa_abs = 40000000;
    await editor.fill(JSON.stringify(changed));
    await expect(panel).toHaveCount(0);
    await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
    await expect(page.getByRole('status')).toContainText('Requirements valid');
    await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
    const failed = page.waitForResponse('**/api/digital-engineer/calculate');
    await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
    expect((await failed).ok()).toBe(false);
    await expect(page.locator('#engineering-error')).toContainText('invalid_pressure');
    await expect(panel).toHaveCount(0);
  });

test('M17 equal pressure: absent vapor, populated molecular properties and edit invalidation', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page
    .getByRole('button', { name: 'Load Milestone 17 adiabatic PH reference', exact: true })
    .click();
  const editor = page.locator('#requirements');
  const input = JSON.parse(await editor.inputValue());
  input.equipment[0].parameters.separator_pressure_Pa_abs = 30000000;
  await editor.fill(JSON.stringify(input));
  const { r } = await run(page);
  if (r.schema_version !== '1.11') throw new Error('Expected M17 result');
  await checkMolecularTable(page, r);
  for (const id of ['HYDROCARBON_FEED', 'LIQUID_PRODUCT']) {
    expect(r.streams[id].properties.molar_flow.value).toBeCloseTo(360, 9);
    expect(r.streams[id].properties.molar_composition.value).toEqual({
      methane: 0.5,
      n_hexane: 0.5,
    });
  }
  const vapor = r.streams.VAPOR_PRODUCT;
  expect(vapor.mass_flow_kg_h).toBe(0);
  expect(vapor.enthalpy_flow_W).toBe(0);
  expect(vapor.properties.molar_flow.value).toBe(0);
  expect(vapor.properties.molecular_mass.value).toBeNull();
  expect(vapor.properties.molar_composition.value).toBeNull();
  input.equipment[0].parameters.separator_pressure_Pa_abs = 1000000;
  await editor.fill(JSON.stringify(input));
  await expect(page.getByRole('region', { name: 'Separator energy results' })).toHaveCount(0);
  await expect(page.getByRole('status')).toContainText('Previous results are stale');
  await expect(
    page.getByRole('heading', { name: 'results.json (not current)', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
  await expect(
    page.getByRole('button', { name: 'Run engineering calculation', exact: true }),
  ).toBeDisabled();
  await expect(page.getByLabel('flowsheet.json', { exact: true })).toHaveText('null');
});
