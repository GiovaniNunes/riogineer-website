import { requirementsSchema, type Requirements } from '../contracts';
import { componentIdentifier, registeredComponentIds } from './components';
import { isExplicitScopeExclusion } from './scope';
import {
  componentFields,
  factKey,
  labels,
  unitsFor,
  type Fact,
  type Draft,
  type Review,
  type Field,
} from './contracts';

export const capabilityManifest = {
  profile: 'single_separator_development',
  equipment: 'three_phase_separator',
  topology: 'one_feed_one_separator_gas_oil_water',
  outputs: 'gas, oil, water',
  model: 'prescribed_component_recoveries@1.0',
  required: [
    'equipment',
    'topology',
    'components',
    'feed_temperature',
    'feed_pressure',
    'separator_temperature',
    'separator_pressure',
    'reference_temperature',
    ...componentFields,
  ],
  limitations: [
    'No equilibrium prediction',
    'No sizing',
    'No geometry-based efficiency',
    'No multiple equipment or feeds',
    'Prescribed recoveries only',
    'Constant Cp; no latent heat or pressure/phase dependence',
  ],
} as const;
export type Value = Pick<Fact, 'field' | 'component' | 'value' | 'unit'>;
const supportedOutputs = ['gas', 'oil', 'water'] as const;
// Tokenize presentation variants, never discard unknown requested outputs.
export function outputIds(value: Value['value']): string[] {
  return typeof value === 'string'
    ? [
        ...new Set(
          value
            .toLowerCase()
            .replace(/\band\b/g, ',')
            .split(',')
            .map((id) => id.trim())
            .filter(Boolean),
        ),
      ].sort()
    : [];
}
export function supportedRequestedOutputs(value: Value['value']) {
  const ids = outputIds(value);
  return ids.length === supportedOutputs.length && supportedOutputs.every((id) => ids.includes(id));
}
export function normalize(f: Value): Value {
  if (f.component !== null) f = { ...f, component: componentIdentifier(f.component) };
  if (f.field === 'components' && f.unit === 'text' && typeof f.value === 'string')
    return { ...f, value: registeredComponentIds(f.value).join(', ') };
  // Whole-phrase aliases only: never infer topology or drop unsupported equipment.
  if (f.unit === 'text' && typeof f.value === 'string') {
    const wording = f.value.trim().toLowerCase();
    if (
      f.field === 'equipment' &&
      [
        'three_phase_separator',
        'three-phase separator',
        'three phase separator',
        'separador trifásico',
      ].includes(wording)
    )
      return { ...f, value: capabilityManifest.equipment };
    if (
      f.field === 'topology' &&
      [
        'one_feed_one_separator_gas_oil_water',
        'one feed, one separator, gas, oil and water outlets',
        'one feed, one separator, gas, oil, water outlets',
        'uma alimentação, um separador, saídas de gás, óleo e água',
      ].includes(wording)
    )
      return { ...f, value: capabilityManifest.topology };
  }
  if (f.field === 'outputs' && f.unit === 'text')
    return supportedRequestedOutputs(f.value) ? { ...f, value: capabilityManifest.outputs } : f;
  if (typeof f.value !== 'number') return f;
  const conversions: Partial<Record<Fact['unit'], [number, number, Fact['unit']]>> = {
    degC: [1, 273.15, 'K'],
    bar_abs: [100000, 0, 'Pa_abs'],
    'kg/s': [3600, 0, 'kg/h'],
    'kJ/(kg K)': [1000, 0, 'J/(kg K)'],
    '%': [0.01, 0, 'mass_fraction'],
  };
  const c = conversions[f.unit];
  return c ? { ...f, value: f.value * c[0] + c[1], unit: c[2] } : f;
}
export function sameValue(a: Value, b: Value) {
  const x = normalize(a),
    y = normalize(b);
  return x.value === y.value && x.unit === y.unit;
}
export function effectiveValues(draft: Draft, review: Review) {
  const values = new Map<string, Value>();
  draft.facts.forEach((f, index) => {
    if (f.origin === 'derived') return;
    if (f.origin === 'assumed' && review.assumptions[String(index)] !== 'accepted') return;
    const key = factKey(f);
    if (!values.has(key)) values.set(key, f);
  });
  review.corrections.forEach((c) => values.set(factKey(c), c));
  return values;
}
export function componentIds(values: Map<string, Value>) {
  return registeredComponentIds(values.get('components')?.value);
}
export function reviewFields(
  draft: Draft,
  review: Review,
): { field: Field; component: string | null }[] {
  const values = effectiveValues(draft, review);
  const base: Field[] = [
    'equipment',
    'topology',
    'components',
    'outputs',
    'total_flow',
    'feed_temperature',
    'feed_pressure',
    'separator_temperature',
    'separator_pressure',
    'reference_temperature',
  ];
  return [
    ...base.map((field) => ({ field, component: null })),
    ...componentIds(values).flatMap((component) =>
      componentFields.map((field) => ({ field, component })),
    ),
  ];
}
export function isMissingValue(value: Value | undefined) {
  return !value || (typeof value.value === 'string' && !value.value.trim());
}
export function isOrdinaryMissingInput(
  issue: Draft['issues'][number],
  draft: Draft,
  review: Review,
) {
  return (
    issue.kind === 'missing' &&
    issue.field !== null &&
    capabilityManifest.required.some((field) => field === issue.field) &&
    unitsFor(issue.field)[0] !== 'text' &&
    reviewFields(draft, review).some(
      (field) => factKey(field) === factKey({ field: issue.field!, component: issue.component }),
    )
  );
}
export function blockers(draft: Draft, review: Review): string[] {
  const errors: string[] = [];
  const values = effectiveValues(draft, review);
  const components = componentIds(values);
  if (!review.model_accepted) errors.push('Accept the development model and its limitations.');
  if (
    !components.length ||
    components.length > 50 ||
    new Set(components).size !== components.length ||
    components.some((c) => !/^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(c))
  )
    errors.push(
      'Provide 1–50 unique component IDs (letters, digits, underscores or hyphens; start with a letter).',
    );
  for (const f of reviewFields(draft, review)) {
    const key = factKey(f),
      v = values.get(key);
    if (['total_flow', 'outputs'].includes(f.field) && !v) continue;
    if (isMissingValue(v)) {
      errors.push(
        `Missing information: ${f.component ? f.component + ' — ' : ''}${labels[f.field]}.`,
      );
      continue;
    }
    if (!v) continue;
    if (!unitsFor(f.field).includes(v.unit))
      errors.push(`${key}: specify an explicit supported unit; pressure must be absolute.`);
    if (v.unit !== 'text' && (typeof v.value !== 'number' || !Number.isFinite(v.value)))
      errors.push(`${key}: enter a finite number.`);
    const n = normalize(v);
    if (typeof n.value === 'number') {
      if (
        (f.field.includes('temperature') || f.field.includes('pressure') || f.field === 'cp') &&
        n.value <= 0
      )
        errors.push(`${key}: must be positive in canonical units.`);
      if (f.field.includes('flow') && n.value < 0) errors.push(`${key}: cannot be negative.`);
      if (f.field.startsWith('recovery_') && (n.value < 0 || n.value > 1))
        errors.push(`${key}: recovery must be between 0 and 1.`);
    }
  }
  if (
    !values.has('equipment') ||
    normalize(values.get('equipment')!).value !== capabilityManifest.equipment
  )
    errors.push('UNSUPPORTED CAPABILITY: equipment must be a three-phase separator.');
  if (
    !values.has('topology') ||
    normalize(values.get('topology')!).value !== capabilityManifest.topology
  )
    errors.push(
      'UNSUPPORTED CAPABILITY: exactly one feed, one separator and gas/oil/water outlets are supported.',
    );
  if (values.has('outputs') && !supportedRequestedOutputs(values.get('outputs')!.value))
    errors.push(
      'UNSUPPORTED CAPABILITY: supported products are gas, oil, water; available calculations are streams and mass/energy balances.',
    );
  const groups = Map.groupBy(draft.facts, factKey);
  for (const [key, facts] of groups) {
    if (facts.some((f) => !sameValue(f, facts[0]))) {
      if (!review.corrections.some((c) => factKey(c) === key))
        errors.push(`CONFLICT DETECTED: ${key}. Select or replace the value explicitly.`);
      if (!review.resolutions[`conflict:${key}`]?.trim())
        errors.push(`CONFLICT DETECTED: ${key}. Explain the selection in a resolution note.`);
    }
  }
  draft.facts.forEach((f, index) => {
    const corrected = review.corrections.some((c) => factKey(c) === factKey(f));
    if (f.origin === 'assumed' && !review.assumptions[String(index)])
      errors.push(`Assumption ${index + 1}: explicitly accept or reject.`);
    if ((f.confidence === 'low' || f.origin === 'derived') && !corrected)
      errors.push(`${factKey(f)}: confirm or replace this uncertain/derived interpretation.`);
  });
  for (const issue of draft.issues) {
    if (issue.kind === 'scope_exclusion') {
      if (!isExplicitScopeExclusion(issue.evidence?.excerpt))
        errors.push('Invalid scope exclusion: reinterpret the source statement.');
      continue;
    }
    // The required-field checks above already gate these inputs. Keep the original
    // issue in provenance, without a second blocker or an explanation requirement.
    if (isOrdinaryMissingInput(issue, draft, review)) continue;
    if (issue.kind === 'unsupported') {
      errors.push(
        `UNSUPPORTED CAPABILITY: ${issue.message} Revise the specification and interpret again.`,
      );
      continue;
    }
    if (
      issue.kind === 'missing' &&
      issue.field &&
      values.has(factKey({ field: issue.field, component: issue.component }))
    )
      continue;
    if (!review.resolutions[issue.id]?.trim())
      errors.push(`${issue.kind.toUpperCase()}: ${issue.message}`);
    else if (
      issue.field &&
      !review.corrections.some(
        (c) => factKey(c) === factKey({ field: issue.field!, component: issue.component }),
      )
    )
      errors.push(`Resolve ${issue.message} by entering a reviewed value.`);
  }
  // Reject orphan component data rather than silently dropping it from the engineering basis.
  for (const v of values.values())
    if (v.component && !components.includes(componentIdentifier(v.component)))
      errors.push(
        `Component ${v.component} is absent from the component basis. Correct the basis or reinterpret the specification.`,
      );
  if (values.has('total_flow') && components.length) {
    const total = normalize(values.get('total_flow')!).value;
    const rates = components
      .map((c) => values.get('component_flow:' + c))
      .filter((v) => !!v)
      .map((v) => normalize(v!).value);
    if (
      typeof total === 'number' &&
      rates.length === components.length &&
      rates.every((v) => typeof v === 'number')
    ) {
      const sum = (rates as number[]).reduce((a, b) => a + b, 0);
      if (Math.abs(total - sum) > Math.max(1e-6, Math.abs(total) * 1e-9))
        errors.push(
          'CONFLICT DETECTED: specified total feed flow does not equal the supplied component flows. Correct the inputs; no composition is inferred.',
        );
    }
  }
  return [...new Set(errors)];
}
export function finalizeRequirements(
  draft: Draft,
  review: Review,
  approvedAt: string,
): Requirements {
  const errors = blockers(draft, review);
  if (errors.length) throw new Error(errors.join('\n'));
  const values = effectiveValues(draft, review);
  const components = componentIds(values);
  const n = (field: Field, component: string | null = null) =>
    normalize(values.get(factKey({ field, component }))!).value as number;
  const map = (field: Field) => Object.fromEntries(components.map((c) => [c, n(field, c)]));
  const audit = {
    format: 'riogineer.interpretation-approval',
    version: '1.0',
    interpretation: draft,
    review,
    approved_at: approvedAt,
    status: 'user_reviewed',
    normalized_values: [...values.values()].map((v) => {
      const correction = review.corrections.find((c) => factKey(c) === factKey(v));
      const fact = draft.facts.find((f) => factKey(f) === factKey(v) && sameValue(f, v));
      const converted = v.unit !== normalize(v).unit;
      const normalizedText = v.unit === 'text' && v.value !== normalize(v).value;
      const mappedComponent = v.component !== normalize(v).component;
      return {
        ...normalize(v),
        origin:
          converted || normalizedText || mappedComponent
            ? 'derived'
            : correction
              ? 'specified'
              : fact?.origin,
        review_status: correction ? 'user_specified' : 'user_reviewed',
        derivation: converted
          ? 'deterministic_unit_conversion'
          : normalizedText
            ? 'deterministic_text_normalization'
            : mappedComponent
              ? 'deterministic_component_identity'
              : null,
        original_value: v.value,
        original_unit: v.unit,
        original_component: v.component,
        ...(mappedComponent
          ? {
              component_mapping: {
                source_name: v.component,
                registered_id: normalize(v).component,
              },
            }
          : {}),
        ...(v.field === 'outputs' ? { normalized_output_ids: outputIds(v.value) } : {}),
        evidence: correction
          ? {
              source_id: 'review',
              source_type: 'user_text',
              excerpt: `${correction.value} ${correction.unit}. ${correction.note}`,
              page: null,
            }
          : fact?.evidence,
      };
    }),
    model: capabilityManifest,
  };
  // The unchanged v1 source string carries a versioned JSON audit envelope. No v1 field or validation is relaxed.
  return requirementsSchema.parse({
    schema_version: '1.0',
    kind: 'requirements',
    case_id: 'SPEC_' + draft.id.replaceAll('-', ''),
    profile: 'single_separator_development',
    units: {
      temperature: 'K',
      pressure: 'Pa_abs',
      component_mass_flow: 'kg/h',
      heat_capacity: 'J/(kg K)',
      duty: 'W',
      recovery: 'mass_fraction',
    },
    provenance: { source: JSON.stringify(audit), basis: 'synthetic_development_assumptions' },
    components,
    feeds: [
      {
        id: 'FEED',
        state: {
          temperature_K: n('feed_temperature'),
          pressure_Pa_abs: n('feed_pressure'),
          component_mass_flow_kg_h: map('component_flow'),
        },
      },
    ],
    equipment: [
      {
        id: 'SEP_1',
        type: 'three_phase_separator',
        model: { id: 'prescribed_component_recoveries', version: '1.0' },
        parameters: {
          separator: {
            temperature_K: n('separator_temperature'),
            pressure_Pa_abs: n('separator_pressure'),
            thermal_mode: 'specified_temperature_calculate_duty',
          },
          recovery_fractions: Object.fromEntries(
            components.map((c) => [
              c,
              {
                gas: n('recovery_gas', c),
                oil: n('recovery_oil', c),
                water: n('recovery_water', c),
              },
            ]),
          ),
          caloric_model: {
            type: 'constant_cp_no_pressure_or_phase_dependence',
            reference_temperature_K: n('reference_temperature'),
            cp_J_kg_K: map('cp'),
          },
        },
      },
    ],
    required_outputs: ['streams', 'mass_balance', 'energy_balance'],
  });
}
