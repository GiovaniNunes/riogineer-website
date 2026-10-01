import { describe, it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import fixture from '../contracts/examples/milestone-18-pump-requirements.json';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
const execute = (identity = false) =>
  JSON.parse(
    execFileSync(
      'engine/.venv/bin/python',
      [
        '-B',
        '-c',
        `import json;from riogineer_engine.milestone18 import requirements;from riogineer_engine.core import build_flowsheet,calculate;f=build_flowsheet(requirements(${identity ? 'Pout=20e6' : ''}));print(json.dumps(dict(f=f,r=calculate(f))))`,
      ],
      { env: { ...process.env, PYTHONPATH: 'engine' }, encoding: 'utf8' },
    ),
  );
describe('M18 additive pump', () => {
  it('accepts fixture and rejects scalar/extra-field violations', () => {
    expect(engineeringRequirementsSchema.parse(fixture).schema_version).toBe('1.10');
    for (const parameters of [
      { ...fixture.equipment[0].parameters, isentropic_efficiency: 0.59 },
      { ...fixture.equipment[0].parameters, outlet_pressure_Pa_abs: 30e6 + 1 },
      { ...fixture.equipment[0].parameters, head_m: 1 },
    ]) {
      expect(
        engineeringRequirementsSchema.safeParse({
          ...fixture,
          equipment: [{ ...fixture.equipment[0], parameters }],
        }).success,
      ).toBe(false);
    }
  });
  it.each([false, true])(
    'validates actual adapter serialization and stale state (identity=%s)',
    (identity) => {
      const actual = execute(identity);
      const f = flowsheetSchema.parse(actual.f);
      const r = resultsSchema.parse(actual.r);
      expect(f.schema_version).toBe('1.11');
      expect(r.schema_version).toBe('1.12');
      if (r.schema_version !== '1.12') throw Error('Wrong version');
      const d = r.equipment[0].thermodynamics;
      expect(d.fluid_power_W).toBeCloseTo(identity ? 0 : 110622.8601133975, 5);
      expect(d.isentropic_outlet === null).toBe(identity);
      expect(r.streams.PUMP_PRODUCT.properties.molar_flow.value).toBe(360);
      let state = initialWorkflow(JSON.stringify(fixture));
      state = workflowReducer(state, { type: 'validated', revision: state.revision });
      state = workflowReducer(state, { type: 'built', revision: state.revision, flowsheet: f });
      state = workflowReducer(state, { type: 'calculated', revision: state.revision, results: r });
      expect(resultsAreCurrent(state)).toBe(true);
      state = workflowReducer(state, {
        type: 'edit',
        draft: JSON.stringify({ ...fixture, case_id: 'EDITED' }),
      });
      expect(resultsAreCurrent(state)).toBe(false);
      expect(state.validated).toBe(false);
    },
    20000,
  );
});
