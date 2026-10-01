import { z } from 'zod';

// The JSON schemas consumed by Python are generated from these definitions.
const id = z.string().regex(/^[A-Za-z][A-Za-z0-9_-]{0,79}$/);
const num = z.number().finite();
const nonnegative = num.nonnegative();
const positive = num.positive();
const rates = z.record(id, nonnegative);
const fractionMap = z.record(id, num.min(0).max(1));
const hash = z.string().regex(/^[a-f0-9]{64}$/);
export const unitsSchema = z.strictObject({
  temperature: z.literal('K'),
  pressure: z.literal('Pa_abs'),
  component_mass_flow: z.literal('kg/h'),
  heat_capacity: z.literal('J/(kg K)'),
  duty: z.literal('W'),
  recovery: z.literal('mass_fraction'),
});
export const modelSchema = z.strictObject({
  id: z.literal('prescribed_component_recoveries'),
  version: z.literal('1.0'),
});
const feedSchema = z.strictObject({
  temperature_K: positive,
  pressure_Pa_abs: positive,
  component_mass_flow_kg_h: rates,
});
const parametersSchema = z.strictObject({
  separator: z.strictObject({
    temperature_K: positive,
    pressure_Pa_abs: positive,
    thermal_mode: z.literal('specified_temperature_calculate_duty'),
  }),
  recovery_fractions: z.record(
    id,
    z.strictObject({ gas: num.min(0).max(1), oil: num.min(0).max(1), water: num.min(0).max(1) }),
  ),
  caloric_model: z.strictObject({
    type: z.literal('constant_cp_no_pressure_or_phase_dependence'),
    reference_temperature_K: positive,
    cp_J_kg_K: z.record(id, positive),
  }),
});
export const messageSchema = z.strictObject({
  code: z.string(),
  path: z.string(),
  severity: z.enum(['error', 'warning']),
  message: z.string(),
});
const validationSchema = z.strictObject({
  status: z.literal('valid'),
  messages: z.array(messageSchema),
});
const portSchema = z.strictObject({
  id,
  direction: z.enum(['in', 'out']),
  kind: z.literal('material'),
});
const endpointSchema = z.strictObject({ owner_id: id, port_id: id });
export const requirementsSchema = z.strictObject({
  schema_version: z.literal('1.0'),
  kind: z.literal('requirements'),
  case_id: id,
  profile: z.literal('single_separator_development'),
  units: unitsSchema,
  provenance: z.strictObject({
    source: z.string().min(1),
    basis: z.literal('synthetic_development_assumptions'),
  }),
  components: z.array(id).min(1).max(50),
  feeds: z.array(z.strictObject({ id, state: feedSchema })).length(1),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('three_phase_separator'),
        model: modelSchema,
        parameters: parametersSchema,
      }),
    )
    .length(1),
  required_outputs: z.tuple([
    z.literal('streams'),
    z.literal('mass_balance'),
    z.literal('energy_balance'),
  ]),
});
const legacyFlowsheetSchema = z.strictObject({
  schema_version: z.literal('1.0'),
  kind: z.literal('flowsheet'),
  case_id: id,
  profile: z.literal('single_separator_development'),
  units: unitsSchema,
  requirements_sha256: hash,
  components: z.array(id).min(1).max(50),
  boundaries: z
    .array(
      z.strictObject({
        id,
        type: z.enum(['source', 'sink']),
        ports: z.array(portSchema).length(1),
      }),
    )
    .length(4),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('three_phase_separator'),
        model: modelSchema,
        ports: z.array(portSchema).length(4),
        operating_parameters: parametersSchema,
      }),
    )
    .length(1),
  streams: z
    .array(
      z.strictObject({
        id,
        service: z.enum(['feed', 'gas', 'oil', 'water']),
        specified_state: feedSchema.nullable(),
      }),
    )
    .length(4),
  connections: z
    .array(z.strictObject({ id, stream_id: id, source: endpointSchema, target: endpointSchema }))
    .length(4),
  solver: z.strictObject({ method: z.literal('single_pass') }),
  calculation: z.strictObject({
    status: z.enum(['not_run', 'current', 'stale', 'failed']),
    input_sha256: hash.nullable(),
  }),
  validation: validationSchema,
  presentation: z.strictObject({ layout: z.enum(['wide', 'compact']) }),
});
const splitterModel = z.strictObject({
  id: z.literal('proportional_split'),
  version: z.literal('1.0'),
});
const mixerModel = z.strictObject({
  id: z.literal('equal_condition_mix'),
  version: z.literal('1.0'),
});
const graphModel = z.strictObject({
  id: z.literal('acyclic_component_conservation'),
  version: z.literal('1.0'),
});
const graphEquipmentInput = z.discriminatedUnion('type', [
  requirementsSchema.shape.equipment.element,
  z.strictObject({
    id,
    type: z.literal('splitter'),
    model: splitterModel,
    parameters: z.strictObject({
      fractions: z.strictObject({ outlet_a: nonnegative, outlet_b: nonnegative }),
    }),
  }),
  z.strictObject({
    id,
    type: z.literal('mixer'),
    model: mixerModel,
    parameters: z.strictObject({}),
  }),
]);
const graphStreams = z
  .array(z.strictObject({ id, service: z.string().min(1).max(80) }))
  .min(1)
  .max(200);
const graphConnections = z.array(legacyFlowsheetSchema.shape.connections.element).min(1).max(200);
export const networkRequirementsSchema = requirementsSchema.extend({
  schema_version: z.literal('1.1'),
  profile: z.literal('acyclic_development'),
  feeds: z.array(requirementsSchema.shape.feeds.element).min(1).max(50),
  equipment: z.array(graphEquipmentInput).min(1).max(50),
  sinks: z.array(z.strictObject({ id })).min(1).max(100),
  streams: graphStreams,
  connections: graphConnections,
  caloric_model: parametersSchema.shape.caloric_model,
});
const heaterModel = z.strictObject({
  id: z.literal('specified_outlet_temperature_constant_cp'),
  version: z.literal('1.0'),
});
const heaterInput = z.strictObject({
  id,
  type: z.literal('heater'),
  model: heaterModel,
  parameters: z.strictObject({
    outlet_temperature_K: positive,
    caloric_model: parametersSchema.shape.caloric_model,
  }),
});
export const sequentialRequirementsSchema = networkRequirementsSchema.extend({
  schema_version: z.literal('1.2'),
  equipment: z
    .array(z.union([graphEquipmentInput, heaterInput]))
    .min(1)
    .max(50),
});
const compressorModel = z.strictObject({
  id: z.literal('ideal_gas_isentropic_efficiency'),
  version: z.literal('1.0'),
});
const efficiency = positive.max(1);
const compressorInput = z.strictObject({
  id,
  type: z.literal('compressor'),
  model: compressorModel,
  parameters: z.strictObject({
    discharge_pressure_Pa_abs: positive,
    cp_J_kg_K: positive,
    heat_capacity_ratio: num.gt(1),
    isentropic_efficiency: efficiency,
    mechanical_efficiency: efficiency,
    inlet_phase: z.literal('gas'),
  }),
});
export const compressionRequirementsSchema = sequentialRequirementsSchema.extend({
  schema_version: z.literal('1.3'),
  equipment: z
    .array(z.union([sequentialRequirementsSchema.shape.equipment.element, compressorInput]))
    .min(1)
    .max(50),
});
const equilibriumModel = z.strictObject({
  id: z.literal('pt_flash_separator'),
  version: z.literal('1.0'),
});
const bipSchema = z.strictObject({
  identifier: z.literal('m9_methane_nhexane_zero_kij@1.0'),
  component_ids: z.tuple([z.literal('methane'), z.literal('n_hexane')]),
  values: z.tuple([z.tuple([z.literal(0), z.literal(0)]), z.tuple([z.literal(0), z.literal(0)])]),
  source: z.string().min(1),
  model: z.literal('peng_robinson@1.0'),
});
const equilibriumInput = z.strictObject({
  id,
  type: z.literal('equilibrium_separator_2phase'),
  model: equilibriumModel,
  parameters: z.strictObject({ property_package: z.literal('peng_robinson@1.0'), bip: bipSchema }),
});
export const equilibriumRequirementsSchema = networkRequirementsSchema
  .omit({ caloric_model: true })
  .extend({
    schema_version: z.literal('1.4'),
    profile: z.literal('pt_flash_separator'),
    provenance: z.strictObject({
      source: z.string().min(1),
      basis: z.literal('qualified_pt_flash_reference'),
    }),
    components: z.array(z.enum(['methane', 'n_hexane'])).length(2),
    feeds: z.array(requirementsSchema.shape.feeds.element).length(1),
    equipment: z.array(equilibriumInput).length(1),
    sinks: z.array(z.strictObject({ id })).length(2),
    streams: graphStreams.length(3),
    connections: graphConnections.length(3),
    required_outputs: z.tuple([
      z.literal('streams'),
      z.literal('mass_balance'),
      z.literal('pt_flash'),
    ]),
  });
