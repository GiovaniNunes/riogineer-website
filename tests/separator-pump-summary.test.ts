import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import { resultsSchema } from '../src/lib/digital-engineer/contracts';
import { initialWorkflow } from '../src/lib/digital-engineer/workflow';
import { EngineerWorkspace } from '../src/app/digital-engineer/workspace';
import fixture from '../contracts/examples/milestone-20-reference-requirements.json';

// Seed the existing workspace with saved results; no server or thermodynamic rerun.
vi.mock('../src/lib/digital-engineer/workflow', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../src/lib/digital-engineer/workflow')>()),
  initialWorkflow: vi.fn(),
  resultsAreCurrent: () => true,
}));
const evidence = JSON.parse(
  readFileSync('benchmarks/m20_separator_pump/implementation.json', 'utf8'),
);
function render(caseId: string, zeroPtDuty = false) {
  const result = resultsSchema.parse(
    evidence.cases.find((row: { case_id: string }) => row.case_id === caseId).result,
  );
  if (result.schema_version !== '1.14') throw Error('Expected M20');
  if (zeroPtDuty) {
    // Presentation-only synthetic zero: mode, not numerical magnitude, owns the label.
    result.balances.energy.duty_W = 0;
    result.equipment.find((unit) => unit.type === 'equilibrium_separator_2phase')!.duty_W = 0;
  }
  vi.mocked(initialWorkflow).mockReturnValue({
    draft: JSON.stringify(fixture),
    revision: 0,
    validated: true,
    flowsheet: null,
    results: result,
    busy: false,
    error: null,
  });
  const html = renderToStaticMarkup(
    createElement(EngineerWorkspace, {
      referenceText: '',
      networkReferenceText: '',
      sequentialReferenceText: '',
      compressionReferenceText: '',
      equilibriumReferenceText: '',
    }),
  );
  const text = html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ');
  return {
    text,
    summary: text
      .split('Available energy balance')[1]
      .split('Qualified separator-to-pump integration')[0],
  };
}

describe('M20 rendered general energy summary', () => {
  it.each([
    ['PT_VL_HEATING_DP1000000.0', '1,832,535.619763', '1,585.583543', 'calculated'],
    ['PH_FLASH_DP1000000.0', '0', '8,068.185157', 'imposed zero'],
    ['PH_FLASH_DP0.0', '0', '0', 'imposed zero'],
  ])('%s distinguishes process heat and fluid power', (id, heat, power, specification) => {
    const { text, summary } = render(id);
    expect(summary).toContain(`Total process heat duty: ${heat} W (positive into the process).`);
    expect(summary).toContain(
      `Total power transferred to the fluid: ${power} W (positive into the process).`,
    );
    expect(summary).not.toContain('Imposed pump heat duty');
    expect(summary).not.toContain('electrical');
    expect(text).toContain(`Separator heat duty — ${specification}`);
    if (id === 'PH_FLASH_DP0.0') expect(text).toContain('Unavailable — equal-pressure identity');
  });
  it('labels PT duty as calculated even when its rendered value is zero', () => {
    const { text, summary } = render('PT_VL_HEATING_DP1000000.0', true);
    expect(summary).toContain('Total process heat duty: 0 W');
    expect(text).toContain('Separator heat duty — calculated');
    expect(text).not.toContain('Separator heat duty — imposed zero');
  });
});
