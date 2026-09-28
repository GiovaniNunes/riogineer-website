import { expect, test, type Page } from '@playwright/test';
import { resultsSchema } from '../../src/lib/digital-engineer/contracts';
async function run(page: Page) {
  for (const name of ['Validate requirements', 'Generate PFD', 'Run engineering calculation'])
    await page.getByRole('button', { name, exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Calculation complete');
}

test('M6 molecular enrichment displays every stream without changing its PFD identity', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await page.getByRole('button', { name: 'Load Milestone 6 reference' }).click();
  await run(page);
  const result = resultsSchema.parse(
    JSON.parse(await page.getByLabel('results.json', { exact: true }).innerText()),
  );
  if (result.schema_version !== '1.5') throw new Error('Expected molecular results');
  const f = JSON.parse(await page.getByLabel('flowsheet.json', { exact: true }).innerText());
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  for (const stream of f.streams) {
    const state = result.streams[stream.id],
      p = state.properties;
    await expect(table.locator(`thead [data-stream-id="${stream.id}"]`)).toContainText(
      `${stream.engineering_number} — ${stream.service.toUpperCase()}`,
    );
    await expect(page.locator(`svg g[data-stream-id="${stream.id}"] text`)).toHaveText(
      `${stream.engineering_number} — ${stream.service.toUpperCase()}`,
    );
    const values: [string, number | null][] = [
      ['Molar flow', p.molar_flow.value],
      ['Molecular mass', p.molecular_mass.value],
    ];
    for (const [c, v] of Object.entries(p.molar_composition.value!))
      values.push([`${c} — molar fraction`, v]);
    for (const [name, value] of values) {
      const cell = table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .locator(`td[data-stream-id="${stream.id}"]`);
      expect(value).not.toBeNull();
      expect(Number((await cell.innerText()).replaceAll(',', ''))).toBeCloseTo(value!, 7);
    }
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
          .locator(`td[data-stream-id="${stream.id}"]`),
      ).toHaveText('—');
  }
  await expect(
    page.getByText('Mass composition (kg/kg) remains authoritative.', { exact: false }),
  ).toBeVisible();
  await page.locator('#pfd-section').screenshot({ path: '.local/milestone-7-stream-table.png' });
});

test('a calculated zero-flow outlet shows zero molar flow and unavailable ratios', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const r = JSON.parse(await editor.inputValue());
  r.equipment[0].parameters.recovery_fractions.methane = { gas: 0, oil: 1, water: 0 };
  await editor.fill(JSON.stringify(r));
  await run(page);
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  for (const [name, value] of [
    ['Molar flow', '0'],
    ['Molecular mass', '—'],
    ['methane — molar fraction', '—'],
    ['Density', '—'],
  ])
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name, exact: true }) })
        .locator('td[data-stream-id="GAS"]'),
    ).toHaveText(value);
});
