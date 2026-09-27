import { z } from 'zod';
import { componentIdentifier } from './components';

export const fields = [
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
  'component_flow',
  'cp',
  'recovery_gas',
  'recovery_oil',
  'recovery_water',
] as const;
export const fieldSchema = z.enum(fields);
export const unitSchema = z.enum([
  'text',
  'K',
  'degC',
  'Pa_abs',
  'bar_abs',
  'bar',
  'bar_g',
  'kg/h',
  'kg/s',
  'J/(kg K)',
  'kJ/(kg K)',
  'mass_fraction',
  '%',
]);
export const evidenceSchema = z.strictObject({
  source_id: z.string().min(1).max(80),
  source_type: z.enum(['uploaded_document', 'user_text']),
  excerpt: z.string().min(1).max(60000),
  provider_excerpt: z.string().min(1).max(1200).optional(),
  source_start: z.number().int().nonnegative().optional(),
  source_end: z.number().int().positive().optional(),
  page: z.number().int().positive().nullable(),
});
export const factSchema = z.strictObject({
  field: fieldSchema,
  component: z
    .string()
    .regex(/^[A-Za-z][A-Za-z0-9_-]{0,79}$/)
    .nullable(),
  value: z.union([z.string().min(1).max(500), z.number().finite()]),
  unit: unitSchema,
  origin: z.enum(['specified', 'assumed', 'derived']),
  evidence: evidenceSchema,
  confidence: z.enum(['high', 'medium', 'low']),
});
export const issueSchema = z
  .strictObject({
    kind: z.enum(['missing', 'ambiguity', 'conflict', 'unsupported', 'scope_exclusion']),
    field: fieldSchema.nullable(),
    component: z.string().max(80).nullable(),
    message: z.string().min(1).max(1200),
    evidence: evidenceSchema.optional(),
  })
  .refine((issue) => issue.kind !== 'scope_exclusion' || issue.evidence !== undefined, {
    path: ['evidence'],
    message: 'A scope exclusion requires source evidence.',
  });
const providerEvidenceSchema = evidenceSchema
  .omit({ provider_excerpt: true, source_start: true, source_end: true })
  .extend({ excerpt: z.string().min(1).max(1200) });
export const interpretationSchema = z.strictObject({
  facts: z.array(factSchema.extend({ evidence: providerEvidenceSchema })).max(500),
  issues: z.array(issueSchema.safeExtend({ evidence: providerEvidenceSchema.optional() })).max(100),
});
export const sourceSchema = z.strictObject({
  id: z.string().min(1).max(80),
  type: z.enum(['uploaded_document', 'user_text']),
  label: z.string().max(200),
  pages: z
    .array(
      z.strictObject({ page: z.number().int().positive().nullable(), text: z.string().max(60000) }),
    )
    .max(40),
});
export const draftSchema = z.strictObject({
  version: z.literal('1.0'),
  id: z.string().uuid(),
  created_at: z.string(),
  provider: z.string().max(200),
  sources: z
    .array(
      z.strictObject({
        id: z.string(),
        type: z.enum(['uploaded_document', 'user_text']),
        label: z.string(),
        sha256: z.string(),
        pages: sourceSchema.shape.pages.optional(),
      }),
    )
    .max(3),
  facts: z.array(factSchema).max(500),
  issues: z.array(issueSchema.safeExtend({ id: z.string() })).max(300),
});
export const correctionSchema = z.strictObject({
  field: fieldSchema,
  component: z
    .string()
    .regex(/^[A-Za-z][A-Za-z0-9_-]{0,79}$/)
    .nullable(),
  value: z.union([z.string().min(1).max(500), z.number().finite()]),
  unit: unitSchema,
  note: z.string().min(1).max(500),
});
export const reviewSchema = z.strictObject({
  corrections: z.array(correctionSchema).max(300),
  assumptions: z.record(z.string(), z.enum(['accepted', 'rejected'])),
  resolutions: z.record(z.string(), z.string().min(1).max(500)),
  model_accepted: z.boolean(),
});
export const envelopeSchema = z.strictObject({
  draft: draftSchema,
  signature: z.string().regex(/^[a-f0-9]{64}$/),
});
export const approvalSchema = envelopeSchema.extend({ review: reviewSchema });
export type Field = z.infer<typeof fieldSchema>;
export type Fact = z.infer<typeof factSchema>;
export type Source = z.infer<typeof sourceSchema>;
export type Draft = z.infer<typeof draftSchema>;
export type Review = z.infer<typeof reviewSchema>;
export type Correction = z.infer<typeof correctionSchema>;
export type Envelope = z.infer<typeof envelopeSchema>;
export const emptyReview = (): Review => ({
  corrections: [],
  assumptions: {},
  resolutions: {},
  model_accepted: false,
});
export const factKey = (f: { field: Field; component: string | null }) =>
  `${f.field}${f.component ? ':' + componentIdentifier(f.component) : ''}`;
export const componentFields: Field[] = [
  'component_flow',
  'cp',
  'recovery_gas',
  'recovery_oil',
  'recovery_water',
];
export const labels: Record<Field, string> = {
  equipment: 'Equipment',
  topology: 'Process connections',
  components: 'Components (comma-separated IDs)',
  outputs: 'Requested outputs',
  total_flow: 'Specified total feed flow',
  feed_temperature: 'Feed temperature',
  feed_pressure: 'Feed pressure',
  separator_temperature: 'Separator temperature',
  separator_pressure: 'Separator pressure',
  reference_temperature: 'Reference temperature',
  component_flow: 'Mass flow',
  cp: 'Constant heat capacity',
  recovery_gas: 'Gas recovery',
  recovery_oil: 'Oil recovery',
  recovery_water: 'Water recovery',
};
export function unitsFor(field: Field): Fact['unit'][] {
  if (field.includes('temperature')) return ['K', 'degC'];
  if (field.includes('pressure')) return ['Pa_abs', 'bar_abs'];
  if (field.includes('flow')) return ['kg/h', 'kg/s'];
  if (field === 'cp') return ['J/(kg K)', 'kJ/(kg K)'];
  if (field.startsWith('recovery_')) return ['mass_fraction', '%'];
  return ['text'];
}
