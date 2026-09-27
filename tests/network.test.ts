import { describe, expect, it, vi } from 'vitest';
import {
  networkRequirements as requirements,
  networkFlowsheet as flowsheet,
  networkResults as results,
} from './network-fixture';
import {
  engineeringRequirementsSchema,
  requirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import { handleEngineeringRequest } from '../src/lib/digital-engineer/api';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
import { streamColumns, streamRows } from '../src/lib/digital-engineer/stream-table';
import { streamLabel } from '../src/lib/digital-engineer/stream-label';
import { graphLayout } from '../src/lib/digital-engineer/pfd-layout';

function request(body: unknown) {
  return new Request('http://localhost:3000/api/digital-engineer/build-flowsheet', {
    method: 'POST',
    headers: { origin: 'http://localhost:3000', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
describe('Milestone 4 deterministic network integration', () => {
  it('accepts explicitly versioned graph documents without broadening interpretation requirements', () => {
    expect(engineeringRequirementsSchema.parse(requirements)).toEqual(requirements);
    expect(requirementsSchema.safeParse(requirements).success).toBe(false);
    expect(flowsheetSchema.parse(flowsheet).streams).toHaveLength(7);
    expect(resultsSchema.parse(results).streams.OIL_A.mass_flow_kg_h).toBe(46530);
    for (const schema_version of ['1.0', '1.1'])
      expect(flowsheetSchema.safeParse({ ...flowsheet, schema_version }).success).toBe(false);
    expect(resultsSchema.safeParse({ ...results, schema_version: '1.1' }).success).toBe(false);
  });
  it('forwards numbered graph builds and seven-stream results unchanged', async () => {
    const built = await handleEngineeringRequest(
      request(requirements),
      'build-flowsheet',
      vi.fn().mockResolvedValue(Response.json(flowsheet)),
    );
    expect(built.status).toBe(200);
    expect(await built.json()).toEqual(flowsheet);
    const calculated = await handleEngineeringRequest(
      request(flowsheet),
      'calculate',
      vi.fn().mockResolvedValue(Response.json(results)),
    );
    expect(calculated.status).toBe(200);
    expect(await calculated.json()).toEqual(results);
    const wrong = structuredClone(results);
    delete wrong.streams.OIL_A;
    expect(
      (
        await handleEngineeringRequest(
          request(flowsheet),
          'calculate',
          vi.fn().mockResolvedValue(Response.json(wrong)),
        )
      ).status,
    ).toBe(502);
  });
  it('preserves original numbered objects through repeat calculation, layout and all table joins', () => {
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
      const columns = streamColumns(state.flowsheet!, state.results);
      expect(columns.map((c) => streamLabel(c.stream))).toEqual([
        '1 — FEED',
        '2 — GAS',
        '3 — OIL',
        '4 — WATER',
        '5 — OIL_A',
        '6 — OIL_B',
        '7 — OIL',
      ]);
      columns.forEach((c) => {
        expect(c.stream).toBe(flowsheet.streams.find((s) => s.id === c.stream.id));
        expect(c.result).toBe(results.streams[c.stream.id]);
      });
      expect(columns.map((c) => c.result!.mass_flow_kg_h)).toEqual([
        110000, 22000, 77550, 10450, 46530, 31020, 77550,
      ]);
    }
    const rows = streamRows(flowsheet),
      columns = streamColumns(flowsheet, results);
    expect(columns.map((c) => rows.find((r) => r.label === 'Density')!.value(c))).toEqual(
      Array(7).fill(null),
    );
    expect(rows.find((r) => r.label === 'methane — component mass flow')!.value(columns[4])).toBe(
      0,
    );
    expect(
      streamColumns(flowsheet, { ...results, input_sha256: '0'.repeat(64) }).every(
        (c) => !c.result,
      ),
    ).toBe(true);
  });
  it('lays out all nodes from connectivity without mutating or depending on array order', () => {
    const copy = structuredClone(flowsheet),
      before = structuredClone(copy);
    const a = graphLayout(copy);
    expect(copy).toEqual(before);
    for (const key of ['equipment', 'boundaries', 'connections', 'streams'] as const)
      copy[key].reverse();
    const b = graphLayout(copy);
    expect(b.positions).toEqual(a.positions);
    expect([...a.positions.keys()].sort()).toEqual([
      'FEED',
      'GAS_SINK',
      'MIX_1',
      'OIL_SINK',
      'SEP_1',
      'SPLIT_1',
      'WATER_SINK',
    ]);
    for (const c of flowsheet.connections) {
      expect(a.point(c.source.owner_id, c.source.port_id).x).toBeLessThan(
        a.point(c.target.owner_id, c.target.port_id).x,
      );
    }
  });
  it('keeps unsupported property status and units strict in network results', () => {
    if (results.schema_version !== '1.2') throw new Error('Expected network fixture');
    const bad = structuredClone(results);
    Object.assign(bad.streams.OIL_A.properties.density, { value: 0 });
    expect(resultsSchema.safeParse(bad).success).toBe(false);
    expect(results.execution.equipment_order).toEqual(['SEP_1', 'SPLIT_1', 'MIX_1']);
    expect(results.equipment.every((e) => e.mass_balance.total_residual_kg_h === 0)).toBe(true);
  });
});
