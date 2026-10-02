import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { expect, it, vi } from 'vitest';
import { resultsSchema, type Results } from '../src/lib/digital-engineer/contracts';
import { formatEngineeringNumber } from '../src/lib/digital-engineer/number-format';
import { initialWorkflow } from '../src/lib/digital-engineer/workflow';
import { EngineerWorkspace } from '../src/app/digital-engineer/workspace';
import { SeparatorPumpResults } from '../src/app/digital-engineer/separator-pump-results';
vi.mock('../src/lib/digital-engineer/workflow', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../src/lib/digital-engineer/workflow')>()),
  initialWorkflow: vi.fn(),
  resultsAreCurrent: () => true,
}));
const evidence = JSON.parse(readFileSync('benchmarks/m22_separator_pump/integration.json', 'utf8'));
function result(index: number) {
  const r = resultsSchema.parse(evidence.cases[index].result);
  if (r.schema_version !== '1.15') throw Error('Expected M22');
  return r;
}
function render(r: Results) {
  vi.mocked(initialWorkflow).mockReturnValue({
    draft: '{}',
    revision: 0,
    validated: true,
    flowsheet: null,
    results: r,
    busy: false,
    error: null,
  });
  return renderToStaticMarkup(
    createElement(EngineerWorkspace, {
      referenceText: '',
      networkReferenceText: '',
      sequentialReferenceText: '',
      compressionReferenceText: '',
      equilibriumReferenceText: '',
    }),
  )
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ');
}
it('rounds only display zero and preserves resolved signs at each precision', () => {
  for (const precision of [6, 8]) {
    const small = 0.49 * 10 ** -precision;
    expect(formatEngineeringNumber(-small, precision)).toBe('0');
    expect(formatEngineeringNumber(small, precision)).toBe('0');
    expect(formatEngineeringNumber(-0, precision)).toBe('0');
    expect(formatEngineeringNumber(-1.1 * 10 ** -precision, precision)).toMatch(/^-0\.0*1$/);
    expect(formatEngineeringNumber(-12.5, precision)).toBe('-12.5');
  }
  expect(formatEngineeringNumber(-2.0256265997886658e-7)).toBe('0');
  expect(formatEngineeringNumber(-2.0256265997886658e-7, 8)).toBe('-0.0000002');
  expect(formatEngineeringNumber(null)).toBe('—');
});
it.each([0, 1])(
  'M22 %i renders verified evidence, calculated duty and neutral limitations without changing exports',
  (index) => {
    const r = result(index);
    const raw = JSON.stringify(r);
    const text = render(r);
    expect(text).toContain(
      index === 0
        ? 'Source saturation metadata: unknown (unspecified)'
        : 'Source saturation metadata: source_vle',
    );
    expect(text).toContain(
      index === 0
        ? 'Local phase evidence: Verified compressed liquid — lower-pressure witness'
        : 'Local phase evidence: Verified saturated source liquid — parent equilibrium coexistence',
    );
    expect(text).toContain('Total process heat duty: 0 W');
    expect(text).not.toContain('-0 W');
    expect(text).toContain('Separator heat duty — calculated');
    expect(text).not.toContain('Separator heat duty — imposed zero');
    if (index === 1) expect(text).toContain('-0.0000002');
    expect(text).toContain('This model qualifies material and fluid-energy integration only.');
    expect(text.split('Unavailable calculations')[1]).not.toContain('M20 qualifies material');
    expect(text).toContain('PT200 — explicitly selected');
    expect(text).toContain('Separator calculation: historical settings');
    expect(text).toContain('separator lineage retained');
    expect(JSON.stringify(r)).toBe(raw);
  },
);
it('missing or unaccepted local diagnostics cannot acquire a success label from names or saturation metadata', () => {
  for (const mutation of ['missing', 'unrecognized', 'unaccepted']) {
    const r = result(1);
    const pump = r.equipment.find((e) => e.type === 'pump')!;
    if (mutation === 'missing') delete pump.thermodynamics.diagnostics.inlet;
    else
      pump.thermodynamics.diagnostics.inlet = {
        status: mutation === 'unaccepted' ? 'rejected' : 'accepted',
        local: { status: mutation === 'unrecognized' ? 'unknown' : 'saturated_source_liquid' },
      };
    const text = renderToStaticMarkup(createElement(SeparatorPumpResults, { results: r }));
    expect(text).toContain('Not available in the recorded diagnostics');
    expect(text).not.toContain('Verified saturated');
    expect(text).not.toContain('Verified compressed');
  }
});
it('verified evidence follows the diagnostics even when display names change', () => {
  const r = result(0);
  const pump = r.equipment.find((e) => e.type === 'pump')!;
  pump.thermodynamics.qualification_id = 'RENAMED_ABOVE';
  const text = renderToStaticMarkup(createElement(SeparatorPumpResults, { results: r }));
  expect(text).toContain('Verified compressed liquid — lower-pressure witness');
  expect(text).not.toContain('Verified saturated');
});
it('historical M20 rendering retains its limitation text and calculated/imposed semantics', () => {
  const old = JSON.parse(readFileSync('benchmarks/m20_separator_pump/implementation.json', 'utf8'));
  const r = resultsSchema.parse(
    old.cases.find((c: { case_id: string }) => c.case_id === 'PH_FLASH_DP0.0').result,
  );
  const text = render(r);
  expect(text).toContain('M20 qualifies material and fluid-energy integration only.');
  expect(text).toContain('Separator heat duty — imposed zero');
  expect(text).toContain('Total process heat duty: 0 W');
});
