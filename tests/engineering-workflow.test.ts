import { describe, expect, it } from 'vitest';
import {
  initialWorkflow,
  workflowReducer as reduce,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
import {
  referenceRequirements as requirements,
  referenceFlowsheet as flowsheet,
  referenceResults as results,
} from './engine-fixture';
function completed() {
  let s = initialWorkflow(JSON.stringify(requirements));
  s = reduce(s, { type: 'validated', revision: 0 });
  s = reduce(s, { type: 'built', revision: 0, flowsheet });
  return reduce(s, { type: 'calculated', revision: 0, results });
}
describe('web engineering state machine', () => {
  it('requires the validated model before a result is current', () => {
    expect(resultsAreCurrent(initialWorkflow('{}'))).toBe(false);
    expect(resultsAreCurrent(completed())).toBe(true);
  });
  it('marks previous results stale immediately on a numerical edit', () => {
    const edited = structuredClone(requirements);
    edited.feeds[0].state.temperature_K += 1;
    const s = reduce(completed(), { type: 'edit', draft: JSON.stringify(edited) });
    expect(s.results).toEqual(results);
    expect(s.validated).toBe(false);
    expect(s.flowsheet).toBeNull();
    expect(resultsAreCurrent(s)).toBe(false);
  });
  it('preserves current results for layout and formatting only', () => {
    const s = reduce(completed(), { type: 'layout' });
    expect(resultsAreCurrent(s)).toBe(true);
    expect(
      resultsAreCurrent(reduce(s, { type: 'edit', draft: JSON.stringify(requirements, null, 4) })),
    ).toBe(true);
  });
  it('ignores responses from a request preceding an input edit', () => {
    const s = reduce(completed(), { type: 'edit', draft: '{}' });
    expect(reduce(s, { type: 'calculated', revision: 0, results })).toEqual(s);
    expect(reduce(s, { type: 'built', revision: 0, flowsheet })).toEqual(s);
    expect(reduce(s, { type: 'validated', revision: 0 })).toEqual(s);
  });
  it('rejects results from a different input/implementation fingerprint', () => {
    const s = reduce(completed(), {
      type: 'calculated',
      revision: 0,
      results: { ...results, input_sha256: 'a'.repeat(64) },
    });
    expect(s.error).toContain('different engine version');
    expect(resultsAreCurrent(s)).toBe(false);
  });
  it('never labels retained results current after an error', () => {
    const s = reduce(completed(), { type: 'error', revision: 0, error: 'Engine offline' });
    expect(resultsAreCurrent(s)).toBe(false);
    expect(s.results).toEqual(results);
  });
});
