import { expect, it } from 'vitest';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { requirements as historicalInput, results as historicalOutput } from './sequential-fixture';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
  rigorousHeaterInput,
  rigorousHeaterModel,
  thermalDetailsSchema,
} from '../src/lib/digital-engineer/contracts';

const bip = {
  identifier: 'explicit_zero@1.0',
  component_ids: ['methane', 'n_hexane'],
  values: [
    [0, 0],
    [0, 0],
  ],
  source: 'Explicit qualified zero kij',
  model: 'peng_robinson@1.0',
};
const common = { property_package: 'peng_robinson@1.0', bip, outlet_pressure_Pa_abs: 1000 };
const model = { id: 'equilibrium_energy_balance_pr', version: '1.0' };
const unit = (parameters: object) => ({ id: 'HEATER_1', type: 'heater', model, parameters });
const a = unit({ ...common, mode: 'specified_outlet_temperature', outlet_temperature_K: 350 });
const b = unit({ ...common, mode: 'specified_heat_duty', duty_W: 0 });
const phase = {
  composition: { methane: 0.5, n_hexane: 0.5 },
  Z: 1,
  h_ig_J_mol: 0,
  h_res_J_mol: 0,
  h_J_mol: 0,
};
const state = {
  temperature_K: 300,
  pressure_Pa_abs: 1000,
  z: phase.composition,
  classification: 'single_vapor',
  beta: 1,
  H_eq_J_mol: 0,
  phases: { vapor: phase },
  pt_status: 'success_single_phase',
  max_log_fugacity_residual: 0,
};
const details = {
  mode: 'specified_heat_duty',
  property_package: 'peng_robinson@1.0',
  component_dataset: 'riogineer_components@1.0',
  molecular_provider: 'molecular_composition@1.0',
  caloric_dataset: 'riogineer_caloric@1.0',
  caloric_reference: 'ideal_gas_sensible_298.15K_101325Pa@1.0',
  bip,
  F_mol_s: 100,
  inlet: state,
  outlet: state,
  delta_H_J_mol: 0,
  Q_W: 0,
  energy_residual_W: 0,
  energy_allowance_W: 1e-4,
  H_out_target_J_mol: 0,
  ph: {
    status: 'success',
    capability: 'flash_PH',
    pt_profile: 'high_accuracy',
    root_iterations: 1,
    evaluation_count: 130,
    enthalpy_residual_J_mol: 0,
  },
};
const roundtrip = (v: unknown) => JSON.parse(JSON.stringify(v));

it('preserves historical heater input and output serialization', () => {
  expect(engineeringRequirementsSchema.parse(roundtrip(historicalInput))).toEqual(historicalInput);
  expect(resultsSchema.parse(roundtrip(historicalOutput))).toEqual(historicalOutput);
});
for (const [label, input] of [
  ['Mode A', a],
  ['Mode B zero duty', b],
] as const) {
  it(`accepts and preserves ${label}`, () =>
    expect(rigorousHeaterInput.parse(roundtrip(input))).toEqual(input));
}
it('rejects both specifications and neither specification', () => {
  expect(rigorousHeaterInput.safeParse(unit({ ...a.parameters, duty_W: 0 })).success).toBe(false);
  expect(
    rigorousHeaterInput.safeParse(unit({ ...common, mode: 'specified_heat_duty' })).success,
  ).toBe(false);
});
it('rejects invalid pressure, provider and BIP provenance', () => {
  for (const change of [
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
  ]) {
    expect(rigorousHeaterInput.safeParse(unit({ ...a.parameters, ...change })).success).toBe(false);
  }
});
it('preserves structured rigorous result and its explicit version', () => {
  expect(thermalDetailsSchema.parse(roundtrip(details))).toEqual(details);
  const r = {
    ...historicalOutput,
    schema_version: '1.7',
    process_result_version: '1.7',
    engine: { ...historicalOutput.engine, version: '1.6.0' },
    streams: {},
    equipment: [
      {
        id: 'HEATER_1',
        type: 'heater',
        model: rigorousHeaterModel.parse(model),
        duty_W: 0,
        work_W: 0,
        energy_residual_W: 0,
        mass_balance: historicalOutput.balances.mass,
        thermodynamics: details,
      },
    ],
    balances: {
      mass: historicalOutput.balances.mass,
      energy: {
        status: 'passed',
        residual_W: 0,
        tolerance_W: 1e-4,
        duty_W: 0,
        model: 'equilibrium_energy_balance_pr',
        positive_duty: 'heat_into_process',
      },
    },
  };
  const serial = roundtrip(r);
  delete serial.model_tolerances;
  expect(resultsSchema.parse(serial)).toEqual(serial);
  expect(resultsSchema.safeParse({ ...serial, schema_version: '1.5' }).success).toBe(false);
});
it('retains the unchanged M9 result reader', () => {
  const output = execFileSync(
    resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      'import json; from riogineer_engine.core import build_flowsheet, calculate; from riogineer_engine.milestone9 import requirements; print(json.dumps(calculate(build_flowsheet(requirements()))))',
    ],
    { cwd: resolve('engine'), encoding: 'utf8' },
  );
  const result = JSON.parse(output);
  expect(resultsSchema.parse(result)).toEqual(result);
});

