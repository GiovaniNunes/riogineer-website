import { execFileSync } from 'node:child_process';
import { expect, it } from 'vitest';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
  exchangerDetailsSchema,
} from '../src/lib/digital-engineer/contracts';
import { results as oldResult } from './compression-fixture';
import { workflowReducer, resultsAreCurrent } from '../src/lib/digital-engineer/workflow';
const fixture = JSON.parse(
  execFileSync(
    'engine/.venv/bin/python',
    ['-B', 'engine/tests/test_two_stream_heat_exchanger_topology.py', '--fixture'],
    { env: { ...process.env, PYTHONPATH: 'engine' }, encoding: 'utf8' },
  ),
);
const input = fixture.requirements,
  flowsheet = fixture.flowsheet;
const clone = <T>(x: T): T => structuredClone(x);
const phase = {
  composition: { methane: 0.9, n_hexane: 0.1 },
  Z: 1,
  h_ig_J_mol: 1,
  h_res_J_mol: 0,
  h_J_mol: 1,
  s_ig_J_mol_K: 1,
  s_res_J_mol_K: 0,
  s_J_mol_K: 1,
};
const state = {
  temperature_K: 300,
  pressure_Pa_abs: 100000,
  z: phase.composition,
  classification: 'single_vapor',
  beta: 1,
  H_eq_J_mol: 1,
  S_eq_J_mol_K: 1,
  phases: { vapor: phase },
  pt_status: 'success_single_phase',
  max_log_fugacity_residual: 0,
};
const details = {
  property_package: 'peng_robinson@1.0',
  component_dataset: 'riogineer_components@1.0',
  molecular_provider: 'molecular_composition@1.0',
  caloric_dataset: 'riogineer_caloric@1.0',
  caloric_reference: 'ideal_gas_sensible_298.15K_101325Pa@1.0',
  bip: input.equipment[0].parameters.bip,
  specification_mode: 'specified_hot_outlet_temperature',
  hot_molar_flow_mol_s: 100,
  cold_molar_flow_mol_s: 200,
  hot_inlet: state,
  hot_outlet: state,
  cold_inlet: state,
  cold_outlet: state,
  Q_hot_W: -100,
  Q_cold_W: 100,
  Q_exchanged_W: 100,
  energy_residual_W: 0,
  energy_allowance_W: 1e-6,
  recovered_outlet_target_enthalpy_J_mol: 1,
  ph: {
    status: 'success',
    capability: 'flash_PH',
    pt_profile: 'high_accuracy',
    candidate_count: 1,
    bracket_K: [300, 310],
    final_bracket_K: [305, 305],
    root_iterations: 30,
    evaluation_count: 100,
    enthalpy_residual_J_mol: 0,
  },
};
const sideBalances = { hot: oldResult.balances.mass, cold: oldResult.balances.mass };
const stream = clone(Object.values(oldResult.streams)[0]);
Reflect.deleteProperty(stream, 'property_provenance');
Reflect.deleteProperty(stream.properties, 'component_molar_flow');
const result = {
  ...oldResult,
  streams: Object.fromEntries(
    ['HOT_IN', 'HOT_OUT', 'COLD_IN', 'COLD_OUT'].map((id) => [id, clone(stream)]),
  ),
  schema_version: '1.9',
  process_result_version: '1.9',
  engine: { ...oldResult.engine, version: '1.8.0' },
  requirements_sha256: flowsheet.requirements_sha256,
  input_sha256: flowsheet.calculation.input_sha256,
  equipment: [
    {
      id: 'HX',
      type: 'two_stream_heat_exchanger',
      model: input.equipment[0].model,
      duty_W: 0,
      work_W: 0,
      material_streams: {
        hot_in: 'HOT_IN',
        hot_out: 'HOT_OUT',
        cold_in: 'COLD_IN',
        cold_out: 'COLD_OUT',
      },
      material_balances: sideBalances,
      energy_residual_W: 0,
      thermodynamics: details,
    },
  ],
  balances: {
    material_paths: { HX: sideBalances },
    energy: {
      status: 'passed',
      residual_W: 0,
      tolerance_W: 1e-6,
      duty_W: 0,
      model: 'rigorous_two_stream_pr',
      positive_duty: 'heat_into_each_material_path',
    },
  },
};
Reflect.deleteProperty(result, 'model_tolerances');
it('round trips explicit requirements, four ports and an atomic four-state result', () => {
  expect(engineeringRequirementsSchema.parse(input)).toEqual(input);
  expect(flowsheetSchema.parse(flowsheet)).toEqual(flowsheet);
  expect(resultsSchema.parse(result)).toEqual(result);
});
it('accepts both exclusive modes and rejects under/over specification', () => {
  const b = clone(input);
  delete b.equipment[0].parameters.hot_outlet_temperature_K;
  b.equipment[0].parameters.mode = 'specified_cold_outlet_temperature';
  b.equipment[0].parameters.cold_outlet_temperature_K = 320;
  expect(engineeringRequirementsSchema.safeParse(b).success).toBe(true);
  for (const change of [
    (p: typeof input) => delete p.equipment[0].parameters.mode,
    (p: typeof input) => delete p.equipment[0].parameters.hot_outlet_temperature_K,
    (p: typeof input) => (p.equipment[0].parameters.cold_outlet_temperature_K = 320),
  ]) {
    const v = clone(input);
    change(v);
    expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
  }
});
it('rejects unsupported model and property provenance', () => {
  for (const patch of [
    { property_package: 'unknown' },
    { bip: { ...details.bip, source: '' } },
    {
      bip: {
        ...details.bip,
        values: [
          [0, 0.1],
          [0.1, 0],
        ],
      },
    },
    { bip: { ...details.bip, component_ids: ['methane', 'water'] } },
  ]) {
    const v = clone(input);
    Object.assign(v.equipment[0].parameters, patch);
    expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
  }
  const v = clone(input);
  v.equipment[0].model.id = 'equilibrium_energy_balance_pr';
  expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
});
for (const role of ['hot_in', 'cold_in', 'hot_out', 'cold_out'])
  it(`requires distinct ${role}`, () => {
    const f = clone(flowsheet);
    f.equipment[0].ports = f.equipment[0].ports.filter((p: { id: string }) => p.id !== role);
    expect(flowsheetSchema.safeParse(f).success).toBe(false);
  });
