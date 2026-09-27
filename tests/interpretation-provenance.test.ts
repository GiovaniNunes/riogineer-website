import { afterEach, describe, expect, it, vi } from 'vitest';
import { fixture } from './interpretation-fixture';
import { type Fact } from '../src/lib/digital-engineer/interpretation/contracts';
import {
  configuredProvider,
  systemPrompt,
} from '../src/lib/digital-engineer/interpretation/provider';
import {
  handleInterpretRequest,
  interpretSources,
} from '../src/lib/digital-engineer/interpretation/service';
import { blockers, finalizeRequirements } from '../src/lib/digital-engineer/interpretation/review';

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

function diagnosticLog() {
  vi.stubEnv('NODE_ENV', 'development');
  return vi.spyOn(console, 'warn').mockImplementation(() => {});
}
function adapter(raw: unknown) {
  return configuredProvider(
    {
      RIOGINEER_LLM_PROVIDER: 'chat-completions',
      RIOGINEER_LLM_ENDPOINT: 'https://provider.example/v1/chat/completions',
      RIOGINEER_LLM_MODEL: 'private-model-name',
      RIOGINEER_LLM_API_KEY: 'private-credential',
    },
    async () =>
      Response.json({
        choices: [{ finish_reason: 'stop', message: { content: JSON.stringify(raw) } }],
      }),
  );
}
function request(text: string) {
  const form = new FormData();
  form.set('specification', text);
  return new Request('http://localhost/api/digital-engineer/interpret-specification', {
    method: 'POST',
    headers: { Origin: 'http://localhost' },
    body: form,
  });
}

describe('provider provenance diagnostics (constructed regressions, not a captured live response)', () => {
  it.each([
    [
      'source_id_mismatch',
      (f: Fact) => {
        f.evidence.source_id = 'wrong';
      },
    ],
    [
      'source_type_mismatch',
      (f: Fact) => {
        f.evidence.source_type = 'uploaded_document';
      },
    ],
    [
      'page_not_found',
      (f: Fact) => {
        f.evidence.page = 1;
      },
    ],
    [
      'excerpt_not_exact',
      (f: Fact) => {
        f.evidence.excerpt = 'private fabricated excerpt';
      },
    ],
    [
      'component_scope_mismatch',
      (f: Fact) => {
        f.component = 'water';
      },
    ],
    [
      'derived_origin_forbidden',
      (f: Fact) => {
        f.origin = 'derived';
      },
    ],
  ] as const)(
    'reports %s with the exact field and index; browser stays sanitized',
    async (reason, change) => {
      const log = diagnosticLog();
      const { source, draft } = fixture();
      change(draft.facts[0]);
      const res = await handleInterpretRequest(
        request(source.pages[0].text),
        adapter({ facts: draft.facts, issues: [] }),
      );
      expect(res.status).toBe(502);
      expect(await res.json()).toEqual({
        error: {
          code: 'PROVIDER_EVIDENCE',
          message:
            'The provider returned an unsupported derived fact or evidence that does not match the source. No requirements were approved.',
          issues: [],
        },
      });
      expect(log).toHaveBeenCalledTimes(1);
      const logged = JSON.parse(log.mock.calls[0][1]);
      expect(logged.failures).toEqual([
        { source_index: 0, fact_index: 0, field: 'equipment', reason },
      ]);
      expect(logged.event_id).toMatch(/^[a-f0-9-]{36}$/);
      const serialized = JSON.stringify(log.mock.calls);
      for (const secret of [
        'private-credential',
        'private-model-name',
        'private fabricated excerpt',
        draft.facts[1].evidence.excerpt,
      ])
        expect(serialized).not.toContain(secret);
    },
  );

  it('reports every rejected fact and every failing rule without rewriting a derived origin', async () => {
    const log = diagnosticLog();
    const { source, draft } = fixture();
    const components = draft.facts.find((f) => f.field === 'components')!;
    components.origin = 'derived';
    components.evidence.excerpt = 'n_hexane normalized evidence';
    draft.facts.find((f) => f.field === 'outputs')!.origin = 'derived';
    await expect(
      interpretSources([source], adapter({ facts: draft.facts, issues: [] })),
    ).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
    expect(JSON.parse(log.mock.calls[0][1]).failures).toEqual([
      { source_index: 0, fact_index: 2, field: 'components', reason: 'excerpt_not_exact' },
      { source_index: 0, fact_index: 2, field: 'components', reason: 'derived_origin_forbidden' },
      { source_index: 0, fact_index: 3, field: 'outputs', reason: 'derived_origin_forbidden' },
    ]);
    expect(components.origin).toBe('derived');
  });

  it.each(['n_hexane = 77000 kg/h.'])(
    'rejects normalized or reformatted evidence: %s',
    async (excerpt) => {
      const { source, draft } = fixture();
      source.pages[0].text = 'n-Hexane = 77000 kg/h.';
      const fact = {
        ...draft.facts[10],
        component: 'n-Hexane',
        evidence: { ...draft.facts[10].evidence, excerpt },
      };
      await expect(
        interpretSources([source], adapter({ facts: [fact], issues: [] })),
      ).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
    },
  );

  it('requires matching text on the cited PDF page, not just somewhere in the document', async () => {
    const log = diagnosticLog();
    const { source, draft } = fixture();
    source.type = 'uploaded_document';
    source.pages = [
      { page: 1, text: 'Unrelated text' },
      { page: 2, text: draft.facts[0].evidence.excerpt },
    ];
    draft.facts[0].evidence.source_type = 'uploaded_document';
    draft.facts[0].evidence.page = 1;
    await expect(
      interpretSources([source], adapter({ facts: [draft.facts[0]], issues: [] })),
    ).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
    expect(JSON.parse(log.mock.calls[0][1]).failures[0].reason).toBe('excerpt_not_exact');
  });

  it.each(['unit', 'field', 'metadata'] as const)(
    'logs safe schema paths for invalid %s through the real adapter',
    async (variant) => {
      const log = diagnosticLog();
      const { source, draft } = fixture();
      const raw = structuredClone({ facts: draft.facts, issues: [] }) as unknown as {
        facts: Record<string, unknown>[];
        issues: unknown[];
        [key: string]: unknown;
      };
      if (variant === 'metadata') raw['private-credential'] = { model: 'private-model-name' };
      else raw.facts[0][variant] = 'private-invalid-value';
      const res = await handleInterpretRequest(request(source.pages[0].text), adapter(raw));
      expect(res.status).toBe(502);
      expect((await res.json()).error.code).toBe('PROVIDER_MALFORMED');
      const entry = JSON.parse(log.mock.calls[0][1]);
      expect(entry.stage).toBe('schema');
      expect(entry.failures[0].path).toBe(variant === 'metadata' ? '' : `facts.0.${variant}`);
      expect(JSON.stringify(log.mock.calls)).not.toMatch(/private-/);
    },
  );

  it('does not log diagnostics in production', async () => {
    vi.stubEnv('NODE_ENV', 'production');
    const log = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { source, draft } = fixture();
    draft.facts[0].origin = 'derived';
    await expect(
      interpretSources([source], adapter({ facts: draft.facts, issues: [] })),
    ).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
    expect(log).not.toHaveBeenCalled();
  });
});

