import { expect, it } from 'vitest';
import {
  requirements as oldInput,
  flowsheet as oldFlowsheet,
  results as oldResult,
} from './compression-fixture';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
  valveDetailsSchema,
} from '../src/lib/digital-engineer/contracts';

const roundtrip = (x: unknown) => JSON.parse(JSON.stringify(x));
const model = { id: 'rigorous_isenthalpic_pr', version: '1.0' };
const bip = {
  identifier: 'm14_zero@1.0',
  component_ids: ['methane', 'n_hexane'],
  values: [
    [0, 0],
    [0, 0],
  ],
  source: 'Explicit zero',
  model: 'peng_robinson@1.0',
};
const parameters = {
  outlet_pressure_Pa_abs: 50000,
  property_package: 'peng_robinson@1.0',
  bip,
};
const unit = { id: 'COMPRESSOR', type: 'throttling_valve', model, parameters };
const feed = {
  temperature_K: 300,
  pressure_Pa_abs: 100000,
  component_mass_flow_kg_h: { methane: 1, n_hexane: 1 },
};
const connections = [
  {
    id: 'C1',
    stream_id: 'FEED',
    source: { owner_id: 'SOURCE', port_id: 'outlet' },
    target: { owner_id: 'COMPRESSOR', port_id: 'inlet' },
  },
  {
    id: 'C2',
    stream_id: 'PRODUCT',
    source: { owner_id: 'COMPRESSOR', port_id: 'outlet' },
    target: { owner_id: 'SINK', port_id: 'inlet' },
  },
];
const input = roundtrip({
  ...oldInput,
  schema_version: '1.8',
  profile: 'throttling_valve_energy',
  provenance: { source: 'Contract-only fixture', basis: 'qualified_equilibrium_energy' },
  components: ['methane', 'n_hexane'],
  feeds: [{ id: 'SOURCE', state: feed }],
  equipment: [unit],
  sinks: [{ id: 'SINK' }],
  streams: [
    { id: 'FEED', service: 'feed' },
    { id: 'PRODUCT', service: 'product' },
  ],
  connections,
});
delete input.caloric_model;
const ports = [
  { id: 'inlet', direction: 'in', kind: 'material' },
  { id: 'outlet', direction: 'out', kind: 'material' },
];
const flowsheet = roundtrip({
  ...oldFlowsheet,
  schema_version: '1.9',
  profile: 'throttling_valve_energy',
  components: input.components,
  boundaries: [
    { id: 'SOURCE', type: 'source', ports: [ports[1]] },
    { id: 'SINK', type: 'sink', ports: [ports[0]] },
  ],
  equipment: [{ id: unit.id, type: unit.type, model, operating_parameters: parameters, ports }],
  connections,
  streams: input.streams.map((s: object, i: number) => ({
    ...s,
    engineering_number: i + 1,
    specified_state: i === 0 ? feed : null,
  })),
});
delete flowsheet.caloric_model;
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
const inverse = {
  status: 'success',
  pt_profile: 'high_accuracy',
  candidate_count: 1,
  bracket_K: [300, 310],
  final_bracket_K: [305, 305],
  root_iterations: 30,
  evaluation_count: 100,
};
const details = {
  property_package: 'peng_robinson@1.0',
  component_dataset: 'riogineer_components@1.0',
  molecular_provider: 'molecular_composition@1.0',
  caloric_dataset: 'riogineer_caloric@1.0',
  caloric_reference: 'ideal_gas_sensible_298.15K_101325Pa@1.0',
  bip,
  F_mol_s: 100,
  inlet: { ...state, classification: 'single_liquid', beta: 0, phases: { liquid: phase } },
  outlet: {
    ...state,
    classification: 'vapor_liquid',
    beta: 0.5,
    pt_status: 'success_two_phase',
    phases: { liquid: phase, vapor: phase },
  },
  pressure_ratio: 0.5,
  pressure_drop_Pa: 50000,
  H_out_target_J_mol: 1,
  delta_H_J_mol: 0,
  delta_S_J_mol_K: 0,
  enthalpy_residual_J_mol: 0,
  energy_residual_W: 0,
  energy_allowance_W: 1e-6,
  ph: { ...inverse, capability: 'flash_PH', enthalpy_residual_J_mol: 0 },
};
const result = roundtrip({
  ...oldResult,
  schema_version: '1.10',
  process_result_version: '1.10',
  engine: { ...oldResult.engine, version: '1.9.0' },
  streams: {},
  equipment: [
    {
      id: unit.id,
      type: 'throttling_valve',
      model,
      material_streams: { inlet: 'FEED', outlet: 'PRODUCT' },
      mass_balance: oldResult.balances.mass,
      energy_residual_W: 0,
      thermodynamics: details,
    },
  ],
  balances: {
    mass: oldResult.balances.mass,
    energy: {
      status: 'passed',
      residual_W: 0,
      tolerance_W: 1e-6,
      model: 'rigorous_isenthalpic_pr',
    },
  },
});
delete result.model_tolerances;

