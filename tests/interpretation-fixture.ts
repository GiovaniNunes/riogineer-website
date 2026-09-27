import { randomUUID } from 'node:crypto';
import reference from '../contracts/examples/requirements.json' with { type: 'json' };
import {
  type Draft,
  type Fact,
  type Field,
  type Source,
  type Review,
  emptyReview,
} from '../src/lib/digital-engineer/interpretation/contracts';
import { capabilityManifest } from '../src/lib/digital-engineer/interpretation/review';
export function fixture() {
  const facts: Fact[] = [];
  function add(
    field: Field,
    value: Fact['value'],
    unit: Fact['unit'],
    component: string | null = null,
    assumed = false,
  ) {
    const excerpt = `${assumed ? 'Assume ' : ''}${component || ''} ${field}: ${value} ${unit}.`;
    facts.push({
      field,
      component,
      value,
      unit,
      origin: assumed ? 'assumed' : 'specified',
      confidence: 'high',
      evidence: { source_id: 'specification', source_type: 'user_text', excerpt, page: null },
    });
  }
  const feed = reference.feeds[0].state,
    params = reference.equipment[0].parameters;
  add('equipment', capabilityManifest.equipment, 'text');
  add('topology', capabilityManifest.topology, 'text');
  add('components', reference.components.join(', '), 'text');
  add('outputs', capabilityManifest.outputs, 'text');
  add('total_flow', 110000, 'kg/h');
  add('feed_temperature', feed.temperature_K, 'K');
  add('feed_pressure', feed.pressure_Pa_abs, 'Pa_abs');
  add('separator_temperature', params.separator.temperature_K, 'K');
  add('separator_pressure', params.separator.pressure_Pa_abs, 'Pa_abs');
  add('reference_temperature', params.caloric_model.reference_temperature_K, 'K', null, true);
  for (const c of reference.components as (keyof typeof feed.component_mass_flow_kg_h)[]) {
    add('component_flow', feed.component_mass_flow_kg_h[c], 'kg/h', c);
    add('cp', params.caloric_model.cp_J_kg_K[c], 'J/(kg K)', c, true);
    for (const phase of ['gas', 'oil', 'water'] as const)
      add(`recovery_${phase}`, params.recovery_fractions[c][phase], 'mass_fraction', c, true);
  }
  const source: Source = {
    id: 'specification',
    type: 'user_text',
    label: 'Typed specification',
    pages: [{ page: null, text: facts.map((f) => f.evidence.excerpt).join('\n') }],
  };
  const draft: Draft = {
    version: '1.0',
    id: randomUUID(),
    created_at: '2026-09-27T00:00:00.000Z',
    provider: 'test-only',
    sources: [{ id: source.id, type: source.type, label: source.label, sha256: 'a'.repeat(64) }],
    facts,
    issues: [],
  };
  const review: Review = {
    ...emptyReview(),
    model_accepted: true,
    assumptions: Object.fromEntries(
      facts.flatMap((f, i) => (f.origin === 'assumed' ? [[String(i), 'accepted' as const]] : [])),
    ),
  };
  return { source, draft, review };
}
