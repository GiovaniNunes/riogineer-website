import { describe, expect, it } from 'vitest';
import { anchorEvidence } from '../src/lib/digital-engineer/interpretation/anchoring';
import { interpretSources } from '../src/lib/digital-engineer/interpretation/service';
import { naturalFixture } from './natural-specification-fixture';

describe('deterministic evidence location', () => {
  it.each([
    ['n-Hexane = 77000 kg/h.', 'n-Hexane =\n77000  kg/h.'],
    ['Components:\n• Methane\n• n–Hexane\n• Water', 'Components: Methane, n-Hexane, Water'],
    ['Components:\n- Methane\n- n-Hexane\n- Water', 'Components: Methane; n-Hexane; Water'],
    ['Temperature: −40 degC', 'Temperature: -40 degC'],
    ['Gas recovery: 0.05', 'Gas recovery 0.05'],
  ])('anchors presentation differences to untouched text: %s', (text, candidate) => {
    const result = anchorEvidence(text, candidate);
    expect(result).not.toHaveProperty('reason');
    if ('excerpt' in result) {
      expect(text.slice(result.start, result.end)).toBe(result.excerpt);
      expect(result.excerpt).toBe(text.endsWith('.') ? text.slice(0, -1) : text);
    }
  });

  it.each([
    ['Methane: 22000 kg/h', 'Methane: 22001 kg/h'],
    ['Methane: 22000 kg/h', 'Methane: 22000 kg/s'],
    ['Methane: 22000 kg/h', 'Methane: 22000 kg'],
    ['Methane: 22000 kg/h', 'Ethane: 22000 kg/h'],
    ['n-Hexane: 77000 kg/h', 'n_hexane: 77000 kg/h'],
    ['Water: gas 0.0, oil 0.05, water 0.95', 'Water: gas 0.0, water 0.05, oil 0.95'],
    ['Temperature: -40 degC', 'Temperature: 40 degC'],
    ['Temperature: +40 degC', 'Temperature: -40 degC'],
    ['Temperature: - 40 degC', 'Temperature: 40 degC'],
    ['Recovery: 0.05', 'Recovery: 0.5'],
    ['Recovery: -.05', 'Recovery: .05'],
    ['Ratio: 1:2', 'Ratio: 1 2'],
    ['Flow: 22,000 kg/h', 'Flow: 22.000 kg/h'],
    ['Cp: 2200 J/(kg K)', 'Cp: 2200 kJ/(kg K)'],
    ['Pressure: 20 bar abs', 'Pressure: 20 bar gauge'],
    ['Equipment: SEP-01', 'Equipment: SEP-02'],
    ['Flow: 1e-3 kg/h', 'Flow: 1e3 kg/h'],
    ['Flow: 122000 kg/h', '22000 kg/h'],
    ['Components: methane, water, oil', 'Components: methane, oil'],
  ])('rejects engineering changes: %s / %s', (text, candidate) => {
    expect(anchorEvidence(text, candidate)).toEqual({ reason: 'excerpt_not_exact' });
  });

  it.each([
    ['Methane: 22000 kg/h\nMethane: 22000 kg/h', 'Methane: 22000 kg/h'],
    ['Methane: 22000 kg/h\nMethane:\n22000  kg/h', 'Methane: 22000 kg/h'],
  ])('rejects duplicate exact and formatting-equivalent anchors', (text, candidate) => {
    expect(anchorEvidence(text, candidate)).toEqual({ reason: 'excerpt_ambiguous' });
  });

  it('reproduces components fact index 2 formatting failure through the service', async () => {
    // Constructed reproduction: the historical provider excerpt was not captured.
    const { source, draft } = naturalFixture();
    const exact = 'Components:\n• methane\n• n_hexane\n• water';
    source.pages[0].text =
      '  \n' +
      source.pages[0].text.replace('Components: methane, n_hexane, water.', exact) +
      '\n  ';
    const original = structuredClone(source);
    const candidate = draft.facts[2].evidence.excerpt;
    expect(source.pages[0].text).not.toContain(candidate);
    const result = await interpretSources([source], {
      name: 'test-only',
      interpret_specification: async () => ({
        facts: draft.facts,
        issues: draft.issues.map((issue) => ({
          kind: issue.kind,
          field: issue.field,
          component: issue.component,
          message: issue.message,
          evidence: issue.evidence,
        })),
      }),
    });
    expect(source).toEqual(original);
    expect(result.draft.sources[0].pages).toEqual(original.pages);
    expect(result.draft.facts[2].evidence).toMatchObject({
      excerpt: exact,
      provider_excerpt: candidate,
    });
    for (const fact of result.draft.facts)
      expect(source.pages[0].text).toContain(fact.evidence.excerpt);
    expect(draft.facts[2].evidence.excerpt).toBe(candidate);
  });

  it('anchors issue evidence as well and preserves its candidate', async () => {
    const { source, draft } = naturalFixture();
    draft.issues[0].evidence!.excerpt = draft.issues[0].evidence!.excerpt.replace(' is ', '  is\n');
    const result = await interpretSources([source], {
      name: 'test-only',
      interpret_specification: async () => ({
        facts: draft.facts,
        issues: draft.issues.map((issue) => ({
          kind: issue.kind,
          field: issue.field,
          component: issue.component,
          message: issue.message,
          evidence: issue.evidence,
        })),
      }),
    });
    expect(result.draft.issues[0].evidence?.provider_excerpt).toBe(
      draft.issues[0].evidence?.excerpt,
    );
    expect(source.pages[0].text).toContain(result.draft.issues[0].evidence!.excerpt);
  });
});