// M12 is a separate model/profile; historical constant-Cp documents retain their meaning.
export const rigorousHeaterModel = z.strictObject({
  id: z.literal('equilibrium_energy_balance_pr'),
  version: z.literal('1.0'),
});
const thermalBip = bipSchema.extend({ identifier: z.string().min(1) });
const thermalCommon = z.strictObject({
  property_package: z.literal('peng_robinson@1.0'),
  bip: thermalBip,
  outlet_pressure_Pa_abs: positive,
});
export const rigorousHeaterParameters = z.union([
  thermalCommon.extend({
    mode: z.literal('specified_outlet_temperature'),
    outlet_temperature_K: num.min(200).max(500),
  }),
  thermalCommon.extend({ mode: z.literal('specified_heat_duty'), duty_W: num }),
]);
export const rigorousHeaterInput = z.strictObject({
  id,
  type: z.literal('heater'),
  model: rigorousHeaterModel,
  parameters: rigorousHeaterParameters,
});
export const thermalRequirementsSchema = networkRequirementsSchema
  .omit({ caloric_model: true })
  .extend({
    schema_version: z.literal('1.5'),
    profile: z.literal('heater_cooler_energy'),
    provenance: z.strictObject({
      source: z.string().min(1),
      basis: z.literal('qualified_equilibrium_energy'),
    }),
    components: z.tuple([z.literal('methane'), z.literal('n_hexane')]),
    feeds: z.array(requirementsSchema.shape.feeds.element).length(1),
    equipment: z.array(rigorousHeaterInput).length(1),
    sinks: z.array(z.strictObject({ id })).length(1),
    streams: graphStreams.length(2),
    connections: graphConnections.length(2),
  });
