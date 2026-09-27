import { afterEach, describe, expect, it, vi } from 'vitest';
import reference from '../contracts/examples/requirements.json';
import {
  naturalFixture,
  componentFieldNames,
  exclusionText,
} from './natural-specification-fixture';
import {
  emptyReview,
  factKey,
  type Fact,
} from '../src/lib/digital-engineer/interpretation/contracts';
import {
  blockers,
  effectiveValues,
  finalizeRequirements,
  reviewFields,
} from '../src/lib/digital-engineer/interpretation/review';
import { interpretSources } from '../src/lib/digital-engineer/interpretation/service';
import { reviewCoverage } from '../src/lib/digital-engineer/interpretation/validation';
import {
  componentIdentifier,
  registeredComponentIds,
} from '../src/lib/digital-engineer/interpretation/components';

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});
async function interpretNatural(data = naturalFixture()) {
  return interpretSources([data.source], {
    name: 'test-only',
    interpret_specification: async () => ({
      facts: data.draft.facts,
      issues: data.draft.issues.map((issue) => ({
        kind: issue.kind,
        field: issue.field,
        component: issue.component,
        message: issue.message,
        ...(issue.evidence ? { evidence: issue.evidence } : {}),
      })),
    }),
  });
}

describe('natural-language component identity and scope', () => {
  it('reproduces all 15 old missing joins and populates all explicit inputs without corrections', async () => {
    const input = naturalFixture();
    // Before: canonical basis + exact-string source fact keys missed every one of these rows.
    const oldKeys = new Set(input.draft.facts.map((f) => `${f.field}:${f.component}`));
    expect(
      reference.components
        .flatMap((component) => componentFieldNames.map((field) => `${field}:${component}`))
        .filter((key) => !oldKeys.has(key)),
    ).toHaveLength(15);
    const { draft } = await interpretNatural(input);
    expect(draft.facts).toEqual(input.draft.facts);
    const fields = reviewFields(draft, input.review).filter((f) => f.component);
    const values = effectiveValues(draft, input.review);
    expect(fields).toHaveLength(15);
    expect(fields.every((f) => typeof values.get(factKey(f))?.value === 'number')).toBe(true);
    expect(blockers(draft, input.review)).toEqual([]);
    expect(input.review.corrections).toEqual([]);
    const requirements = finalizeRequirements(draft, input.review, 'now');
    expect(requirements.components).toEqual(reference.components);
    expect(requirements.feeds[0].state).toEqual(reference.feeds[0].state);
    expect(requirements.equipment[0].parameters).toEqual(reference.equipment[0].parameters);
    const audit = JSON.parse(requirements.provenance.source);
    expect(audit.interpretation.facts).toEqual(draft.facts);
    expect(
      audit.interpretation.issues.filter((i: { kind: string }) => i.kind === 'scope_exclusion'),
    ).toHaveLength(3);
    for (const fact of draft.facts.filter((f) => f.component)) {
      const value = audit.normalized_values.find((v: Fact) => factKey(v) === factKey(fact));
      expect(value.component_mapping).toEqual({
        source_name: fact.component,
        registered_id: componentIdentifier(fact.component!),
      });
      expect(value.original_component).toBe(fact.component);
      expect(value.evidence).toEqual(fact.evidence);
      expect(value.value).toBe(fact.value); // includes explicitly zero recoveries
    }
  });

  it('maps arbitrary registered component names using the same algorithm, without reference-case values', () => {
    const { draft, review } = naturalFixture();
    const replacements: Record<string, string> = {
      Methane: 'Ethane',
      'n-Hexane': 'n-Heptane',
      Water: 'Brine',
    };
    draft.facts.find((f) => f.field === 'components')!.value = 'ETHANE, n_heptane, brine';
    for (const fact of draft.facts)
      if (fact.component) {
        fact.component = replacements[fact.component];
        if (fact.field === 'component_flow') fact.value = 17;
        if (fact.field === 'cp') fact.value = 1234;
      }
    expect(blockers(draft, review)).toEqual([]);
    const req = finalizeRequirements(draft, review, 'now');
    expect(req.components).toEqual(['ethane', 'n_heptane', 'brine']);
    expect(req.feeds[0].state.component_mass_flow_kg_h).toEqual({
      ethane: 17,
      n_heptane: 17,
      brine: 17,
    });
    expect(req.equipment[0].parameters.caloric_model.cp_J_kg_K).toEqual({
      ethane: 1234,
      n_heptane: 1234,
      brine: 1234,
    });
  });

  it('does not register an orphan, deduplicate colliding basis entries or fuzzy-match chemical names', () => {
    const { draft, review } = naturalFixture();
    draft.facts.find((f) => f.field === 'cp')!.component = 'Ethane';
    expect(blockers(draft, review).join()).toContain('absent from the component basis');
    draft.facts.find((f) => f.field === 'components')!.value = 'n-Hexane, n_hexane';
    expect(blockers(draft, review).join()).toContain('unique component IDs');
    expect(registeredComponentIds('Methane, methanol, CH4')).toEqual([
      'methane',
      'methanol',
      'ch4',
    ]);
    expect(componentIdentifier('n-Hexane!')).toBe('n-Hexane!');
  });

  it('retains alias conflicts and resolves them only with an explicit correction and note', () => {
    const { draft, review } = naturalFixture();
    const fact = draft.facts.find((f) => f.field === 'cp' && f.component === 'Methane')!;
    draft.facts.push({ ...fact, component: 'methane', value: 2300 });
    expect(blockers(draft, review).join()).toContain('CONFLICT DETECTED: cp:methane');
    review.corrections.push({
      field: 'cp',
      component: 'METHANE',
      value: 2200,
      unit: fact.unit,
      note: 'Select source value',
    });
    expect(blockers(draft, review).join()).toContain('resolution note');
    review.resolutions['conflict:cp:methane'] =
      'Keep the explicitly reviewed original source value.';
    expect(blockers(draft, review)).toEqual([]);
    expect(
      finalizeRequirements(draft, review, 'now').equipment[0].parameters.caloric_model.cp_J_kg_K
        .methane,
    ).toBe(2200);
  });

  it('does not report a stale source-name missing issue after its canonical field is populated', () => {
    const { draft, review } = naturalFixture();
    draft.issues.push({
      id: 'missing',
      kind: 'missing',
      field: 'component_flow',
      component: 'METHANE',
      message: 'Not found',
    });
    expect(blockers(draft, review)).toEqual([]);
  });

  it('does not invent omitted data or auto-accept explicitly proposed assumptions', async () => {
    const input = naturalFixture();
    input.draft.facts = input.draft.facts.filter(
      (f) => !(f.field === 'cp' && f.component === 'Water'),
    );
    input.draft.facts.find((f) => f.field === 'cp' && f.component === 'Methane')!.origin =
      'assumed';
    const { draft } = await interpretNatural(input);
    const coverage = reviewCoverage(draft);
    expect(
      coverage.component_fields.find((f) => f.component_index === 2 && f.field === 'cp')?.state,
    ).toBe('not_returned_for_component');
    expect(
      coverage.component_fields.find((f) => f.component_index === 0 && f.field === 'cp')?.state,
    ).toBe('awaiting_assumption_review');
    expect(blockers(draft, input.review).join()).toContain('water — Constant heat capacity');
    expect(effectiveValues(draft, emptyReview()).has('cp:water')).toBe(false);
  });

  it('logs successful field coverage and alias mapping without source text, values or provider names', async () => {
    vi.stubEnv('NODE_ENV', 'development');
    const log = vi.spyOn(console, 'info').mockImplementation(() => {});
    await interpretNatural();
    expect(log).toHaveBeenCalledTimes(1);
    const report = JSON.parse(log.mock.calls[0][1]);
    expect(report.component_fields).toHaveLength(15);
    expect(
      report.component_fields.every(
        (f: { state: string; identity_mapped: boolean }) =>
          f.state === 'populated' && f.identity_mapped,
      ),
    ).toBe(true);
    expect(report.orphan_fact_indices).toEqual([]);
    expect(report.scope_exclusions).toBe(3);
    expect(report.unsupported_requests).toBe(0);
    expect(JSON.stringify(report)).not.toMatch(
      /Methane|n-Hexane|77000|test-only|source_id|excerpt/,
    );
  });

  it('keeps successful extraction diagnostics silent in production', async () => {
    vi.stubEnv('NODE_ENV', 'production');
    const info = vi.spyOn(console, 'info').mockImplementation(() => {});
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    await interpretNatural();
    expect(info).not.toHaveBeenCalled();
    expect(warn).not.toHaveBeenCalled();
  });

  it.each(exclusionText.split('\n'))(
    'retains the cited exclusion without unsupported warnings: %s',
    async (excerpt) => {
      const input = naturalFixture();
      input.draft.issues = input.draft.issues.filter((i) => i.evidence?.excerpt === excerpt);
      const { draft } = await interpretNatural(input);
      expect(draft.issues[0].evidence?.excerpt).toBe(excerpt);
      expect(blockers(draft, input.review)).toEqual([]);
    },
  );

  it.each([
    'Perform separator sizing.',
    'Separator sizing is not outside the requested calculation scope.',
    'Separator sizing is outside the requested calculation scope, but size this vessel.',
    'Separator sizing is outside the requested calculation scope. Also size this vessel.',
  ])('rejects incorrectly labelled exclusions: %s', async (excerpt) => {
    const input = naturalFixture();
    input.source.pages[0].text += '\n' + excerpt;
    input.draft.issues = [
      { ...input.draft.issues[0], evidence: { ...input.draft.issues[0].evidence!, excerpt } },
    ];
    await expect(interpretNatural(input)).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
  });

  it('rejects fabricated exclusion evidence', async () => {
    const input = naturalFixture();
    input.source.pages[0].text = input.source.pages[0].text.replace(exclusionText, '');
    await expect(interpretNatural(input)).rejects.toMatchObject({ code: 'PROVIDER_EVIDENCE' });
  });

  it.each([
    'Predict rigorous vapor-oil-water equilibrium.',
    'Perform separator sizing.',
    'Calculate geometry-based separation efficiency.',
  ])('keeps affirmative requests blocked even alongside valid exclusions: %s', async (message) => {
    const input = naturalFixture();
    input.source.pages[0].text += '\n' + message;
    input.draft.issues.push({
      id: 'request',
      kind: 'unsupported',
      field: null,
      component: null,
      message,
    });
    const { draft } = await interpretNatural(input);
    input.review.resolutions[draft.issues.at(-1)!.id] = 'Ignore it';
    expect(() => finalizeRequirements(draft, input.review, 'now')).toThrow(
      'UNSUPPORTED CAPABILITY',
    );
  });
});