it('rejects duplicate port roles', () => {
  const f = clone(flowsheet);
  f.equipment[0].ports[2] = f.equipment[0].ports[0];
  expect(flowsheetSchema.safeParse(f).success).toBe(false);
});
for (const key of ['hot_outlet', 'cold_outlet', 'ph'])
  it(`requires ${key} for success`, () => {
    const d = clone(details);
    Reflect.deleteProperty(d, key);
    expect(exchangerDetailsSchema.safeParse(d).success).toBe(false);
    const r = clone(result);
    Reflect.deleteProperty(r.equipment[0].thermodynamics, key);
    expect(resultsSchema.safeParse(r).success).toBe(false);
  });
it('invalidates the complete outlet pair on either inlet or specification edit', () => {
  const accepted = resultsSchema.parse(result),
    f = flowsheetSchema.parse(flowsheet);
  const current = {
    draft: JSON.stringify(input),
    revision: 0,
    validated: true,
    flowsheet: { ...f, calculation: { ...f.calculation, status: 'current' as const } },
    results: accepted,
    busy: false,
    error: null,
  };
  expect(resultsAreCurrent(current)).toBe(true);
  for (const change of [
    (v: typeof input) => (v.feeds[0].state.temperature_K = 440),
    (v: typeof input) => (v.feeds[1].state.temperature_K = 310),
    (v: typeof input) => (v.equipment[0].parameters.hot_outlet_temperature_K = 380),
  ]) {
    const v = clone(input);
    change(v);
    expect(
      resultsAreCurrent(workflowReducer(current, { type: 'edit', draft: JSON.stringify(v) })),
    ).toBe(false);
  }
});