// M14 is additive: historical compressor and M12 serialization stay unchanged.
export const rigorousCompressorModel = z.strictObject({
  id: z.literal('rigorous_isentropic_pr'),
  version: z.literal('1.0'),
});
export const rigorousCompressorInput = z.strictObject({
  id,
  type: z.literal('compressor'),
  model: rigorousCompressorModel,
  parameters: thermalCommon.extend({ isentropic_efficiency: efficiency }),
});
export const rigorousCompressionRequirementsSchema = thermalRequirementsSchema.extend({
  schema_version: z.literal('1.6'),
  profile: z.literal('compressor_energy'),
  equipment: z.array(rigorousCompressorInput).length(1),
});
// M15 adds two wall-separated material paths without changing historical branches.
export const exchangerModel = z.strictObject({
  id: z.literal('rigorous_two_stream_pr'),
  version: z.literal('1.0'),
});
const exchangerCommon = thermalCommon.omit({ outlet_pressure_Pa_abs: true }).extend({
  hot_outlet_pressure_Pa_abs: positive,
  cold_outlet_pressure_Pa_abs: positive,
});
export const exchangerParameters = z.discriminatedUnion('mode', [
  exchangerCommon.extend({
    mode: z.literal('specified_hot_outlet_temperature'),
    hot_outlet_temperature_K: num.min(200).max(500),
  }),
  exchangerCommon.extend({
    mode: z.literal('specified_cold_outlet_temperature'),
    cold_outlet_temperature_K: num.min(200).max(500),
  }),
]);
export const exchangerInput = z.strictObject({
  id,
  type: z.literal('two_stream_heat_exchanger'),
  model: exchangerModel,
  parameters: exchangerParameters,
});
export const exchangerRequirementsSchema = thermalRequirementsSchema.extend({
  schema_version: z.literal('1.7'),
  profile: z.literal('two_stream_heat_exchanger_energy'),
  feeds: z.array(requirementsSchema.shape.feeds.element).min(2).max(50),
  sinks: z.array(z.strictObject({ id })).min(2).max(100),
  equipment: z.array(exchangerInput).min(1).max(50),
  streams: graphStreams.min(4),
  connections: graphConnections.min(4),
});
const exchangerPorts = z.tuple([
  z.strictObject({
    id: z.literal('hot_in'),
    direction: z.literal('in'),
    kind: z.literal('material'),
  }),
  z.strictObject({
    id: z.literal('hot_out'),
    direction: z.literal('out'),
    kind: z.literal('material'),
  }),
  z.strictObject({
    id: z.literal('cold_in'),
    direction: z.literal('in'),
    kind: z.literal('material'),
  }),
  z.strictObject({
    id: z.literal('cold_out'),
    direction: z.literal('out'),
    kind: z.literal('material'),
  }),
]);
// M16 adds an explicitly isenthalpic one-stream valve; historical models stay unchanged.
export const rigorousValveModel = z.strictObject({
  id: z.literal('rigorous_isenthalpic_pr'),
  version: z.literal('1.0'),
});
export const rigorousValveInput = z.strictObject({
  id,
  type: z.literal('throttling_valve'),
  model: rigorousValveModel,
  parameters: thermalCommon,
});
export const valveRequirementsSchema = thermalRequirementsSchema.extend({
  schema_version: z.literal('1.8'),
  profile: z.literal('throttling_valve_energy'),
  equipment: z.array(rigorousValveInput).length(1),
});
// M17 is additive; M9 retains its PT-only and null-energy contract.
export const separatorEnergyModel = z.strictObject({
  id: z.literal('equilibrium_separator_energy_pr'),
  version: z.literal('1.0'),
});
const separatorCommon = z.strictObject({
  separator_pressure_Pa_abs: positive,
  property_package: z.literal('peng_robinson@1.0'),
  bip: bipSchema,
});
export const separatorEnergyParameters = z.discriminatedUnion('mode', [
  separatorCommon.extend({
    mode: z.literal('specified_temperature'),
    separator_temperature_K: num.min(200).max(500),
  }),
  separatorCommon.extend({ mode: z.literal('adiabatic') }),
]);
const separatorEnergyInput = z.strictObject({
  id,
  type: z.literal('equilibrium_separator_2phase'),
  model: separatorEnergyModel,
  parameters: separatorEnergyParameters,
});
export const separatorEnergyRequirementsSchema = equilibriumRequirementsSchema.extend({
  schema_version: z.literal('1.9'),
  profile: z.literal('separator_energy'),
  provenance: thermalRequirementsSchema.shape.provenance,
  components: thermalRequirementsSchema.shape.components,
  equipment: z.array(separatorEnergyInput).length(1),
  required_outputs: z.tuple([
    z.literal('streams'),
    z.literal('mass_balance'),
    z.literal('energy_balance'),
  ]),
});
// M18 guarded liquid service is a distinct, additive branch.
export const pumpModel = z.strictObject({
  id: z.literal('rigorous_isentropic_pump_pr'),
  version: z.literal('1.0'),
});
export const pumpInput = z.strictObject({
  id,
  type: z.literal('pump'),
  model: pumpModel,
  parameters: thermalCommon.extend({
    outlet_pressure_Pa_abs: num.min(20e6).max(30e6),
    isentropic_efficiency: num.min(0.6).max(1),
  }),
});
export const pumpRequirementsSchema = thermalRequirementsSchema.extend({
  schema_version: z.literal('1.10'),
  profile: z.literal('pump_energy'),
  equipment: z.array(pumpInput).length(1),
});
export const variablePumpModel = z.strictObject({
  id: z.literal('rigorous_isentropic_pump_pr'),
  version: z.literal('2.0'),
});
export const variablePumpInput = z.strictObject({
  id,
  type: z.literal('pump'),
  model: variablePumpModel,
  parameters: thermalCommon.extend({
    outlet_pressure_Pa_abs: num.min(20e6).max(30e6),
    isentropic_efficiency: num.min(0.6).max(1),
  }),
});
export const variablePumpRequirementsSchema = thermalRequirementsSchema.extend({
  schema_version: z.literal('1.11'),
  profile: z.literal('variable_pump_energy'),
  equipment: z.array(variablePumpInput).length(1),
});
export const separatorPumpModel = z.strictObject({
  id: z.literal('separator_liquid_pump_pr'),
  version: z.literal('1.0'),
});
const separatorPumpInput = z.strictObject({
  id,
  type: z.literal('pump'),
  model: separatorPumpModel,
  parameters: thermalCommon.extend({ isentropic_efficiency: num.min(0.6).max(1) }),
});
export const separatorPumpRequirementsSchema = separatorEnergyRequirementsSchema.extend({
  schema_version: z.literal('1.12'),
  profile: z.literal('separator_pump_energy'),
  equipment: z.array(z.union([separatorEnergyInput, separatorPumpInput])).length(2),
  streams: graphStreams.length(4),
  connections: graphConnections.length(4),
});
// Interpretation stays on requirementsSchema (1.0); deterministic API accepts both.
export const engineeringRequirementsSchema = z.union([
  requirementsSchema,
  networkRequirementsSchema,
  sequentialRequirementsSchema,
  compressionRequirementsSchema,
  equilibriumRequirementsSchema,
  thermalRequirementsSchema,
  rigorousCompressionRequirementsSchema,
  exchangerRequirementsSchema,
  valveRequirementsSchema,
  separatorEnergyRequirementsSchema,
  pumpRequirementsSchema,
  variablePumpRequirementsSchema,
  separatorPumpRequirementsSchema,
]);
const graphEquipment = z.discriminatedUnion('type', [
  graphEquipmentInput.options[0]
    .omit({ parameters: true })
    .extend({ ports: z.array(portSchema), operating_parameters: parametersSchema }),
  graphEquipmentInput.options[1].omit({ parameters: true }).extend({
    ports: z.array(portSchema),
    operating_parameters: graphEquipmentInput.options[1].shape.parameters,
  }),
  graphEquipmentInput.options[2].omit({ parameters: true }).extend({
    ports: z.array(portSchema),
    operating_parameters: graphEquipmentInput.options[2].shape.parameters,
  }),
]);
const numberedStream = legacyFlowsheetSchema.shape.streams.element.extend({
  service: z.string().min(1).max(80),
  engineering_number: z.number().int().positive().max(Number.MAX_SAFE_INTEGER),
});
const networkFlowsheetSchema = legacyFlowsheetSchema.extend({
  schema_version: z.literal('1.2'),
  profile: z.literal('acyclic_development'),
  boundaries: z.array(legacyFlowsheetSchema.shape.boundaries.element).min(2).max(150),
  equipment: z.array(graphEquipment).min(1).max(50),
  streams: z.array(numberedStream).min(1).max(200),
  connections: graphConnections,
  solver: z.strictObject({ method: z.literal('topological') }),
  caloric_model: parametersSchema.shape.caloric_model,
});
const sequentialFlowsheetSchema = networkFlowsheetSchema.extend({
  schema_version: z.literal('1.3'),
  equipment: z
    .array(
      z.union([
        graphEquipment,
        heaterInput.omit({ parameters: true }).extend({
          ports: z.array(portSchema),
          operating_parameters: heaterInput.shape.parameters,
        }),
      ]),
    )
    .min(1)
    .max(50),
});
const compressionFlowsheetSchema = sequentialFlowsheetSchema.extend({
  schema_version: z.literal('1.4'),
  equipment: z
    .array(
      z.union([
        sequentialFlowsheetSchema.shape.equipment.element,
        compressorInput.omit({ parameters: true }).extend({
          ports: z.array(portSchema),
          operating_parameters: compressorInput.shape.parameters,
        }),
      ]),
    )
    .min(1)
    .max(50),
});
const equilibriumFlowsheetSchema = networkFlowsheetSchema.omit({ caloric_model: true }).extend({
  schema_version: z.literal('1.5'),
  profile: z.literal('pt_flash_separator'),
  components: equilibriumRequirementsSchema.shape.components,
  boundaries: z.array(legacyFlowsheetSchema.shape.boundaries.element).length(3),
  equipment: z
    .array(
      equilibriumInput.omit({ parameters: true }).extend({
        ports: z.array(portSchema).length(3),
        operating_parameters: equilibriumInput.shape.parameters,
      }),
    )
    .length(1),
  streams: z.array(numberedStream).length(3),
  connections: graphConnections.length(3),
});
const thermalFlowsheetSchema = networkFlowsheetSchema.omit({ caloric_model: true }).extend({
  schema_version: z.literal('1.6'),
  profile: z.literal('heater_cooler_energy'),
  components: thermalRequirementsSchema.shape.components,
  boundaries: z.array(legacyFlowsheetSchema.shape.boundaries.element).length(2),
  equipment: z
    .array(
      rigorousHeaterInput.omit({ parameters: true }).extend({
        ports: z.array(portSchema).length(2),
        operating_parameters: rigorousHeaterParameters,
      }),
    )
    .length(1),
  streams: z.array(numberedStream).length(2),
  connections: graphConnections.length(2),
});
const rigorousCompressionFlowsheetSchema = thermalFlowsheetSchema.extend({
  schema_version: z.literal('1.7'),
  profile: z.literal('compressor_energy'),
  equipment: z
    .array(
      rigorousCompressorInput.omit({ parameters: true }).extend({
        ports: z.array(portSchema).length(2),
        operating_parameters: rigorousCompressorInput.shape.parameters,
      }),
    )
    .length(1),
});
export const exchangerFlowsheetSchema = thermalFlowsheetSchema.extend({
  schema_version: z.literal('1.8'),
  profile: z.literal('two_stream_heat_exchanger_energy'),
  boundaries: z.array(legacyFlowsheetSchema.shape.boundaries.element).min(4),
  equipment: z
    .array(
      exchangerInput
        .omit({ parameters: true })
        .extend({ ports: exchangerPorts, operating_parameters: exchangerParameters }),
    )
    .min(1)
    .max(50),
  streams: z.array(numberedStream).min(4).max(200),
  connections: graphConnections.min(4),
});
export const valveFlowsheetSchema = thermalFlowsheetSchema.extend({
  schema_version: z.literal('1.9'),
  profile: z.literal('throttling_valve_energy'),
  equipment: z
    .array(
      rigorousValveInput.omit({ parameters: true }).extend({
        ports: z.tuple([
          z.strictObject({
            id: z.literal('inlet'),
            direction: z.literal('in'),
            kind: z.literal('material'),
          }),
          z.strictObject({
            id: z.literal('outlet'),
            direction: z.literal('out'),
            kind: z.literal('material'),
          }),
        ]),
        operating_parameters: rigorousValveInput.shape.parameters,
      }),
    )
    .length(1),
});
export const separatorEnergyFlowsheetSchema = equilibriumFlowsheetSchema.extend({
  schema_version: z.literal('1.10'),
  profile: z.literal('separator_energy'),
  equipment: z
    .array(
      separatorEnergyInput.omit({ parameters: true }).extend({
        ports: z.tuple([
          z.strictObject({
            id: z.literal('inlet'),
            direction: z.literal('in'),
            kind: z.literal('material'),
          }),
          z.strictObject({
            id: z.literal('vapor'),
            direction: z.literal('out'),
            kind: z.literal('material'),
          }),
          z.strictObject({
            id: z.literal('liquid'),
            direction: z.literal('out'),
            kind: z.literal('material'),
          }),
        ]),
        operating_parameters: separatorEnergyParameters,
      }),
    )
    .length(1),
});
export const pumpFlowsheetSchema = thermalFlowsheetSchema.extend({
  schema_version: z.literal('1.11'),
  profile: z.literal('pump_energy'),
  equipment: z
    .array(
      pumpInput.omit({ parameters: true }).extend({
        ports: valveFlowsheetSchema.shape.equipment.element.shape.ports,
        operating_parameters: pumpInput.shape.parameters,
      }),
    )
    .length(1),
});
export const variablePumpFlowsheetSchema = thermalFlowsheetSchema.extend({
  schema_version: z.literal('1.12'),
  profile: z.literal('variable_pump_energy'),
  equipment: z
    .array(
      variablePumpInput.omit({ parameters: true }).extend({
        ports: valveFlowsheetSchema.shape.equipment.element.shape.ports,
        operating_parameters: variablePumpInput.shape.parameters,
      }),
    )
    .length(1),
});
export const separatorPumpFlowsheetSchema = separatorEnergyFlowsheetSchema.extend({
  schema_version: z.literal('1.13'),
  profile: z.literal('separator_pump_energy'),
  equipment: z
    .array(
      z.union([
        separatorEnergyFlowsheetSchema.shape.equipment.element,
        separatorPumpInput.omit({ parameters: true }).extend({
          ports: valveFlowsheetSchema.shape.equipment.element.shape.ports,
          operating_parameters: separatorPumpInput.shape.parameters,
        }),
      ]),
    )
    .length(2),
  streams: z.array(separatorEnergyFlowsheetSchema.shape.streams.element).length(4),
  connections: graphConnections.length(4),
});
// Legacy 1.0/1.1 readers remain unchanged; graph builds explicitly use 1.2.
export const flowsheetSchema = z.union([
  legacyFlowsheetSchema,
  networkFlowsheetSchema,
  sequentialFlowsheetSchema,
  compressionFlowsheetSchema,
  equilibriumFlowsheetSchema,
  thermalFlowsheetSchema,
  rigorousCompressionFlowsheetSchema,
  exchangerFlowsheetSchema,
  valveFlowsheetSchema,
  separatorEnergyFlowsheetSchema,
  pumpFlowsheetSchema,
  variablePumpFlowsheetSchema,
  separatorPumpFlowsheetSchema,
  legacyFlowsheetSchema.extend({
    schema_version: z.literal('1.1'),
    streams: z
      .array(
        legacyFlowsheetSchema.shape.streams.element.extend({
          engineering_number: z.number().int().positive().max(Number.MAX_SAFE_INTEGER),
        }),
      )
      .length(4),
  }),
]);

