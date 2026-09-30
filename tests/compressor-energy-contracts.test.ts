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
  rigorousCompressorInput,
  compressorDetailsSchema,
} from '../src/lib/digital-engineer/contracts';

const roundtrip = (x: unknown) => JSON.parse(JSON.stringify(x));
const model = { id: 'rigorous_isentropic_pr', version: '1.0' };
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
  outlet_pressure_Pa_abs: 300000,
  isentropic_efficiency: 0.8,
  property_package: 'peng_robinson@1.0',
  bip,
};
const unit = { id: 'COMPRESSOR', type: 'compressor', model, parameters };
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
  schema_version: '1.6',
  profile: 'compressor_energy',
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
  schema_version: '1.7',
  profile: 'compressor_energy',
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
  inlet: state,
  isentropic_outlet: state,
  actual_outlet: state,
  pressure_ratio: 3,
  isentropic_efficiency: 0.8,
  reconstructed_efficiency: 0.8,
  eta_power: 0.8,
  efficiency_allowance: 1e-8,
  H_out_target_J_mol: 2,
  delta_H_is_J_mol: 1,
  delta_H_actual_J_mol: 1.25,
  isentropic_fluid_power_W: 100,
  fluid_power_W: 125,
  power_identity_residual_W: 0,
  power_identity_allowance_W: 1e-6,
  delta_S_actual_J_mol_K: 1,
  energy_residual_W: 0,
  energy_allowance_W: 1e-6,
  ps: { ...inverse, capability: 'flash_PS', entropy_residual_J_mol_K: 0 },
  ph: { ...inverse, capability: 'flash_PH', enthalpy_residual_J_mol: 0 },
};
const result = roundtrip({
  ...oldResult,
  schema_version: '1.8',
  process_result_version: '1.8',
  engine: { ...oldResult.engine, version: '1.7.0' },
  streams: {},
  equipment: [
    {
      id: unit.id,
      type: 'compressor',
      model,
      duty_W: 0,
      work_W: 125,
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
      duty_W: 0,
      fluid_power_W: 125,
      model: 'rigorous_isentropic_pr',
      positive_work: 'work_into_process',
    },
  },
});
delete result.model_tolerances;

it('preserves all historical compressor serialization branches', () => {
  expect(engineeringRequirementsSchema.parse(roundtrip(oldInput))).toEqual(oldInput);
  expect(flowsheetSchema.parse(roundtrip(oldFlowsheet))).toEqual(oldFlowsheet);
  expect(resultsSchema.parse(roundtrip(oldResult))).toEqual(oldResult);
});
it('round trips rigorous requirements, flowsheet and structured result before equipment implementation', () => {
  expect(engineeringRequirementsSchema.parse(roundtrip(input))).toEqual(input);
  expect(flowsheetSchema.parse(roundtrip(flowsheet))).toEqual(flowsheet);
  expect(resultsSchema.parse(roundtrip(result))).toEqual(result);
  expect(compressorDetailsSchema.parse(roundtrip(details))).toEqual(details);
});
for (const key of ['outlet_pressure_Pa_abs', 'isentropic_efficiency', 'property_package', 'bip']) {
  it(`requires rigorous ${key}`, () => {
    const v = roundtrip(unit);
    delete v.parameters[key];
    expect(rigorousCompressorInput.safeParse(v).success).toBe(false);
  });
}
it('accepts eta=1 without Cp, gamma or mechanical efficiency', () => {
  expect(
    rigorousCompressorInput.safeParse({
      ...unit,
      parameters: { ...parameters, isentropic_efficiency: 1 },
    }).success,
  ).toBe(true);
});
it('rejects invalid efficiencies and pressures', () => {
  for (const eta of [0, -1, 1.01, NaN, Infinity, -Infinity])
    expect(
      rigorousCompressorInput.safeParse({
        ...unit,
        parameters: { ...parameters, isentropic_efficiency: eta },
      }).success,
    ).toBe(false);
  for (const pressure of [0, -1, NaN, Infinity])
    expect(
      rigorousCompressorInput.safeParse({
        ...unit,
        parameters: { ...parameters, outlet_pressure_Pa_abs: pressure },
      }).success,
    ).toBe(false);
});
it('rejects malformed or unqualified provenance', () => {
  for (const patch of [
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
    expect(
      rigorousCompressorInput.safeParse({ ...unit, parameters: { ...parameters, ...patch } })
        .success,
    ).toBe(false);
});
it('keeps historical required fields and separates model identities', () => {
  for (const key of ['cp_J_kg_K', 'heat_capacity_ratio', 'mechanical_efficiency']) {
    const v = roundtrip(oldInput);
    const c = v.equipment.find((e: { type: string }) => e.type === 'compressor');
    delete c.parameters[key];
    expect(engineeringRequirementsSchema.safeParse(v).success).toBe(false);
    expect(
      rigorousCompressorInput.safeParse({ ...unit, parameters: { ...parameters, [key]: 1 } })
        .success,
    ).toBe(false);
  }
  expect(
    rigorousCompressorInput.safeParse({
      ...unit,
      model: { id: 'ideal_gas_isentropic_efficiency', version: '1.0' },
    }).success,
  ).toBe(false);
  expect(rigorousCompressorInput.safeParse({ ...unit, model: { version: '1.0' } }).success).toBe(
    false,
  );
  const old = roundtrip(oldInput);
  old.equipment.find((e: { type: string }) => e.type === 'compressor').parameters.property_package =
    'peng_robinson@1.0';
  expect(engineeringRequirementsSchema.safeParse(old).success).toBe(false);
});
it('requires entropy, nested capability and structured isentropic state', () => {
  for (const mutate of [
    (v: typeof result) => delete v.equipment[0].thermodynamics.isentropic_outlet,
    (v: typeof result) => delete v.equipment[0].thermodynamics.inlet.S_eq_J_mol_K,
    (v: typeof result) => {
      v.equipment[0].thermodynamics.ps.capability = 'flash_PH';
    },
  ]) {
    const v = roundtrip(result);
    mutate(v);
    expect(resultsSchema.safeParse(v).success).toBe(false);
  }
  expect(resultsSchema.safeParse({ ...result, schema_version: '1.7' }).success).toBe(false);
});
