import { test, expect } from '@playwright/test';
import { resultsSchema } from '../../src/lib/digital-engineer/contracts';
import { readFileSync } from 'node:fs';
const references = JSON.parse(
  readFileSync('benchmarks/pt_iteration_budget/reference.json', 'utf8'),
);
for (const boundary of ['below', 'above']) {
  test(`M22 ${boundary} PT200 reference, tables/export, stale edits and rejection`, async ({
    page,
  }) => {
    test.setTimeout(120000);
    await page.goto('/digital-engineer');
    await page.getByText('Engineering data / Advanced', { exact: true }).click();
    await page
      .getByRole('button', {
        name: `Load Milestone 22 ${boundary}-boundary PT200 reference`,
        exact: true,
      })
      .click();
    await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
    await expect(page.getByRole('status')).toContainText('Requirements valid');
    await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Run engineering calculation', exact: true }),
    ).toBeEnabled();
    const response = page.waitForResponse('**/api/digital-engineer/calculate');
    await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
    const http = await response;
    expect(http.ok()).toBe(true);
    const result = resultsSchema.parse(await http.json());
    if (result.schema_version !== '1.15') throw Error('M22 result required');
    await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
    const panel = page.getByRole('region', { name: 'Separator-to-pump results' });
    await expect(panel).toContainText('PT200 — explicitly selected');
    await expect(panel).toContainText('Separator calculation: historical settings');
    await expect(panel).toContainText(
      boundary === 'below'
        ? 'Verified compressed liquid — lower-pressure witness'
        : 'Verified saturated source liquid — parent equilibrium coexistence',
    );
    await expect(panel).toContainText(
      boundary === 'below'
        ? 'Source saturation metadata: unknown (unspecified)'
        : 'Source saturation metadata: source_vle',
    );
    await expect(
      page.getByText('This model qualifies material and fluid-energy integration only.', {
        exact: false,
      }),
    ).toBeVisible();
    await expect(page.getByText('Total process heat duty:', { exact: false })).not.toContainText(
      '-0 W',
    );
    await expect(panel).toContainText('Separator heat duty — calculated');
    const pump = result.equipment.find((e) => e.type === 'pump')!;
    const ref = references.chains.find(
      (r: { source: string; P2: number }) =>
        r.source === `PT_BUBBLE_${boundary.toUpperCase()}` && r.P2 === 8e6,
    );
    expect(Math.abs(pump.work_W - ref.result.metrics.W_recovered_W)).toBeLessThan(0.0003);
    expect(
      Math.abs(result.streams.PUMP_PRODUCT.temperature_K - ref.result.states.outlet.T_K),
    ).toBeLessThan(1e-7);
    expect(pump.thermodynamics.numerical_profile).toBe('pr_high_accuracy_pt200@1');
    await expect(page.locator('[data-symbol="pump"]')).toBeAttached();
    for (const [id, number] of [
      ['HYDROCARBON_FEED', 1],
      ['LIQUID_PRODUCT', 2],
      ['VAPOR_PRODUCT', 3],
      ['PUMP_PRODUCT', 4],
    ]) {
      await expect(page.locator(`svg g[data-stream-id="${id}"] text`)).toHaveText(
        `${number} — ${id}`,
      );
    }
    const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
    await expect(table).toContainText('methane');
    await expect(table.locator('td[data-stream-id="PUMP_PRODUCT"]').first()).toBeVisible();
    const format = new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 });
    for (const [id, stream] of Object.entries(result.streams)) {
      const cells: [string, number | null][] = [
        ['Temperature', stream.temperature_K],
        ['Pressure', stream.pressure_Pa_abs],
        ['Total mass flow', stream.mass_flow_kg_h],
        ['Molar flow', stream.properties.molar_flow.value],
        ['Molecular mass', stream.properties.molecular_mass.value],
        ['Density', stream.properties.density.value],
        ['methane — component mass flow', stream.component_mass_flow_kg_h.methane],
        ['n_hexane — component mass flow', stream.component_mass_flow_kg_h.n_hexane],
        ['methane — molar fraction', stream.properties.molar_composition.value?.methane ?? null],
      ];
      for (const [label, value] of cells) {
        const row = table
          .getByRole('row')
          .filter({ has: page.getByRole('rowheader', { name: label, exact: true }) });
        await expect(row.locator(`td[data-stream-id="${id}"]`)).toHaveText(
          value === null ? '—' : format.format(value),
        );
      }
    }
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download results', exact: true }).click();
    const stream = await (await download).createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
    expect(JSON.parse(Buffer.concat(chunks).toString())).toEqual(result);
    await page.locator('#pfd-section').screenshot({ path: `.local/m22-${boundary}-pfd.png` });
    const draft = JSON.parse(await page.locator('#requirements').inputValue());
    if (boundary === 'below') draft.equipment[1].parameters.numerical_profile = 'unknown';
    else draft.equipment[1].parameters.isentropic_efficiency = 0.81;
    await page.locator('#requirements').fill(JSON.stringify(draft));
    await expect(
      page.getByRole('button', { name: 'Download results', exact: true }),
    ).toBeDisabled();
    await expect(panel).toHaveCount(0);
    await expect(page.getByText('Engineering results — STALE', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
    await expect(page.getByRole('alert', { name: 'Engineering error' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
    await expect(panel).toHaveCount(0);
  });
}