function property(unit: string) {
  return z.union([
    z.strictObject({ value: nonnegative, status: z.literal('calculated'), unit: z.literal(unit) }),
    z.strictObject({ value: z.null(), status: z.literal('not_calculated'), unit: z.literal(unit) }),
  ]);
}
export const streamPropertiesSchema = z.strictObject({
  molar_flow: property('kmol/h'),
  molecular_mass: property('kg/kmol'),
  density: property('kg/m3'),
  gas_volumetric_flow: property('m3/h'),
  oil_volumetric_flow: property('m3/h'),
  water_volumetric_flow: property('m3/h'),
  molar_composition: z.union([
    z.strictObject({
      value: fractionMap,
      status: z.literal('calculated'),
      unit: z.literal('mol/mol'),
    }),
    z.strictObject({
      value: z.null(),
      status: z.literal('not_calculated'),
      unit: z.literal('mol/mol'),
    }),
  ]),
});
const stateSchema = z.strictObject({
  component_mass_flow_kg_h: rates,
  mass_flow_kg_h: nonnegative,
  component_mass_fractions: fractionMap.nullable(),
  temperature_K: positive,
  pressure_Pa_abs: positive,
  enthalpy_flow_W: num,
});
const legacyResultsSchema = z.strictObject({
  schema_version: z.literal('1.0'),
  kind: z.literal('results'),
  case_id: id,
  run_id: z.string().min(1),
  input_sha256: hash,
  requirements_sha256: hash,
  engine: z.strictObject({
    version: z.literal('1.0.0'),
    implementation_sha256: hash,
    evaluator_sha256: hash,
    model: modelSchema,
  }),
  status: z.literal('completed'),
  units: unitsSchema,
  streams: z.record(id, stateSchema),
  equipment: z.array(z.strictObject({ id, model: modelSchema, separator_duty_W: num })).length(1),
  balances: z.strictObject({
    mass: z.strictObject({
      status: z.enum(['passed', 'failed']),
      component_residual_kg_h: z.record(id, num),
      total_residual_kg_h: num,
      component_tolerance_kg_h: positive,
      total_tolerance_kg_h: positive,
    }),
    energy: z.strictObject({
      status: z.enum(['passed', 'failed']),
      residual_W: num,
      tolerance_W: positive,
      duty_W: num,
      model: z.literal('constant_cp_no_pressure_or_phase_dependence'),
      reference_temperature_K: positive,
      positive_duty: z.literal('heat_into_separator'),
    }),
  }),
  warnings: z.array(messageSchema),
  limitations: z.array(z.string()).min(1),
  unavailable: z
    .array(
      z.strictObject({
        calculation: z.string(),
        status: z.literal('not calculated'),
        reason: z.string().min(1),
      }),
    )
    .min(1),
});
const networkResultsSchema = legacyResultsSchema.extend({
  schema_version: z.literal('1.2'),
  engine: legacyResultsSchema.shape.engine.extend({
    version: z.literal('1.1.0'),
    model: graphModel,
  }),
  streams: z.record(id, stateSchema.extend({ properties: streamPropertiesSchema })),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.enum(['three_phase_separator', 'splitter', 'mixer']),
        model: z.union([modelSchema, splitterModel, mixerModel]),
        duty_W: num,
        work_W: num,
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
      }),
    )
    .min(1)
    .max(50),
  balances: legacyResultsSchema.shape.balances.extend({
    energy: legacyResultsSchema.shape.balances.shape.energy.extend({
      positive_duty: z.literal('heat_into_network'),
    }),
  }),
  execution: z.strictObject({
    method: z.literal('topological'),
    equipment_order: z.array(id).min(1),
  }),
  model_tolerances: z.strictObject({
    split_fraction: positive,
    mixer_temperature_K: positive,
    mixer_pressure_Pa: positive,
  }),
});
const sequentialResultsSchema = networkResultsSchema.extend({
  schema_version: z.literal('1.3'),
  engine: networkResultsSchema.shape.engine.extend({ version: z.literal('1.2.0') }),
  equipment: z
    .array(
      networkResultsSchema.shape.equipment.element.extend({
        type: z.enum(['three_phase_separator', 'splitter', 'mixer', 'heater']),
        model: z.union([modelSchema, splitterModel, mixerModel, heaterModel]),
      }),
    )
    .min(1)
    .max(50),
});
const compressionDetails = z.strictObject({
  inlet_pressure_Pa_abs: positive,
  discharge_pressure_Pa_abs: positive,
  pressure_ratio: num.gt(1),
  inlet_temperature_K: positive,
  isentropic_discharge_temperature_K: positive,
  discharge_temperature_K: positive,
  cp_J_kg_K: positive,
  heat_capacity_ratio: num.gt(1),
  isentropic_efficiency: efficiency,
  mechanical_efficiency: efficiency,
  gas_power_W: nonnegative,
  shaft_power_W: nonnegative,
  mechanical_loss_W: nonnegative,
});
const compressionResultsSchema = sequentialResultsSchema.extend({
  schema_version: z.literal('1.4'),
  engine: sequentialResultsSchema.shape.engine.extend({ version: z.literal('1.3.0') }),
  equipment: z
    .array(
      z.union([
        sequentialResultsSchema.shape.equipment.element,
        sequentialResultsSchema.shape.equipment.element.extend({
          type: z.literal('compressor'),
          model: compressorModel,
          compression: compressionDetails,
        }),
      ]),
    )
    .min(1)
    .max(50),
  balances: sequentialResultsSchema.shape.balances.extend({
    energy: sequentialResultsSchema.shape.balances.shape.energy.extend({
      process_work_W: nonnegative,
      shaft_power_W: nonnegative,
      mechanical_loss_W: nonnegative,
      external_enthalpy_change_W: num,
      positive_work: z.literal('work_into_process'),
    }),
  }),
});
const molecularResultFields = {
  schema_version: z.literal('1.5'),
  streams: z.record(
    id,
    stateSchema.extend({
      properties: streamPropertiesSchema.extend({
        component_molar_flow: z.strictObject({
          value: rates,
          status: z.literal('calculated'),
          unit: z.literal('kmol/h'),
        }),
      }),
      property_provenance: z.strictObject({
        provider: z.literal('molecular_composition@1.0'),
        component_dataset: z.literal('riogineer_components@1.0'),
        molecular_weights_kg_kmol: z.record(id, positive),
        status: z.literal('completed'),
        input_basis: z.literal('component_mass_flow_kg_h'),
      }),
    }),
  ),
};
const molecularSingleResults = legacyResultsSchema.extend({
  ...molecularResultFields,
  process_result_version: z.literal('1.1'),
  engine: legacyResultsSchema.shape.engine.extend({ version: z.literal('1.4.0') }),
});
const molecularNetworkResults = networkResultsSchema.extend({
  ...molecularResultFields,
  process_result_version: z.literal('1.2'),
  engine: networkResultsSchema.shape.engine.extend({ version: z.literal('1.4.0') }),
});
const molecularSequentialResults = sequentialResultsSchema.extend({
  ...molecularResultFields,
  process_result_version: z.literal('1.3'),
  engine: sequentialResultsSchema.shape.engine.extend({ version: z.literal('1.4.0') }),
});
const molecularCompressionResults = compressionResultsSchema.extend({
  ...molecularResultFields,
  process_result_version: z.literal('1.4'),
  engine: compressionResultsSchema.shape.engine.extend({ version: z.literal('1.4.0') }),
});
const signedMap = z.record(id, num);
const unavailableEnergy = z.strictObject({
  status: z.literal('not_calculated'),
  reason: z.string().min(1),
  duty_W: z.null(),
  residual_W: z.null(),
});
const equilibriumDetails = z.strictObject({
  property_package: z.literal('peng_robinson@1.0'),
  component_dataset: z.literal('riogineer_components@1.0'),
  bip: bipSchema,
  input_basis: z.literal('component_mass_flow_kg_h'),
  fraction_basis: z.literal('mol/mol'),
  classification: z.enum(['vapor_liquid', 'single_liquid', 'single_vapor']),
  status: z.enum(['success_two_phase', 'success_single_phase']),
  iterations: z.number().int().nonnegative(),
  beta: num.min(0).max(1),
  liquid_fraction: num.min(0).max(1),
  x: fractionMap.nullable(),
  y: fractionMap.nullable(),
  Z_L: positive.nullable(),
  Z_V: positive.nullable(),
  phi_L: rates.nullable(),
  phi_V: rates.nullable(),
  final_K: rates.nullable(),
  fugacity_residual: signedMap.nullable(),
  rachford_rice_residual: num.nullable(),
  material_reconstruction_residual: signedMap,
  inlet_molar_flow_kmol_h: positive,
  vapor_molar_flow_kmol_h: nonnegative,
  liquid_molar_flow_kmol_h: nonnegative,
  component_molar_residual_kmol_h: signedMap,
  component_molar_tolerance_kmol_h: positive,
  component_mass_residual_kg_h: signedMap,
  total_mass_residual_kg_h: num,
});
export const equilibriumResultsSchema = networkResultsSchema
  .omit({ model_tolerances: true })
  .extend({
    schema_version: z.literal('1.6'),
    process_result_version: z.literal('1.6'),
    engine: networkResultsSchema.shape.engine.extend({ version: z.literal('1.5.0') }),
    streams: z.record(
      id,
      molecularResultFields.streams.valueType.extend({ enthalpy_flow_W: z.null() }),
    ),
    equipment: z
      .array(
        z.strictObject({
          id,
          type: z.literal('equilibrium_separator_2phase'),
          model: equilibriumModel,
          duty_W: z.null(),
          work_W: z.null(),
          energy_residual_W: z.null(),
          mass_balance: legacyResultsSchema.shape.balances.shape.mass,
          thermodynamics: equilibriumDetails,
          material_streams: z.strictObject({ inlet: id, vapor: id, liquid: id }),
        }),
      )
      .length(1),
    balances: z.strictObject({
      mass: legacyResultsSchema.shape.balances.shape.mass,
      energy: unavailableEnergy,
    }),
  });