describe('extract first, normalize locally', () => {
  it('preserves source component IDs, outputs, units and exact evidence through approval', async () => {
    const { source, draft, review } = fixture();
    for (const fact of draft.facts) {
      if (fact.component === 'n_hexane') fact.component = 'n-Hexane';
      if (fact.field === 'components') fact.value = 'methane, n-Hexane, water';
      if (fact.field === 'equipment') fact.value = 'three-phase separator';
      if (fact.field === 'topology')
        fact.value = 'one feed, one separator, gas, oil and water outlets';
      if (fact.field === 'outputs') fact.value = 'WATER, GAS and Oil';
      if (fact.field === 'feed_pressure') {
        fact.value = 20;
        fact.unit = 'bar_abs';
      }
      fact.evidence.excerpt = `${fact.component || ''} ${fact.field}: ${fact.value} ${fact.unit}.`;
    }
    source.pages[0].text = draft.facts.map((f) => f.evidence.excerpt).join('\n');
    const interpreted = await interpretSources(
      [source],
      adapter({ facts: draft.facts, issues: [] }),
    );
    expect(interpreted.draft.facts).toEqual(draft.facts);
    expect(blockers(interpreted.draft, review)).toEqual([]);
    const requirements = finalizeRequirements(interpreted.draft, review, 'now');
    expect(requirements.components).toEqual(['methane', 'n_hexane', 'water']);
    expect(requirements.feeds[0].state.component_mass_flow_kg_h['n_hexane']).toBe(77000);
    expect(requirements.feeds[0].state.pressure_Pa_abs).toBe(2000000);
    const audit = JSON.parse(requirements.provenance.source);
    expect(audit.interpretation.facts).toEqual(draft.facts);
    for (const field of ['equipment', 'topology', 'outputs', 'feed_pressure']) {
      const normalized = audit.normalized_values.find((f: Fact) => f.field === field);
      const original = draft.facts.find((f) => f.field === field)!;
      expect(normalized.evidence).toEqual(original.evidence);
      expect(normalized.original_value).toBe(original.value);
      expect(normalized.origin).toBe('derived');
      expect(normalized.derivation).toBe(
        field === 'feed_pressure'
          ? 'deterministic_unit_conversion'
          : 'deterministic_text_normalization',
      );
    }
  });

  it.each([
    ['equipment', 'three-phase separator and compressor'],
    ['topology', 'two feeds, one separator, gas, oil and water outlets'],
    ['outputs', 'gas, oil and water, solids'],
  ] as const)('does not erase unsupported %s during local normalization', (field, value) => {
    const { draft, review } = fixture();
    draft.facts.find((f) => f.field === field)!.value = value;
    expect(() => finalizeRequirements(draft, review, 'now')).toThrow('UNSUPPORTED CAPABILITY');
  });

  it('explains the extraction boundary instead of requesting provider-derived normalization', () => {
    expect(systemPrompt).toContain('n-Hexane stays n-Hexane, never n_hexane');
    expect(systemPrompt).toContain('Never return origin=derived');
    expect(systemPrompt).toContain('one contiguous, exact excerpt');
    expect(systemPrompt).toContain('unit conversion is application behavior after extraction');
  });
});
