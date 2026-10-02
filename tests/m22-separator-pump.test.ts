import { createElement } from 'react';
import { it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
import { SeparatorPumpResults } from '../src/app/digital-engineer/separator-pump-results';
import below from '../contracts/examples/milestone-22-below-requirements.json';
import above from '../contracts/examples/milestone-22-above-requirements.json';
const evidence = JSON.parse(readFileSync('benchmarks/m22_separator_pump/integration.json', 'utf8'));
it('both M22 references and complete serialized calculations retain explicit pump selection', () => {
  for (const [j, fixture] of [below, above].entries()) {
    expect(engineeringRequirementsSchema.parse(fixture)).toEqual(fixture);
    const row = evidence.cases[j];
    expect(flowsheetSchema.parse(row.flowsheet)).toEqual(row.flowsheet);
    expect(resultsSchema.parse(row.result)).toEqual(row.result);
    const result = resultsSchema.parse(row.result);
    if (result.schema_version !== '1.15') throw Error('M22 version');
    const html = renderToStaticMarkup(createElement(SeparatorPumpResults, { results: result }));
    expect(html).toContain('PT200 — explicitly selected');
    expect(html).toContain('Separator calculation: historical settings');
    expect(html).toContain(j === 0 ? 'Below-boundary reference' : 'Above-boundary reference');
    expect(html).toContain('Separator heat duty — calculated');
    expect(html).toContain('Pump fluid power');
  }
});
it('missing, conflicting and historical selections reject in TypeScript contracts', () => {
  for (const change of ['missing', 'unknown', 'settings', 'old_model', 'old_schema', 'separator']) {
    const r = structuredClone(below);
    const pump = r.equipment[1];
    if (change === 'missing') delete pump.parameters.numerical_profile;
    if (change === 'unknown') pump.parameters.numerical_profile = 'pr_high_accuracy_pt400@1';
    if (change === 'settings')
      Object.assign(pump.parameters, { pt_settings: { flash_max_iterations: 100 } });
    if (change === 'old_model') pump.model.version = '1.0';
    if (change === 'old_schema') r.schema_version = '1.12';
    if (change === 'separator')
      Object.assign(r.equipment[0].parameters, { numerical_profile: 'pr_high_accuracy_pt200@1' });
    expect(engineeringRequirementsSchema.safeParse(r).success).toBe(false);
  }
});
it('profile edits invalidate current results and errors never restore successful display/export', () => {
  const row = evidence.cases[0];
  let state = initialWorkflow(JSON.stringify(below));
  state = workflowReducer(state, { type: 'validated', revision: state.revision });
  state = workflowReducer(state, {
    type: 'built',
    revision: state.revision,
    flowsheet: flowsheetSchema.parse(row.flowsheet),
  });
  state = workflowReducer(state, {
    type: 'calculated',
    revision: state.revision,
    results: resultsSchema.parse(row.result),
  });
  expect(resultsAreCurrent(state)).toBe(true);
  const changed = structuredClone(below);
  changed.equipment[1].parameters.numerical_profile = 'unknown';
  state = workflowReducer(state, { type: 'edit', draft: JSON.stringify(changed) });
  expect(resultsAreCurrent(state)).toBe(false);
  state = workflowReducer(state, {
    type: 'error',
    revision: state.revision,
    error: 'Unsupported profile',
  });
  expect(resultsAreCurrent(state)).toBe(false);
});