const thermalPhase = z.strictObject({
  composition: fractionMap,
  Z: positive,
  h_ig_J_mol: num,
  h_res_J_mol: num,
  h_J_mol: num,
});
export const thermalStateSchema = z.strictObject({
  temperature_K: positive,
  pressure_Pa_abs: positive,
  z: fractionMap,
  classification: z.enum(['single_liquid', 'vapor_liquid', 'single_vapor']),
  beta: num.min(0).max(1),
  H_eq_J_mol: num,
  phases: z.strictObject({ liquid: thermalPhase.optional(), vapor: thermalPhase.optional() }),
  pt_status: z.enum(['success_single_phase', 'success_two_phase']),
  max_log_fugacity_residual: nonnegative,
});
export const thermalDetailsSchema = z.strictObject({
  mode: z.enum(['specified_outlet_temperature', 'specified_heat_duty']),
  property_package: z.literal('peng_robinson@1.0'),
  component_dataset: z.literal('riogineer_components@1.0'),
  molecular_provider: z.literal('molecular_composition@1.0'),
  caloric_dataset: z.literal('riogineer_caloric@1.0'),
  caloric_reference: z.literal('ideal_gas_sensible_298.15K_101325Pa@1.0'),
  bip: thermalBip,
  F_mol_s: positive,
  inlet: thermalStateSchema,
  outlet: thermalStateSchema,
  delta_H_J_mol: num,
  Q_W: num,
  energy_residual_W: num,
  energy_allowance_W: positive,
  H_out_target_J_mol: num.nullable(),
  ph: z
    .strictObject({
      status: z.literal('success'),
      capability: z.literal('flash_PH'),
      pt_profile: z.literal('high_accuracy'),
      root_iterations: z.number().int().nonnegative(),
      evaluation_count: z.number().int().positive(),
      enthalpy_residual_J_mol: num,
    })
    .nullable(),
});
const thermalResultsSchema = networkResultsSchema.omit({ model_tolerances: true }).extend({
  schema_version: z.literal('1.7'),
  process_result_version: z.literal('1.7'),
  engine: networkResultsSchema.shape.engine.extend({ version: z.literal('1.6.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('heater'),
        model: rigorousHeaterModel,
        duty_W: num,
        work_W: z.literal(0),
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
        thermodynamics: thermalDetailsSchema,
      }),
    )
    .length(1),
  balances: z.strictObject({
    mass: legacyResultsSchema.shape.balances.shape.mass,
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: num,
      model: z.literal('equilibrium_energy_balance_pr'),
      positive_duty: z.literal('heat_into_process'),
    }),
  }),
});
const compressorPhase = thermalPhase.extend({
  s_ig_J_mol_K: num,
  s_res_J_mol_K: num,
  s_J_mol_K: num,
});
export const compressorStateSchema = thermalStateSchema.extend({
  S_eq_J_mol_K: num,
  phases: z.strictObject({ liquid: compressorPhase.optional(), vapor: compressorPhase.optional() }),
});
const compressorInverse = z.strictObject({
  status: z.literal('success'),
  pt_profile: z.literal('high_accuracy'),
  candidate_count: z.literal(1),
  bracket_K: z.tuple([positive, positive]),
  final_bracket_K: z.tuple([positive, positive]),
  root_iterations: z.number().int().nonnegative(),
  evaluation_count: z.number().int().positive(),
});
export const compressorDetailsSchema = thermalDetailsSchema
  .pick({
    property_package: true,
    component_dataset: true,
    molecular_provider: true,
    caloric_dataset: true,
    caloric_reference: true,
    bip: true,
    F_mol_s: true,
    energy_residual_W: true,
    energy_allowance_W: true,
  })
  .extend({
    inlet: compressorStateSchema,
    isentropic_outlet: compressorStateSchema,
    actual_outlet: compressorStateSchema,
    pressure_ratio: num.gt(1),
    isentropic_efficiency: efficiency,
    reconstructed_efficiency: positive,
    eta_power: positive,
    efficiency_allowance: positive,
    H_out_target_J_mol: num,
    delta_H_is_J_mol: positive,
    delta_H_actual_J_mol: positive,
    isentropic_fluid_power_W: positive,
    fluid_power_W: positive,
    power_identity_residual_W: num,
    power_identity_allowance_W: positive,
    delta_S_actual_J_mol_K: num,
    ps: compressorInverse.extend({
      capability: z.literal('flash_PS'),
      entropy_residual_J_mol_K: num,
    }),
    ph: compressorInverse.extend({
      capability: z.literal('flash_PH'),
      enthalpy_residual_J_mol: num,
    }),
  });
const rigorousCompressionResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.8'),
  process_result_version: z.literal('1.8'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.7.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('compressor'),
        model: rigorousCompressorModel,
        duty_W: z.literal(0),
        work_W: positive,
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
        thermodynamics: compressorDetailsSchema,
      }),
    )
    .length(1),
  balances: thermalResultsSchema.shape.balances.extend({
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: z.literal(0),
      fluid_power_W: positive,
      model: z.literal('rigorous_isentropic_pr'),
      positive_work: z.literal('work_into_process'),
    }),
  }),
});
export const exchangerDetailsSchema = thermalDetailsSchema
  .pick({
    property_package: true,
    component_dataset: true,
    molecular_provider: true,
    caloric_dataset: true,
    caloric_reference: true,
    bip: true,
    energy_residual_W: true,
    energy_allowance_W: true,
  })
  .extend({
    specification_mode: z.enum([
      'specified_hot_outlet_temperature',
      'specified_cold_outlet_temperature',
    ]),
    hot_molar_flow_mol_s: positive,
    cold_molar_flow_mol_s: positive,
    hot_inlet: compressorStateSchema,
    hot_outlet: compressorStateSchema,
    cold_inlet: compressorStateSchema,
    cold_outlet: compressorStateSchema,
    Q_hot_W: num,
    Q_cold_W: num,
    Q_exchanged_W: nonnegative,
    recovered_outlet_target_enthalpy_J_mol: num,
    ph: compressorInverse.extend({
      capability: z.literal('flash_PH'),
      enthalpy_residual_J_mol: num,
    }),
  });
