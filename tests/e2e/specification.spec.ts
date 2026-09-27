import { test, expect, type Page } from '@playwright/test';
import { createHmac } from 'node:crypto';
import { fixture } from '../interpretation-fixture';
import {
  naturalFixture,
  naturalSpecification,
  exclusionText,
} from '../natural-specification-fixture';
import { componentIdentifier } from '../../src/lib/digital-engineer/interpretation/components';
import { labels } from '../../src/lib/digital-engineer/interpretation/contracts';
import reference from '../../contracts/examples/requirements.json' with { type: 'json' };
import { draftSchema, type Draft } from '../../src/lib/digital-engineer/interpretation/contracts';
function envelope(input: Draft) {
  const draft = draftSchema.parse(input);
  return {
    draft,
    signature: createHmac('sha256', 'test-only-review-key')
      .update(JSON.stringify(draft))
      .digest('hex'),
  };
}
async function interpret(page: Page, draft = fixture().draft) {
  await page.route('**/api/digital-engineer/interpret-specification', (route) =>
    route.fulfill({ json: envelope(draft) }),
  );
  await page
    .getByLabel('Describe or paste your engineering specification')
    .fill(fixture().source.pages[0].text);
  await page.getByRole('button', { name: 'Interpret specification', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'WHAT RIOGINEER UNDERSTOOD' })).toBeVisible();
}
async function accept(page: Page) {
  const decisions = page.getByRole('combobox', { name: /Assumption \d+ decision/ });
  for (let i = 0; i < (await decisions.count()); i++)
    await decisions.nth(i).selectOption('accepted');
  await page.getByRole('checkbox', { name: /I approve use/ }).check();
  await page.getByRole('button', { name: 'Approve requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText(
    'Requirements valid. Ready to generate PFD.',
  );
}
async function calculate(page: Page) {
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  await expect(page.getByRole('img', { name: 'Three-phase separator PFD' })).toBeVisible();
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
}
test('specification → review → approval → real Python results, correction and stale handling', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/digital-engineer');
  await expect(
    page.getByLabel('requirements.json — explicit units and development assumptions'),
  ).not.toBeVisible();
  await interpret(page);
  await expect(
    page.getByRole('button', { name: 'Approve requirements', exact: true }),
  ).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
  await expect(page.locator('[data-results-status]')).toHaveCount(0);
  await accept(page);
  await calculate(page);
  const row = page.getByRole('row').filter({ hasText: 'Total mass flow (kg/h)' });
  for (const value of ['110,000', '22,000', '77,550', '10,450'])
    await expect(row).toContainText(value);
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await expect(page.getByRole('status')).toContainText('results current');
  await page.screenshot({ path: '.local/specification-desktop.png', fullPage: true });
  await page.getByRole('heading', { name: 'WHAT RIOGINEER UNDERSTOOD' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: '.local/specification-review-desktop.png' });
  await page.getByRole('spinbutton', { name: 'Separator temperature', exact: true }).fill('333.15');
  await expect(page.getByRole('heading', { name: 'Engineering results — STALE' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Approve requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('Requirements valid.');
  await calculate(page);
  await expect(page.getByText('1,465,444.444444 W', { exact: true })).toBeVisible();
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const approved = JSON.parse(
    await page
      .getByLabel('requirements.json — explicit units and development assumptions')
      .inputValue(),
  );
  const audit = JSON.parse(approved.provenance.source);
  expect(audit.review.corrections[0].value).toBe(333.15);
  expect(
    audit.interpretation.facts.find((f: { field: string }) => f.field === 'separator_temperature')
      .value,
  ).toBe(313.15);
  expect(errors).toEqual([]);
});
test('conflicts and missing data block approval in the engineering form', async ({ page }) => {
  await page.goto('/digital-engineer');
  const { draft } = fixture();
  const pressure = draft.facts.find((f) => f.field === 'separator_pressure')!;
  draft.facts.push({
    ...pressure,
    value: 1500000,
    evidence: {
      ...pressure.evidence,
      source_id: 'instructions',
      excerpt: 'Use separator pressure = 15 bar abs',
    },
  });
  draft.facts = draft.facts.filter((f) => f.field !== 'feed_temperature');
  await interpret(page, draft);
  await expect(
    page.getByText(
      'CONFLICT DETECTED: separator_pressure. Select or replace the value explicitly.',
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByText('Missing information: Feed temperature.', { exact: true }),
  ).toBeVisible();
  await page.getByRole('spinbutton', { name: 'Feed temperature', exact: true }).fill('313.15');
  await page.getByRole('spinbutton', { name: 'Separator pressure', exact: true }).fill('1500000');
  await page
    .getByLabel('Resolution note for Separator pressure', { exact: true })
    .fill('Use the additional user instruction.');
  await accept(page);
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeEnabled();
});
test('provider unavailable is reported clearly; mobile workspace does not overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/digital-engineer');
  await page
    .getByLabel('Describe or paste your engineering specification')
    .fill('Separate an offshore well fluid into gas, oil and water at 15 bar.');
  await page.getByRole('button', { name: 'Interpret specification', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Specification error' })).toHaveText(
    'Specification interpretation is not configured.',
  );
  await interpret(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '.local/specification-mobile.png', fullPage: true });
  await page
    .getByRole('spinbutton', { name: 'Separator pressure', exact: true })
    .scrollIntoViewIfNeeded();
  await page.screenshot({ path: '.local/specification-review-mobile.png' });
});
test('late interpretation cannot overwrite a revised source', async ({ page }) => {
  await page.goto('/digital-engineer');
  let release!: () => void, received!: () => void;
  const gate = new Promise<void>((r) => {
    release = r;
  });
  const arrived = new Promise<void>((r) => {
    received = r;
  });
  await page.route('**/api/digital-engineer/interpret-specification', async (route) => {
    received();
    await gate;
    await route.fulfill({ json: envelope(fixture().draft) });
  });
  await page.getByLabel('Describe or paste your engineering specification').fill('Original spec');
  await page.getByRole('button', { name: 'Interpret specification', exact: true }).click();
  await arrived;
  await page.getByLabel('Additional instructions (optional)').fill('Revised feed basis');
  const returned = page.waitForResponse('**/api/digital-engineer/interpret-specification');
  release();
  await returned;
  await expect(page.getByRole('heading', { name: 'WHAT RIOGINEER UNDERSTOOD' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});
test('late approval cannot authorize requirements after a correction', async ({ page }) => {
  await page.goto('/digital-engineer');
  await interpret(page);
  let release!: () => void, received!: () => void;
  const gate = new Promise<void>((r) => {
    release = r;
  });
  const arrived = new Promise<void>((r) => {
    received = r;
  });
  await page.route('**/api/digital-engineer/approve-requirements', async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    received();
    await gate;
    await route.fulfill({ response });
  });
  const decisions = page.getByRole('combobox', { name: /Assumption \d+ decision/ });
  for (let i = 0; i < (await decisions.count()); i++)
    await decisions.nth(i).selectOption('accepted');
  await page.getByRole('checkbox', { name: /I approve use/ }).check();
  await page.getByRole('button', { name: 'Approve requirements', exact: true }).click();
  await arrived;
  await page.getByRole('spinbutton', { name: 'Feed temperature', exact: true }).fill('320');
  const returned = page.waitForResponse('**/api/digital-engineer/approve-requirements');
  release();
  await returned;
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});

test('supported output variants normalize and missing numerical inputs use field highlights without note boxes', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  const { draft } = fixture();
  draft.facts.find((f) => f.field === 'outputs')!.value = 'gas,oil,water';
  draft.facts = draft.facts.filter((f) => !['feed_temperature', 'feed_pressure'].includes(f.field));
  for (const field of ['feed_temperature', 'feed_pressure'] as const)
    draft.issues.push({
      id: field,
      kind: 'missing',
      field,
      component: null,
      message: 'Required input not found in the source',
    });
  await interpret(page, draft);
  await expect(page.getByRole('combobox', { name: 'Requested outputs', exact: true })).toHaveValue(
    'gas, oil, water',
  );
  await expect(page.getByText('gas,oil,water — unsupported', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: /Resolution note/ })).toHaveCount(0);
  await expect(
    page.getByText('Required input not found in the source', { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText('Complete the required highlighted engineering inputs before approval.', {
      exact: true,
    }),
  ).toBeVisible();
  for (const field of ['Feed temperature', 'Feed pressure']) {
    await expect(page.getByRole('spinbutton', { name: field, exact: true })).toHaveAttribute(
      'aria-invalid',
      'true',
    );
    await expect(page.getByText(`Missing information: ${field}.`, { exact: true })).toHaveCount(1);
  }
  await expect(
    page.getByRole('button', { name: 'Approve requirements', exact: true }),
  ).toBeDisabled();
  await page.getByRole('spinbutton', { name: 'Feed temperature', exact: true }).fill('313.15');
  await page.getByRole('spinbutton', { name: 'Feed pressure', exact: true }).fill('2000000');
  await expect(
    page.getByRole('spinbutton', { name: 'Feed temperature', exact: true }),
  ).not.toHaveAttribute('aria-invalid', 'true');
  await accept(page);
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeEnabled();
});

test('unsupported outputs and explicit interpretation issues still block review', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  const { draft } = fixture();
  draft.facts.find((f) => f.field === 'outputs')!.value = 'gas, oil and water, solids';
  draft.issues.push({
    id: 'pressure-basis',
    kind: 'ambiguity',
    field: 'feed_pressure',
    component: null,
    message: 'Confirm absolute pressure basis.',
  });
  await interpret(page, draft);
  await expect(page.getByRole('textbox', { name: 'Resolution note', exact: true })).toHaveCount(1);
  await expect(
    page.getByText(
      'UNSUPPORTED CAPABILITY: supported products are gas, oil, water; available calculations are streams and mass/energy balances.',
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Approve requirements', exact: true }),
  ).toBeDisabled();
});

test('source equipment and topology wording normalizes locally without losing the audit', async ({
  page,
}) => {
  const { draft } = fixture();
  draft.facts.find((fact) => fact.field === 'equipment')!.value = 'three-phase separator';
  draft.facts.find((fact) => fact.field === 'topology')!.value =
    'one feed, one separator, gas, oil and water outlets';
  await page.goto('/digital-engineer');
  await interpret(page, draft);
  await expect(page.getByRole('combobox', { name: 'Equipment', exact: true })).toHaveValue(
    'three_phase_separator',
  );
  await expect(
    page.getByRole('combobox', { name: 'Process connections', exact: true }),
  ).toHaveValue('one_feed_one_separator_gas_oil_water');
  await accept(page);
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const requirements = JSON.parse(
    await page
      .getByLabel('requirements.json — explicit units and development assumptions')
      .inputValue(),
  );
  const audit = JSON.parse(requirements.provenance.source);
  expect(audit.interpretation.facts).toEqual(draft.facts);
  expect(
    audit.normalized_values.find((fact: { field: string }) => fact.field === 'equipment'),
  ).toMatchObject({
    value: 'three_phase_separator',
    original_value: 'three-phase separator',
    derivation: 'deterministic_text_normalization',
  });
});

test('natural component rows populate all 15 fields and exclusions require no manual data entry', async ({
  page,
}) => {
  const { draft } = naturalFixture();
  await page.goto('/digital-engineer');
  await page.route('**/api/digital-engineer/interpret-specification', (route) =>
    route.fulfill({ json: envelope(draft) }),
  );
  await page
    .getByLabel('Describe or paste your engineering specification')
    .fill(naturalSpecification);
  await page.getByRole('button', { name: 'Interpret specification', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'WHAT RIOGINEER UNDERSTOOD' })).toBeVisible();
  for (const fact of draft.facts.filter((f) => f.component)) {
    const name = `${componentIdentifier(fact.component!)} — ${labels[fact.field]}`;
    await expect(page.getByRole('spinbutton', { name, exact: true })).toHaveValue(
      String(fact.value),
    );
    await expect(page.getByRole('spinbutton', { name, exact: true })).not.toHaveAttribute(
      'aria-invalid',
      'true',
    );
  }
  await expect(page.getByText('Required — missing', { exact: true })).toHaveCount(0);
  await expect(page.getByText(/UNSUPPORTED CAPABILITY:/)).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Source scope exclusions' })).toBeVisible();
  for (const excerpt of exclusionText.split('\n'))
    await expect(page.getByText(excerpt, { exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: /Resolution note/ })).toHaveCount(0);
  await accept(page);
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const requirements = JSON.parse(
    await page
      .getByLabel('requirements.json — explicit units and development assumptions')
      .inputValue(),
  );
  expect(requirements.feeds[0].state).toEqual(reference.feeds[0].state);
  expect(requirements.equipment[0].parameters).toEqual(reference.equipment[0].parameters);
  const audit = JSON.parse(requirements.provenance.source);
  expect(audit.interpretation.facts).toEqual(draft.facts);
  expect(audit.review.corrections).toEqual([]);
});
