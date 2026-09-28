import { expect, it, vi } from 'vitest';
import { requirements, flowsheet, results } from './compression-fixture';
import {
  networkRequirementsSchema,
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import { handleEngineeringRequest } from '../src/lib/digital-engineer/api';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
import { streamColumns } from '../src/lib/digital-engineer/stream-table';
import { referenceRequirements } from './engine-fixture';
import { networkRequirements } from './network-fixture';
it('versions compressor contracts explicitly while preserving earlier readers', () => {
  expect(networkRequirementsSchema.safeParse(requirements).success).toBe(false);
  expect(
    engineeringRequirementsSchema.safeParse({ ...requirements, schema_version: '1.2' }).success,
  ).toBe(false);
  expect(flowsheetSchema.safeParse({ ...flowsheet, schema_version: '1.3' }).success).toBe(false);
  expect(resultsSchema.safeParse({ ...results, schema_version: '1.3' }).success).toBe(false);
});
it('forwards the actual compression case through every deterministic API boundary', async () => {
  for (const [operation, input, output] of [
    ['validate-requirements', requirements, { requirements, validation: flowsheet.validation }],
    ['build-flowsheet', requirements, flowsheet],
    ['calculate', flowsheet, results],
  ] as const) {
    const fetcher = vi.fn().mockResolvedValue(Response.json(output));
    const request = new Request(`http://localhost:3000/api/digital-engineer/${operation}`, {
      method: 'POST',
      headers: { origin: 'http://localhost:3000', 'content-type': 'application/json' },
      body: JSON.stringify(input),
    });
    const response = await handleEngineeringRequest(request, operation, fetcher);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual(output);
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual(input);
  }
});
it('retains structured stream objects across calculation/layout and clears cross-case artifacts', () => {
  let state = initialWorkflow(JSON.stringify(requirements));
  state = workflowReducer(state, { type: 'validated', revision: 0 });
  state = workflowReducer(state, { type: 'built', revision: 0, flowsheet });
  for (const action of [
    { type: 'calculated', revision: 0, results } as const,
    { type: 'layout' } as const,
    { type: 'calculated', revision: 0, results } as const,
  ]) {
    state = workflowReducer(state, action);
    expect(resultsAreCurrent(state)).toBe(true);
    expect(state.flowsheet!.streams).toBe(flowsheet.streams);
    for (const col of streamColumns(state.flowsheet!, state.results))
      expect(col.result).toBe(results.streams[col.stream.id]);
  }
  for (const draft of [referenceRequirements, networkRequirements]) {
    const changed = workflowReducer(state, { type: 'edit', draft: JSON.stringify(draft) });
    expect(changed.results).toBeNull();
    expect(changed.flowsheet).toBeNull();
    expect(changed.validated).toBe(false);
  }
});
