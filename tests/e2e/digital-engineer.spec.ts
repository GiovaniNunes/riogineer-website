import { test, expect, type Page } from '@playwright/test';

async function build(page: Page) {
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('status')).toContainText(
    'Requirements valid. Ready to generate PFD.',
  );
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  await expect(page.getByRole('img', { name: 'Three-phase separator PFD' })).toBeVisible();
}
async function run(page: Page) {
  await build(page);
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
}
test('reference → contracts → PFD → Python results; edits stale and layout preserves', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
  await run(page);
  const row = page.getByRole('row').filter({ hasText: 'Total mass flow (kg/h)' });
  for (const value of ['110,000', '22,000', '77,550', '10,450'])
    await expect(row).toContainText(value);
  await expect(
    page.getByText('Rigorous three-phase equilibrium: not calculated.', { exact: false }),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download results', exact: true }).click();
  expect((await downloadPromise).suggestedFilename()).toBe('results.json');
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  await page.screenshot({ path: '.local/digital-engineer-desktop.png', fullPage: true });
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const r = JSON.parse(await editor.inputValue());
  r.equipment[0].parameters.separator.temperature_K = 333.15;
  await editor.fill(JSON.stringify(r, null, 2));
  await expect(page.getByRole('heading', { name: 'Engineering results — STALE' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download results', exact: true })).toBeDisabled();
  await run(page);
  await expect(page.getByText('1,465,444.444444 W', { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});
test('invalid recoveries stop PFD generation and identify the issue', async ({ page }) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const r = JSON.parse(await editor.inputValue());
  r.equipment[0].parameters.recovery_fractions.water.water = 1;
  await editor.fill(JSON.stringify(r));
  await page.getByRole('button', { name: 'Validate requirements', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'must sum to one',
  );
  await expect(page.getByRole('button', { name: 'Generate PFD', exact: true })).toBeDisabled();
});
test('a late calculation response cannot overwrite an edited model', async ({ page }) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await build(page);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let received!: () => void;
  const arrived = new Promise<void>((resolve) => {
    received = resolve;
  });
  await page.route('**/api/digital-engineer/calculate', async (route) => {
    const response = await route.fetch();
    received();
    await gate;
    await route.fulfill({ response });
  });
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await arrived;
  const editor = page.getByLabel('requirements.json — explicit units and development assumptions');
  const r = JSON.parse(await editor.inputValue());
  r.feeds[0].state.temperature_K = 320;
  await editor.fill(JSON.stringify(r));
  const returned = page.waitForResponse('**/api/digital-engineer/calculate');
  release();
  await returned;
  await expect(page.getByRole('status')).toHaveText('Requirements await validation.');
  await expect(page.locator('[data-results-status="current"]')).toHaveCount(0);
});
test('mobile workspace and engine-unavailable feedback', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await run(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.screenshot({ path: '.local/digital-engineer-mobile.png', fullPage: true });
  await page.route('**/api/digital-engineer/calculate', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        error: {
          code: 'ENGINE_UNAVAILABLE',
          message: 'Start the local Python engine.',
          issues: [],
        },
      }),
    }),
  );
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Engineering error' })).toContainText(
    'Start the local Python engine.',
  );
  await expect(page.getByRole('heading', { name: 'Engineering results — STALE' })).toBeVisible();
});

test('numbered PFD and stream table share identity, preserve downloads and distinguish zero', async ({
  page,
}) => {
  await page.goto('/digital-engineer');
  await page.getByText('Engineering data / Advanced', { exact: true }).click();
  await build(page);
  const table = page.getByRole('table', { name: 'Engineering Stream Table', exact: true });
  await expect(table).toBeVisible();
  const ids = ['FEED', 'GAS', 'OIL', 'WATER'];
  async function expectIdentity() {
    for (const [index, id] of ids.entries()) {
      const label = `${index + 1} — ${id}`;
      await expect(page.locator(`svg g[data-stream-id="${id}"] text`)).toHaveText(label);
      await expect(table.locator(`thead [data-stream-id="${id}"]`)).toHaveText(`${label}ID: ${id}`);
    }
  }
  await expectIdentity();
  await expect(
    table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: 'Total mass flow', exact: true }) })
      .getByRole('cell'),
  ).toHaveText(['kg/h', '—', '—', '—', '—']);
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  await expect(
    table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: 'Total mass flow', exact: true }) })
      .getByRole('cell'),
  ).toHaveText(['kg/h', '110,000', '22,000', '77,550', '10,450']);
  await expect(
    table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: 'Density', exact: true }) })
      .getByRole('cell'),
  ).toHaveText(['kg/m3', '—', '—', '—', '—']);
  await expect(
    table
      .getByRole('row')
      .filter({
        has: page.getByRole('rowheader', { name: 'water — component mass flow', exact: true }),
      })
      .locator('[data-stream-id="GAS"]'),
  ).toHaveText('0');
  await expect(
    table
      .getByRole('row')
      .filter({ has: page.getByRole('rowheader', { name: 'water — mass fraction', exact: true }) })
      .getByRole('cell')
      .first(),
  ).toHaveText('kg/kg');
  await expectIdentity();
  for (const [property, unit, value] of [
    ['Pressure', 'Pa absolute', '2,000,000'],
    ['Temperature', 'K', '313.15'],
  ]) {
    await expect(
      table
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader', { name: property, exact: true }) })
        .getByRole('cell'),
    ).toHaveText([unit, value, value, value, value]);
  }
  const before = await table.innerText();
  await page.getByRole('button', { name: 'Change display layout' }).click();
  await expect(table).toHaveText(before, { useInnerText: true });
  await expectIdentity();
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  await expectIdentity();
  const regenerated = page.waitForResponse('**/api/digital-engineer/build-flowsheet');
  await page.getByRole('button', { name: 'Generate PFD', exact: true }).click();
  expect((await regenerated).ok()).toBe(true);
  await expectIdentity();
  await page.getByRole('button', { name: 'Run engineering calculation', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('Calculation complete — results current.');
  await expectIdentity();
  const pendingDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download flowsheet', exact: true }).click();
  const download = await pendingDownload;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(Buffer.from(chunk));
  const flowsheet = JSON.parse(Buffer.concat(chunks).toString());
  expect(flowsheet.schema_version).toBe('1.1');
  expect(
    flowsheet.streams.map((s: { id: string; engineering_number: number }) => [
      s.id,
      s.engineering_number,
    ]),
  ).toEqual(ids.map((id, i) => [id, i + 1]));
  await page
    .locator('[aria-labelledby="pfd-section-title"]')
    .screenshot({ path: '.local/streams-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .locator('[aria-labelledby="pfd-section-title"]')
    .screenshot({ path: '.local/streams-mobile.png' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
});
