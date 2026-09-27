import type { Flowsheet, Results } from './contracts';

export function streamColumns(flowsheet: Flowsheet, results: Results | null) {
  const current =
    results?.input_sha256 === flowsheet.calculation.input_sha256 &&
    results?.case_id === flowsheet.case_id &&
    results?.requirements_sha256 === flowsheet.requirements_sha256;
  return [...flowsheet.streams]
    .sort(
      (a, b) =>
        (('engineering_number' in a ? a.engineering_number : Infinity) as number) -
          (('engineering_number' in b ? b.engineering_number : Infinity) as number) ||
        a.id.localeCompare(b.id),
    )
    .map((stream) => ({
      stream,
      connection: flowsheet.connections.find((c) => c.stream_id === stream.id)!,
      result: current ? results?.streams[stream.id] : undefined,
      properties:
        current && results && results.schema_version !== '1.0'
          ? results.streams[stream.id]?.properties
          : undefined,
    }));
}
export type StreamColumn = ReturnType<typeof streamColumns>[number];
export function streamRows(flowsheet: Flowsheet) {
  type Row = {
    label: string;
    unit: string;
    value: (column: StreamColumn) => number | string | null;
  };
  const rows: Row[] = [
    {
      label: 'Source',
      unit: 'equipment / port',
      value: (c) => `${c.connection.source.owner_id} / ${c.connection.source.port_id}`,
    },
    {
      label: 'Destination',
      unit: 'equipment / port',
      value: (c) => `${c.connection.target.owner_id} / ${c.connection.target.port_id}`,
    },
    {
      label: 'Pressure',
      unit: 'Pa absolute',
      value: (c) => c.result?.pressure_Pa_abs ?? c.stream.specified_state?.pressure_Pa_abs ?? null,
    },
    {
      label: 'Temperature',
      unit: 'K',
      value: (c) => c.result?.temperature_K ?? c.stream.specified_state?.temperature_K ?? null,
    },
    { label: 'Total mass flow', unit: 'kg/h', value: (c) => c.result?.mass_flow_kg_h ?? null },
  ];
  for (const [key, label, unit] of [
    ['molar_flow', 'Molar flow', 'kmol/h'],
    ['molecular_mass', 'Molecular mass', 'kg/kmol'],
    ['density', 'Density', 'kg/m3'],
    ['gas_volumetric_flow', 'Gas volumetric flow', 'm3/h'],
    ['oil_volumetric_flow', 'Oil volumetric flow', 'm3/h'],
    ['water_volumetric_flow', 'Water volumetric flow', 'm3/h'],
  ] as const) {
    rows.push({
      label,
      unit,
      value: (c) => c.properties?.[key].value ?? null,
    });
  }
  for (const component of flowsheet.components) {
    rows.push({
      label: `${component} — component mass flow`,
      unit: 'kg/h',
      value: (c) =>
        c.result?.component_mass_flow_kg_h[component] ??
        c.stream.specified_state?.component_mass_flow_kg_h[component] ??
        null,
    });
    rows.push({
      label: `${component} — mass fraction`,
      unit: 'kg/kg',
      value: (c) => c.result?.component_mass_fractions?.[component] ?? null,
    });
    rows.push({
      label: `${component} — molar fraction`,
      unit: 'mol/mol',
      value: (c) => c.properties?.molar_composition.value?.[component] ?? null,
    });
  }
  return rows;
}
