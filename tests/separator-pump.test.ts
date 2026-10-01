import { it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import fixture from '../contracts/examples/milestone-20-reference-requirements.json';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
it('M20 all 30 runtime results round-trip through additive TypeScript contract', () => {
  const evidence = JSON.parse(
    readFileSync('benchmarks/m20_separator_pump/implementation.json', 'utf8'),
  );
  expect(evidence.cases).toHaveLength(30);
  for (const row of evidence.cases) expect(resultsSchema.parse(row.result)).toEqual(row.result);
});
it('M20 build identity, four streams and upstream changes invalidate exports', () => {
  engineeringRequirementsSchema.parse(fixture);
  const f = flowsheetSchema.parse(
    JSON.parse(
      execFileSync(
        'engine/.venv/bin/python',
        [
          '-B',
          '-c',
          'import json;from riogineer_engine.milestone20 import requirements;from riogineer_engine.core import build_flowsheet;print(json.dumps(build_flowsheet(requirements())))',
        ],
        { env: { ...process.env, PYTHONPATH: 'engine' }, encoding: 'utf8' },
      ),
    ),
  );
  expect(f.streams).toHaveLength(4);
  const evidence = JSON.parse(
    readFileSync('benchmarks/m20_separator_pump/implementation.json', 'utf8'),
  );
  const r = resultsSchema.parse(
    evidence.cases.find((c: { case_id: string }) => c.case_id === 'PH_FLASH_DP1000000.0').result,
  );
  let state = initialWorkflow(JSON.stringify(fixture));
  state = workflowReducer(state, { type: 'validated', revision: state.revision });
  state = workflowReducer(state, { type: 'built', revision: state.revision, flowsheet: f });
  state = workflowReducer(state, { type: 'calculated', revision: state.revision, results: r });
  expect(resultsAreCurrent(state)).toBe(true);
  const changed = structuredClone(fixture);
  changed.feeds[0].state.temperature_K += 1;
  state = workflowReducer(state, { type: 'edit', draft: JSON.stringify(changed) });
  expect(resultsAreCurrent(state)).toBe(false);
  expect(state.validated).toBe(false);
});
