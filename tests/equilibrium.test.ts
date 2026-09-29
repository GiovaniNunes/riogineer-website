import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { describe, it, expect } from 'vitest';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
import { streamColumns, streamRows } from '../src/lib/digital-engineer/stream-table';
import { graphLayout } from '../src/lib/digital-engineer/pfd-layout';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '../src/lib/digital-engineer/workflow';
import m5 from '../contracts/examples/milestone-5-requirements.json';
import m6 from '../contracts/examples/milestone-6-requirements.json';
const data = JSON.parse(
  execFileSync(
    process.env.ENGINE_PYTHON || resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      'import json; from riogineer_engine.core import build_flowsheet, calculate; from riogineer_engine.milestone9 import requirements; r=requirements(); f=build_flowsheet(r); print(json.dumps(dict(requirements=r, flowsheet=f, results=calculate(f))))',
    ],
    { cwd: resolve('engine'), encoding: 'utf8' },
  ),
);
const f = flowsheetSchema.parse(data.flowsheet);
const r = resultsSchema.parse(data.results);
const draft = JSON.stringify(data.requirements);
describe('M9 contracts and cross-representation identity', () => {
  it('reads the distinct versioned contracts and rejects false energy/property claims', () => {
    expect(engineeringRequirementsSchema.parse(data.requirements).schema_version).toBe('1.4');
    expect(f.schema_version).toBe('1.5');
    expect(r.schema_version).toBe('1.6');
    for (const mutate of [
      (v: typeof data.results) => (v.equipment[0].duty_W = 0),
      (v: typeof data.results) => (v.streams.VAPOR_PRODUCT.enthalpy_flow_W = 0),
      (v: typeof data.results) => (v.equipment[0].thermodynamics.beta = 2),
    ]) {
      const bad = structuredClone(data.results);
      mutate(bad);
      expect(resultsSchema.safeParse(bad).success).toBe(false);
    }
  });
  it('joins process properties by stable identity and reconstructs x/y independently', () => {
    const reordered = structuredClone(f);
    reordered.streams.reverse();
    reordered.connections.reverse();
    const columns = streamColumns(reordered, r);
    expect(columns.map((c) => c.stream.id)).toEqual([
      'HYDROCARBON_FEED',
      'LIQUID_PRODUCT',
      'VAPOR_PRODUCT',
    ]);
    const thermo = data.results.equipment[0].thermodynamics;
    for (const c of columns) {
      expect(c.connection.stream_id).toBe(c.stream.id);
      expect(c.result).toBe(r.streams[c.stream.id]);
      if (c.stream.id !== 'HYDROCARBON_FEED')
        for (const id of f.components)
          expect(c.properties!.molar_composition.value![id]).toBeCloseTo(
            thermo[c.stream.id === 'VAPOR_PRODUCT' ? 'y' : 'x'][id],
            12,
          );
      for (const key of [
        'density',
        'gas_volumetric_flow',
        'oil_volumetric_flow',
        'water_volumetric_flow',
      ] as const)
        expect(c.properties![key].value).toBeNull();
    }
    expect(
      streamRows(f)
        .find((row) => row.label === 'methane — component molar flow')!
        .value(columns[0]),
    ).toBe(500);
    expect(graphLayout(f).positions).toEqual(graphLayout(reordered).positions);
  });
  it('clears M9 thermodynamic results on case changes and rejects mismatched responses', () => {
    let state = initialWorkflow(draft);
    state = workflowReducer(state, { type: 'validated', revision: 0 });
    state = workflowReducer(state, { type: 'built', revision: 0, flowsheet: f });
    state = workflowReducer(state, { type: 'calculated', revision: 0, results: r });
    expect(resultsAreCurrent(state)).toBe(true);
    const layout = workflowReducer(state, { type: 'layout' });
    expect(layout.results).toBe(r);
    expect(resultsAreCurrent(layout)).toBe(true);
    for (const other of [m5, m6]) {
      const next = workflowReducer(state, { type: 'edit', draft: JSON.stringify(other) });
      expect(next.results).toBeNull();
      expect(next.flowsheet).toBeNull();
      expect(next.validated).toBe(false);
      const back = workflowReducer(next, { type: 'edit', draft });
      expect(back.results).toBeNull();
    }
    const edited = workflowReducer(state, {
      type: 'edit',
      draft: draft.replace('300000', '360000'),
    });
    expect(resultsAreCurrent(edited)).toBe(false);
    expect(streamColumns(f, { ...r, input_sha256: 'a'.repeat(64) }).every((c) => !c.result)).toBe(
      true,
    );
  });
});