const exchangerSideBalances = z.strictObject({
  hot: legacyResultsSchema.shape.balances.shape.mass,
  cold: legacyResultsSchema.shape.balances.shape.mass,
});
export const exchangerResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.9'),
  process_result_version: z.literal('1.9'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.8.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('two_stream_heat_exchanger'),
        model: exchangerModel,
        duty_W: z.literal(0),
        work_W: z.literal(0),
        material_streams: z.strictObject({ hot_in: id, hot_out: id, cold_in: id, cold_out: id }),
        material_balances: exchangerSideBalances,
        energy_residual_W: num,
        thermodynamics: exchangerDetailsSchema,
      }),
    )
    .min(1),
  balances: z.strictObject({
    material_paths: z.record(id, exchangerSideBalances),
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: z.literal(0),
      model: z.literal('rigorous_two_stream_pr'),
      positive_duty: z.literal('heat_into_each_material_path'),
    }),
  }),
});
// Reuse caloric state fields, adding phase consistency only to the new M16 branch.
const valveLiquidState = compressorStateSchema.extend({
  classification: z.literal('single_liquid'),
  beta: z.literal(0),
  pt_status: z.literal('success_single_phase'),
  phases: z.strictObject({ liquid: compressorPhase }),
});
const valveVaporState = compressorStateSchema.extend({
  classification: z.literal('single_vapor'),
  beta: z.literal(1),
  pt_status: z.literal('success_single_phase'),
  phases: z.strictObject({ vapor: compressorPhase }),
});
const valveTwoPhaseState = compressorStateSchema.extend({
  classification: z.literal('vapor_liquid'),
  beta: num.gt(0).lt(1),
  pt_status: z.literal('success_two_phase'),
  phases: z.strictObject({ liquid: compressorPhase, vapor: compressorPhase }),
});
export const valveDetailsSchema = thermalDetailsSchema
  .pick({
    property_package: true,
    component_dataset: true,
    molecular_provider: true,
    caloric_dataset: true,
    caloric_reference: true,
    bip: true,
    F_mol_s: true,
    energy_residual_W: true,
    energy_allowance_W: true,
  })
  .extend({
    inlet: z.discriminatedUnion('classification', [valveLiquidState, valveVaporState]),
    outlet: z.discriminatedUnion('classification', [
      valveLiquidState,
      valveVaporState,
      valveTwoPhaseState,
    ]),
    pressure_ratio: positive.lt(1), // P_out / P_in
    pressure_drop_Pa: positive,
    H_out_target_J_mol: num,
    delta_H_J_mol: num,
    delta_S_J_mol_K: num,
    enthalpy_residual_J_mol: num,
    ph: compressorInverse.extend({
      capability: z.literal('flash_PH'),
      enthalpy_residual_J_mol: num,
    }),
  });
export const valveResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.10'),
  process_result_version: z.literal('1.10'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.9.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('throttling_valve'),
        model: rigorousValveModel,
        material_streams: z.strictObject({ inlet: id, outlet: id }),
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
        thermodynamics: valveDetailsSchema,
      }),
    )
    .length(1),
  balances: z.strictObject({
    mass: legacyResultsSchema.shape.balances.shape.mass,
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      model: z.literal('rigorous_isenthalpic_pr'),
    }),
  }),
});
const separatorState = z.discriminatedUnion('classification', [
  valveLiquidState,
  valveVaporState,
  valveTwoPhaseState,
]);
const separatorPhaseFlow = z.union([
  z.strictObject({
    molar_flow_mol_s: positive,
    composition: fractionMap,
    h_J_mol: num,
    enthalpy_flow_W: num,
  }),
  z.strictObject({
    molar_flow_mol_s: z.literal(0),
    composition: z.null(),
    h_J_mol: z.null(),
    enthalpy_flow_W: z.literal(0),
  }),
]);
const separatorDetailsCommon = valveDetailsSchema
  .pick({
    property_package: true,
    component_dataset: true,
    molecular_provider: true,
    caloric_dataset: true,
    caloric_reference: true,
    bip: true,
    F_mol_s: true,
    energy_residual_W: true,
    energy_allowance_W: true,
  })
  .extend({
    inlet: separatorState,
    outlet: separatorState,
    phases: z.strictObject({ vapor: separatorPhaseFlow, liquid: separatorPhaseFlow }),
    inlet_enthalpy_flow_W: num,
    component_molar_residual_kmol_h: signedMap,
    zero_duty_tolerance_W: positive,
  });
export const separatorEnergyDetailsSchema = z.discriminatedUnion('mode', [
  separatorDetailsCommon.extend({
    mode: z.literal('specified_temperature'),
    duty_W: num,
    ph: z.null(),
  }),
  separatorDetailsCommon.extend({
    mode: z.literal('adiabatic'),
    duty_W: z.literal(0),
    ph: valveDetailsSchema.shape.ph,
  }),
]);
export const separatorEnergyResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.11'),
  process_result_version: z.literal('1.11'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.10.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('equilibrium_separator_2phase'),
        model: separatorEnergyModel,
        material_streams: z.strictObject({ inlet: id, vapor: id, liquid: id }),
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        duty_W: num,
        work_W: z.literal(0),
        energy_residual_W: num,
        thermodynamics: separatorEnergyDetailsSchema,
      }),
    )
    .length(1),
  balances: z.strictObject({
    mass: legacyResultsSchema.shape.balances.shape.mass,
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: num,
      model: z.literal('equilibrium_separator_energy_pr'),
      positive_duty: z.literal('heat_into_equipment'),
    }),
  }),
});
const pumpStability = z.strictObject({
  stable: z.literal(true),
  classification: z.string(),
  converged: z.literal(true),
  iterations: z.number().int().nonnegative(),
  minimum_tpd_RT: num,
  phase_identification_parameter: num.gt(1),
  provider: z.literal('peng_robinson@1.0'),
  algorithm: z.string(),
  trials: z.array(
    z.strictObject({
      composition: z.array(num),
      root_kind: z.string(),
      tpd_RT: num,
      iterations: z.number().int().nonnegative(),
      interval_width: num,
      converged: z.boolean(),
    }),
  ),
});
const pumpState = compressorStateSchema.extend({
  temperature_K: num.min(300).max(370),
  pressure_Pa_abs: num.min(20e6).max(30e6),
  classification: z.literal('single_liquid'),
  beta: z.literal(0),
  pt_status: z.literal('success_single_phase'),
  phases: z.strictObject({ liquid: compressorPhase }),
  pt_profile: z.literal('high_accuracy'),
  stability: pumpStability,
});
const pumpWitness = pumpState.extend({ pressure_Pa_abs: z.literal(16e6) });
const pumpInverse = compressorInverse.extend({
  capability: z.enum(['PS', 'PH']),
  scan_count: z.union([z.literal(64), z.literal(128)]),
  fresh_final_count: z.literal(1),
  temperature_bounds_K: z.tuple([z.literal(200), z.literal(500)]),
  residual: num,
  failure_count: z.number().int().nonnegative(),
});
const pumpCommonDetails = compressorDetailsSchema
  .pick({
    property_package: true,
    component_dataset: true,
    molecular_provider: true,
    caloric_dataset: true,
    caloric_reference: true,
    bip: true,
    F_mol_s: true,
    energy_residual_W: true,
    energy_allowance_W: true,
  })
  .extend({
    guard_status: z.literal('accepted'),
    inlet: pumpState,
    actual_outlet: pumpState,
    outlet_pressure_Pa_abs: num.min(20e6).max(30e6),
    isentropic_efficiency: num.min(0.6).max(1),
    H_out_target_J_mol: num,
    delta_H_actual_J_mol: nonnegative,
    delta_H_is_J_mol: nonnegative,
    target_fluid_power_W: nonnegative,
    fluid_power_W: nonnegative,
    delta_S_actual_J_mol_K: num,
    power_identity_residual_W: num,
    power_identity_allowance_W: positive,
  });
