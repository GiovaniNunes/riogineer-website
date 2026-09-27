import { describe, expect, it } from 'vitest';
import {
  normalizeTopology,
  singleSeparatorTopology,
} from '../src/lib/digital-engineer/interpretation/topology';
import { blockers, normalize, sameValue } from '../src/lib/digital-engineer/interpretation/review';
import { emptyReview } from '../src/lib/digital-engineer/interpretation/contracts';
import { naturalFixture, naturalSpecification } from './natural-specification-fixture';
import { interpretSources } from '../src/lib/digital-engineer/interpretation/service';

export const reportedTopology =
  'The process shall comprise one feed stream entering one three-phase separator.';

const supported = [
  reportedTopology,
  'One feed stream enters a three-phase separator.',
  'A single feed flows into a single three phase separator with three outlets: gas, oil and water.',
  '1 feed -> 1 three-phase separator -> gas + oil + water',
  'one feed → one three-phase separator → water / oil / gas',
  'One feed, one separator, gas, oil and water outlets',
  'One three-phase separator receives one feed stream with gas, oil and water outlets.',
  'The process consists of one feed stream connected to one three-phase separator. The separator has three outlets: gas, oil and water.',
  'one feed entering one separator; gas outlet, oil outlet and water outlet',
];
const unsupported = [
  'The process shall comprise two feed streams entering one three-phase separator.',
  'One feed and an additional feed entering one three-phase separator with gas, oil and water outlets.',
  'One feed stream entering two three-phase separators with gas, oil and water outlets.',
  'One feed entering one separator and an additional separator with gas, oil and water outlets.',
  'One feed entering one separator with gas, oil and water outlets and a recycle.',
  'One feed entering one separator with gas, oil, water and solids outlets.',
  'One feed entering one separator with gas, oil and water outlets. Recycle gas to the feed.',
  'One feed entering one two-phase separator with gas, oil and water outlets.',
  'One feed entering one separator with gas, oil, oil outlets.',
  'One feed entering one separator with gas and oil outlets.',
  'One feed entering one separator with four outlets: gas, oil, water, solids.',
  'One feed does not enter one three-phase separator.',
  'One separator -> one feed -> gas + oil + water',
  'One feed entering one separator with gas, oil and water outlets through a compressor.',
];
describe('single separator topology grammar', () => {
  it.each(supported)('recognizes equivalent supported wording: %s', (text) => {
    expect(normalizeTopology(text, 'gas, oil and water')).toBe(singleSeparatorTopology);
    const { draft } = naturalFixture();
    draft.facts.find((f) => f.field === 'topology')!.value = text;
    expect(blockers(draft, emptyReview())).toEqual([
      'Accept the development model and its limitations.',
    ]);
  });
  it.each(unsupported)('keeps the complete unsupported topology blocked: %s', (text) => {
    expect(normalizeTopology(text, 'gas, oil and water')).toBe(text);
    const { draft } = naturalFixture();
    draft.facts.find((f) => f.field === 'topology')!.value = text;
    expect(blockers(draft, emptyReview()).some((e) => e.includes('exactly one feed'))).toBe(true);
  });
  it.each([undefined, 'gas, oil', 'gas, oil, water, solids', 'gas, oil, oil'])(
    'does not invent unspecified outlets: %s',
    (outputs) => {
      expect(normalizeTopology(reportedTopology, outputs)).toBe(reportedTopology);
    },
  );
  it('normalizes the reported sentence with separately evidenced outlets without rewriting facts', async () => {
    const { source, draft } = naturalFixture();
    source.pages[0].text = naturalSpecification.replace(
      'Topology: one feed, one separator, gas, oil and water outlets.',
      reportedTopology,
    );
    const topology = draft.facts.find((f) => f.field === 'topology')!;
    topology.value = reportedTopology;
    topology.evidence.excerpt = reportedTopology;
    const original = structuredClone(topology);
    const result = await interpretSources([source], {
      name: 'test-only',
      interpret_specification: async () => ({ facts: draft.facts, issues: [] }),
    });
    const stored = result.draft.facts.find((f) => f.field === 'topology')!;
    const outputs = result.draft.facts.find((f) => f.field === 'outputs')!;
    expect(stored).toEqual(original);
    expect(normalize(stored, outputs).value).toBe(singleSeparatorTopology);
    expect(
      sameValue(
        stored,
        { ...stored, value: 'one feed -> one separator -> gas + oil + water' },
        outputs,
      ),
    ).toBe(true);
    expect(blockers(result.draft, emptyReview())).toEqual([
      'Accept the development model and its limitations.',
    ]);
  });
  it('does not erase provider unsupported issues or contradictory topology facts', () => {
    const { draft } = naturalFixture();
    draft.facts.find((f) => f.field === 'topology')!.value = reportedTopology;
    draft.facts.push({
      ...draft.facts.find((f) => f.field === 'topology')!,
      value: unsupported[0],
    });
    draft.issues.push({
      id: 'recycle',
      kind: 'unsupported',
      field: 'topology',
      component: null,
      message: 'Requested recycle',
    });
    expect(blockers(draft, emptyReview()).some((e) => e.includes('CONFLICT'))).toBe(true);
    expect(blockers(draft, emptyReview()).some((e) => e.includes('Requested recycle'))).toBe(true);
  });
});
