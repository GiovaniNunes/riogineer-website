import { describe, expect, it } from 'vitest';
import { referenceFlowsheet as flowsheet, referenceResults as results } from './engine-fixture';
import { streamColumns, streamRows } from '../src/lib/digital-engineer/stream-table';
import { resultsSchema, flowsheetSchema } from '../src/lib/digital-engineer/contracts';

describe('numbered material streams and table projection', () => {
  it('shares stream objects and joins results through stable IDs regardless of array order', () => {
    const f = structuredClone(flowsheet);
    f.streams.reverse();
    f.connections.reverse();
    const columns = streamColumns(f, results);
    expect(
      columns.map((c) => 'engineering_number' in c.stream && c.stream.engineering_number),
    ).toEqual([1, 2, 3, 4]);
    expect(columns.map((c) => c.result?.mass_flow_kg_h)).toEqual([110000, 22000, 77550, 10450]);
    columns.forEach((c) => {
      expect(c.stream).toBe(f.streams.find((s) => s.id === c.stream.id));
      expect(c.connection.stream_id).toBe(c.stream.id);
      expect(c.result).toBe(results.streams[c.stream.id]);
    });
    for (const component of f.components) {
      for (const c of columns) {
        expect(
          streamRows(f)
            .find((r) => r.label === `${component} — component mass flow`)!
            .value(c),
        ).toBe(c.result!.component_mass_flow_kg_h[component]);
        expect(
          streamRows(f)
            .find((r) => r.label === `${component} — mass fraction`)!
            .value(c),
        ).toBe(c.result!.component_mass_fractions![component]);
      }
    }
    expect(streamRows(f).every((r) => r.unit.length > 0)).toBe(true);
  });
  it('distinguishes unsupported properties from real zero and never fills stale results', () => {
    const columns = streamColumns(flowsheet, results);
    const rows = streamRows(flowsheet);
    expect(rows.find((r) => r.label === 'water — component mass flow')!.value(columns[1])).toBe(0);
    for (const name of [
      'Density',
      'Gas volumetric flow',
      'Oil volumetric flow',
      'Water volumetric flow',
    ])
      expect(columns.map((c) => rows.find((r) => r.label === name)!.value(c))).toEqual([
        null,
        null,
        null,
        null,
      ]);
    expect(
      streamColumns(flowsheet, { ...results, input_sha256: '0'.repeat(64) }).every(
        (c) => c.result === undefined,
      ),
    ).toBe(true);
    expect(
      rows.find((r) => r.label === 'Total mass flow')!.value(streamColumns(flowsheet, null)[0]),
    ).toBeNull();
  });
  it('reads v1.0 and v1.1 explicitly, and rejects numeric unavailable placeholders', () => {
    const legacy = structuredClone(flowsheet) as unknown as Record<string, unknown>;
    legacy.schema_version = '1.0';
    for (const s of legacy.streams as Record<string, unknown>[]) delete s.engineering_number;
    expect(flowsheetSchema.safeParse(legacy).success).toBe(true);
    const oldResults = structuredClone(results) as unknown as Record<string, unknown>;
    oldResults.schema_version = '1.0';
    delete oldResults.process_result_version;
    (oldResults.engine as Record<string, unknown>).version = '1.0.0';
    for (const s of Object.values(oldResults.streams as Record<string, Record<string, unknown>>)) {
      delete s.properties;
      delete s.property_provenance;
    }
    expect(resultsSchema.safeParse(oldResults).success).toBe(true);
    for (const value of [0, Number.NaN]) {
      const bad = structuredClone(results);
      if (bad.schema_version !== '1.0')
        Object.assign(bad.streams.FEED.properties.density, { value });
      expect(resultsSchema.safeParse(bad).success).toBe(false);
    }
  });
});