it('preserves historical compressor documents without migration', () => {
  expect(engineeringRequirementsSchema.parse(oldInput)).toEqual(oldInput);
  expect(flowsheetSchema.parse(oldFlowsheet)).toEqual(oldFlowsheet);
  expect(resultsSchema.parse(oldResult)).toEqual(oldResult);
});
it('round trips requirements 1.8, flowsheet 1.9 and atomic VL results 1.10', () => {
  expect(engineeringRequirementsSchema.parse(input)).toEqual(input);
  expect(flowsheetSchema.parse(flowsheet)).toEqual(flowsheet);
  expect(resultsSchema.parse(result)).toEqual(result);
  expect(result.equipment[0].material_streams).toEqual({ inlet: 'FEED', outlet: 'PRODUCT' });
});
for (const key of ['outlet_pressure_Pa_abs', 'property_package', 'bip'])
  it(`requires specification ${key}`, () => {
    const v = roundtrip(input);
    delete v.equipment[0].parameters[key];
    expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
  });
for (const patch of [
  { outlet_temperature_K: 300 },
  { duty_W: 0 },
  { isentropic_efficiency: 1 },
  { Cv: 1 },
  { outlet_pressure_Pa_abs: 0 },
  { property_package: 'unknown' },
  { bip: { ...bip, source: '' } },
  {
    bip: {
      ...bip,
      values: [
        [0, 0.1],
        [0.1, 0],
      ],
    },
  },
  { bip: { ...bip, component_ids: ['methane', 'water'] } },
])
  it(`rejects unsupported specification ${JSON.stringify(patch)}`, () => {
    const v = roundtrip(input);
    Object.assign(v.equipment[0].parameters, patch);
    expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
  });
it('requires explicit valve model and version discrimination', () => {
  const v = roundtrip(input);
  v.equipment[0].model.id = 'rigorous_isentropic_pr';
  expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
  for (const version of ['1.6', '1.7'])
    expect(
      engineeringRequirementsSchema.safeParse({ ...input, schema_version: version }).success,
    ).toBe(false);
});
it('requires exactly one inlet and one outlet, with no phase outlets', () => {
  for (const ports of [
    [],
    [flowsheet.equipment[0].ports[0]],
    [...flowsheet.equipment[0].ports, { id: 'vapor', direction: 'out', kind: 'material' }],
    [flowsheet.equipment[0].ports[0], flowsheet.equipment[0].ports[0]],
  ]) {
    const f = roundtrip(flowsheet);
    f.equipment[0].ports = ports;
    expect(flowsheetSchema.safeParse(f).success).toBe(false);
  }
  const r = roundtrip(result);
  r.equipment[0].material_streams.vapor = 'VAPOR';
  expect(resultsSchema.safeParse(r).success).toBe(false);
});
for (const phaseName of ['liquid', 'vapor'])
  it(`accepts a single-${phaseName} outlet without the absent phase`, () => {
    const r = roundtrip(result);
    r.equipment[0].thermodynamics.outlet = {
      ...state,
      classification: `single_${phaseName}`,
      beta: phaseName === 'liquid' ? 0 : 1,
      phases: { [phaseName]: phase },
    };
    expect(resultsSchema.safeParse(r).success).toBe(true);
  });
for (const key of [
  'inlet',
  'outlet',
  'H_out_target_J_mol',
  'delta_H_J_mol',
  'delta_S_J_mol_K',
  'enthalpy_residual_J_mol',
  'energy_residual_W',
  'ph',
  'bip',
])
  it(`requires accepted-result ${key}`, () => {
    const r = roundtrip(result);
    delete r.equipment[0].thermodynamics[key];
    expect(resultsSchema.safeParse(r).success).toBe(false);
  });
it('rejects malformed VL phases, endpoint beta and failed PH', () => {
  for (const key of ['liquid', 'vapor']) {
    const r = roundtrip(result);
    delete r.equipment[0].thermodynamics.outlet.phases[key];
    expect(resultsSchema.safeParse(r).success).toBe(false);
  }
  for (const beta of [0, 1, -0.1, 1.1]) {
    const d = roundtrip(details);
    d.outlet.beta = beta;
    expect(valveDetailsSchema.safeParse(d).success).toBe(false);
  }
  for (const patch of [
    { status: 'failed' },
    { candidate_count: 2 },
    { pt_profile: 'standard' },
    { capability: 'flash_PS' },
  ]) {
    const r = roundtrip(result);
    Object.assign(r.equipment[0].thermodynamics.ph, patch);
    expect(resultsSchema.safeParse(r).success).toBe(false);
  }
});
it('rejects VL inlet service and valve power fields', () => {
  const d = roundtrip(details);
  d.inlet = d.outlet;
  expect(valveDetailsSchema.safeParse(d).success).toBe(false);
  for (const key of ['fluid_power_W', 'shaft_power_W', 'valve_power_W'])
    expect(valveDetailsSchema.safeParse({ ...details, [key]: 0 }).success).toBe(false);
});