it('round trips both versioned process inputs and flowsheets', () => {
  for (const input of [a, b]) {
    const connections = [
      {
        id: 'C1',
        stream_id: 'FEED',
        source: { owner_id: 'SOURCE', port_id: 'outlet' },
        target: { owner_id: 'HEATER_1', port_id: 'inlet' },
      },
      {
        id: 'C2',
        stream_id: 'PRODUCT',
        source: { owner_id: 'HEATER_1', port_id: 'outlet' },
        target: { owner_id: 'SINK', port_id: 'inlet' },
      },
    ];
    const feed = {
      temperature_K: 300,
      pressure_Pa_abs: 1000,
      component_mass_flow_kg_h: { methane: 1, n_hexane: 1 },
    };
    const r = {
      ...historicalInput,
      schema_version: '1.5',
      profile: 'heater_cooler_energy',
      provenance: { source: 'Contract serialization test', basis: 'qualified_equilibrium_energy' },
      components: ['methane', 'n_hexane'],
      feeds: [{ id: 'SOURCE', state: feed }],
      sinks: [{ id: 'SINK' }],
      equipment: [input],
      streams: [
        { id: 'FEED', service: 'feed' },
        { id: 'PRODUCT', service: 'product' },
      ],
      connections,
    };
    const clean = roundtrip(r);
    delete clean.caloric_model;
    expect(engineeringRequirementsSchema.parse(clean)).toEqual(clean);
    const f = {
      schema_version: '1.6',
      kind: 'flowsheet',
      case_id: 'M12',
      profile: r.profile,
      units: r.units,
      requirements_sha256: 'a'.repeat(64),
      components: r.components,
      boundaries: [
        {
          id: 'SOURCE',
          type: 'source',
          ports: [{ id: 'outlet', direction: 'out', kind: 'material' }],
        },
        { id: 'SINK', type: 'sink', ports: [{ id: 'inlet', direction: 'in', kind: 'material' }] },
      ],
      equipment: [
        {
          id: input.id,
          type: input.type,
          model: input.model,
          operating_parameters: input.parameters,
          ports: [
            { id: 'inlet', direction: 'in', kind: 'material' },
            { id: 'outlet', direction: 'out', kind: 'material' },
          ],
        },
      ],
      streams: r.streams.map((stream, i) => ({
        ...stream,
        engineering_number: i + 1,
        specified_state: i === 0 ? feed : null,
      })),
      connections,
      solver: { method: 'topological' },
      calculation: { status: 'not_run', input_sha256: null },
      validation: { status: 'valid', messages: [] },
      presentation: { layout: 'wide' },
    };
    expect(flowsheetSchema.parse(roundtrip(f))).toEqual(f);
  }
});
