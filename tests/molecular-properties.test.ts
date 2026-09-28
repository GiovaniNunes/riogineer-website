import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { expect, it } from 'vitest';
import { resultsSchema, type Results } from '../src/lib/digital-engineer/contracts';
import { streamColumns, streamRows } from '../src/lib/digital-engineer/stream-table';
import { results, flowsheet } from './compression-fixture';

it('reads all historical result contracts independently of the enriched contract', () => {
  const legacy = JSON.parse(
    execFileSync(
      process.env.ENGINE_PYTHON || resolve('engine/.venv/bin/python'),
      [
        '-B',
        '-c',
        "import json; from riogineer_engine.core import ROOT, loads, build_flowsheet, _calculate_process; names=['requirements.json','milestone-4-requirements.json','milestone-5-requirements.json','milestone-6-requirements.json']; print(json.dumps([_calculate_process(build_flowsheet(loads((ROOT/'contracts/examples'/n).read_text()))) for n in names]))",
      ],
      { cwd: resolve('engine'), encoding: 'utf8' },
    ),
  );
  expect(
    legacy.map((r: { schema_version: string }) => resultsSchema.parse(r).schema_version),
  ).toEqual(['1.1', '1.2', '1.3', '1.4']);
  const oldest = structuredClone(legacy[0]);
  oldest.schema_version = '1.0';
  for (const s of Object.values(oldest.streams) as Record<string, unknown>[]) delete s.properties;
  expect(resultsSchema.parse(oldest).schema_version).toBe('1.0');
  for (const schema_version of ['1.0', '1.1', '1.2', '1.3', '1.4'])
    expect(resultsSchema.safeParse({ ...results, schema_version }).success).toBe(false);
});

it('requires versioned provider provenance, valid units and finite molecular values', () => {
  expect(results.schema_version).toBe('1.5');
  if (results.schema_version !== '1.5') throw new Error('Enriched result required');
  expect(results.process_result_version).toBe('1.4');
  const mutations = [
    (r: Extract<Results, { schema_version: '1.5' }>) => {
      r.streams.FEED.property_provenance.provider = 'fake' as never;
    },
    (r: Extract<Results, { schema_version: '1.5' }>) => {
      r.streams.FEED.property_provenance.molecular_weights_kg_kmol.water = -1;
    },
    (r: Extract<Results, { schema_version: '1.5' }>) => {
      r.streams.FEED.properties.molar_flow.unit = 'mol/h' as never;
    },
    (r: Extract<Results, { schema_version: '1.5' }>) => {
      r.streams.FEED.properties.component_molar_flow.value.water = Number.NaN;
    },
    (r: Extract<Results, { schema_version: '1.5' }>) => {
      Object.assign(r.streams.FEED.properties.density, { value: 0 });
    },
  ];
  for (const mutate of mutations) {
    const bad = structuredClone(results);
    mutate(bad);
    expect(resultsSchema.safeParse(bad).success).toBe(false);
  }
});

it('projects molecular quantities by stable ID despite layout, labels and ordering', () => {
  const f = structuredClone(flowsheet);
  f.streams.reverse();
  f.connections.reverse();
  f.presentation.layout = 'compact';
  for (const s of f.streams) s.service = 'same label';
  const rows = streamRows(f);
  for (const col of streamColumns(f, results)) {
    expect(col.stream).toBe(f.streams.find((s) => s.id === col.stream.id));
    expect(rows.find((r) => r.label === 'Molar flow')!.value(col)).toBe(
      col.properties!.molar_flow.value,
    );
    expect(rows.find((r) => r.label === 'Molecular mass')!.value(col)).toBe(
      col.properties!.molecular_mass.value,
    );
    for (const c of f.components)
      expect(rows.find((r) => r.label === `${c} — molar fraction`)!.value(col)).toBe(
        col.properties!.molar_composition.value![c],
      );
    expect(rows.find((r) => r.label === 'Density')!.value(col)).toBeNull();
  }
});

it('withholds molecular properties for every stale identity mismatch', () => {
  for (const changes of [
    { case_id: 'ANOTHER_CASE' },
    { input_sha256: '0'.repeat(64) },
    { requirements_sha256: '0'.repeat(64) },
  ]) {
    for (const col of streamColumns(flowsheet, { ...results, ...changes })) {
      expect(col.properties).toBeUndefined();
      expect(
        streamRows(flowsheet)
          .find((r) => r.label === 'Molar flow')!
          .value(col),
      ).toBeNull();
    }
  }
});

it('displays actual zero molar fractions while retaining null undefined ratios', () => {
  const column = streamColumns(flowsheet, results).find((c) => c.stream.id === 'GAS_1')!;
  expect(
    streamRows(flowsheet)
      .find((r) => r.label === 'water — molar fraction')!
      .value(column),
  ).toBe(0);
  expect(
    streamRows(flowsheet)
      .find((r) => r.label === 'methane — molar fraction')!
      .value(column),
  ).toBe(1);
  const r = structuredClone(results);
  if (r.schema_version !== '1.5') throw new Error('Enriched result required');
  r.streams.GAS_1.properties.molar_composition = {
    value: null,
    status: 'not_calculated',
    unit: 'mol/mol',
  };
  const zero = streamColumns(flowsheet, r).find((c) => c.stream.id === 'GAS_1')!;
  expect(
    streamRows(flowsheet)
      .find((r) => r.label === 'methane — molar fraction')!
      .value(zero),
  ).toBeNull();
});