export const pumpDetailsSchema = z.discriminatedUnion('mode', [
  pumpCommonDetails.extend({
    mode: z.literal('identity'),
    isentropic_outlet: z.null(),
    reconstructed_efficiency: z.null(),
    delta_H_actual_J_mol: z.literal(0),
    delta_H_is_J_mol: z.literal(0),
    target_fluid_power_W: z.literal(0),
    fluid_power_W: z.literal(0),
    work_screening_allowance_J_mol: z.null(),
    work_screening_ratio: z.null(),
    witnesses: z.strictObject({ inlet: pumpWitness }),
    ps: z.strictObject({ status: z.literal('not_applicable') }),
    ph: z.strictObject({ status: z.literal('not_applicable') }),
  }),
  pumpCommonDetails.extend({
    mode: z.literal('pressure_rise'),
    isentropic_outlet: pumpState,
    reconstructed_efficiency: positive,
    delta_H_actual_J_mol: positive,
    delta_H_is_J_mol: positive,
    target_fluid_power_W: positive,
    fluid_power_W: positive,
    work_screening_allowance_J_mol: positive,
    work_screening_ratio: positive.max(1e-4),
    witnesses: z.strictObject({ inlet: pumpWitness, isentropic: pumpWitness, outlet: pumpWitness }),
    ps: pumpInverse.extend({
      capability: z.literal('PS'),
      scan_count: z.literal(64),
      failure_count: z.literal(0),
      residual: num.min(-1e-8).max(1e-8),
    }),
    ph: pumpInverse.extend({
      capability: z.literal('PH'),
      scan_count: z.literal(128),
      residual: num.min(-1e-6).max(1e-6),
    }),
  }),
]);
export const pumpResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.12'),
  process_result_version: z.literal('1.12'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.11.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('pump'),
        model: pumpModel,
        material_streams: z.strictObject({ inlet: id, outlet: id }),
        duty_W: z.literal(0),
        work_W: nonnegative,
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
        thermodynamics: pumpDetailsSchema,
      }),
    )
    .length(1),
  balances: thermalResultsSchema.shape.balances.extend({
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: z.literal(0),
      fluid_power_W: nonnegative,
      model: z.literal('rigorous_isentropic_pump_pr'),
      positive_work: z.literal('work_into_process'),
    }),
  }),
});
export const variablePumpResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.13'),
  process_result_version: z.literal('1.13'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.12.0') }),
  equipment: z
    .array(
      z.strictObject({
        id,
        type: z.literal('pump'),
        model: variablePumpModel,
        material_streams: z.strictObject({ inlet: id, outlet: id }),
        duty_W: z.literal(0),
        work_W: nonnegative,
        mass_balance: legacyResultsSchema.shape.balances.shape.mass,
        energy_residual_W: num,
        thermodynamics: pumpDetailsSchema,
      }),
    )
    .length(1),
  balances: thermalResultsSchema.shape.balances.extend({
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: z.literal(0),
      fluid_power_W: nonnegative,
      model: z.literal('rigorous_isentropic_pump_pr'),
      positive_work: z.literal('work_into_process'),
    }),
  }),
});
const materialProducer = z.strictObject({
  run_id: z.string().uuid(),
  input_sha256: hash,
  requirements_sha256: hash,
  equipment_id: id,
  port_id: id,
  stream_id: id,
});
export const derivedStateContextSchema = z.strictObject({
  specification_kind: z.literal('upstream_derived'),
  phase: z.enum(['liquid', 'vapor']),
  saturation: z.enum(['source_vle', 'unknown', 'compressed_witness']),
  source: materialProducer,
  lineage: z.array(materialProducer).optional(),
  thermodynamics: z.strictObject({
    property_package: z.literal('peng_robinson@1.0'),
    component_dataset: z.string(),
    caloric_dataset: z.string(),
    caloric_reference: z.string(),
    bip: z.record(z.string(), z.json()),
  }),
});
export const separatorPumpResultsSchema = thermalResultsSchema.extend({
  schema_version: z.literal('1.14'),
  process_result_version: z.literal('1.14'),
  engine: thermalResultsSchema.shape.engine.extend({ version: z.literal('1.13.0') }),
  streams: z.record(
    id,
    stateSchema.extend({
      properties: streamPropertiesSchema,
      state_context: z
        .union([
          derivedStateContextSchema,
          z.strictObject({ specification_kind: z.enum(['independent_PT', 'independent_caloric']) }),
        ])
        .optional(),
    }),
  ),
  equipment: z
    .array(
      z.union([
        separatorEnergyResultsSchema.shape.equipment.element,
        z.strictObject({
          id,
          type: z.literal('pump'),
          model: separatorPumpModel,
          material_streams: z.strictObject({ inlet: id, outlet: id }),
          duty_W: z.literal(0),
          work_W: nonnegative,
          mass_balance: legacyResultsSchema.shape.balances.shape.mass,
          energy_residual_W: num,
          thermodynamics: z.strictObject({
            qualification_id: z.string(),
            source_spec_sha256: hash,
            identity: z.boolean(),
            isentropic_efficiency: num.min(0.6).max(1),
            reconstructed_efficiency: num.nullable(),
            energy_allowance_W: positive,
            diagnostics: z.record(z.string(), z.json()),
          }),
        }),
      ]),
    )
    .length(2),
  balances: z.strictObject({
    mass: legacyResultsSchema.shape.balances.shape.mass,
    energy: z.strictObject({
      status: z.literal('passed'),
      residual_W: num,
      tolerance_W: positive,
      duty_W: num,
      fluid_power_W: nonnegative,
      model: z.literal('separator_pump_energy'),
      positive_duty: z.literal('heat_into_process'),
      positive_work: z.literal('work_into_process'),
    }),
  }),
});
export const resultsSchema = z.union([
  separatorPumpResultsSchema,
  pumpResultsSchema,
  variablePumpResultsSchema,
  separatorEnergyResultsSchema,
  valveResultsSchema,
  exchangerResultsSchema,
  rigorousCompressionResultsSchema,
  thermalResultsSchema,
  equilibriumResultsSchema,
  molecularSingleResults,
  molecularNetworkResults,
  molecularSequentialResults,
  molecularCompressionResults,
  networkResultsSchema,
  sequentialResultsSchema,
  compressionResultsSchema,
  legacyResultsSchema,
  legacyResultsSchema.extend({
    schema_version: z.literal('1.1'),
    streams: z.record(id, stateSchema.extend({ properties: streamPropertiesSchema })),
  }),
]);
export const validationResponseSchema = z.strictObject({
  requirements: requirementsSchema,
  validation: validationSchema,
});
export const engineeringValidationResponseSchema = validationResponseSchema.extend({
  requirements: engineeringRequirementsSchema,
});
export const errorSchema = z.strictObject({
  error: z.strictObject({ code: z.string(), message: z.string(), issues: z.array(messageSchema) }),
});
export type Requirements = z.infer<typeof requirementsSchema>;
export type Flowsheet = z.infer<typeof flowsheetSchema>;
export type Results = z.infer<typeof resultsSchema>;
