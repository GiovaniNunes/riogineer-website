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
export const flowsheetSchema = z.strictObject({
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
const stateSchema = z.strictObject({
  component_mass_flow_kg_h: rates,
  mass_flow_kg_h: nonnegative,
  component_mass_fractions: fractionMap.nullable(),
  temperature_K: positive,
  pressure_Pa_abs: positive,
  enthalpy_flow_W: num,
});
export const resultsSchema = z.strictObject({
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
export const validationResponseSchema = z.strictObject({
  requirements: requirementsSchema,
  validation: validationSchema,
});
export const errorSchema = z.strictObject({
  error: z.strictObject({ code: z.string(), message: z.string(), issues: z.array(messageSchema) }),
});
export type Requirements = z.infer<typeof requirementsSchema>;
export type Flowsheet = z.infer<typeof flowsheetSchema>;
export type Results = z.infer<typeof resultsSchema>;
