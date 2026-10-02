import type { Results } from '@/lib/digital-engineer/contracts';
import { formatEngineeringNumber } from '@/lib/digital-engineer/number-format';
const number = (v: number) => formatEngineeringNumber(v, 8);
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

function inletEvidence(diagnostics: Record<string, unknown>) {
  const inlet = diagnostics.inlet;
  if (!record(inlet) || inlet.status !== 'accepted' || !record(inlet.local))
    return 'Not available in the recorded diagnostics';
  switch (inlet.local.status) {
    case 'compressed_witness':
      return 'Verified compressed liquid — lower-pressure witness';
    case 'saturated_source_liquid':
      return 'Verified saturated source liquid — parent equilibrium coexistence';
    default:
      return 'Not available in the recorded diagnostics';
  }
}
export function SeparatorPumpResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.14' | '1.15' }>;
}) {
  const pump = results.equipment.find((e) => e.type === 'pump')!;
  const separator = results.equipment.find((e) => e.type === 'equilibrium_separator_2phase')!;
  if (pump.type !== 'pump' || separator.type !== 'equilibrium_separator_2phase') return null;
  const inlet = results.streams[pump.material_streams.inlet];
  const outlet = results.streams[pump.material_streams.outlet];
  const context = inlet.state_context;
  return (
    <section aria-label="Separator-to-pump results">
      <h3>Qualified separator-to-pump integration</h3>
      <p>
        Qualified tuple: {pump.thermodynamics.qualification_id}. Listed reference cases only; other
        source, pressure, flow and efficiency combinations are unsupported.
      </p>
      <p>
        Separator: {separator.model.id}@{separator.model.version}. Pump: {pump.model.id}@
        {pump.model.version}.
      </p>
      <p>
        Pump numerical profile:{' '}
        {'numerical_profile' in pump.thermodynamics
          ? 'PT200 — explicitly selected for this reference'
          : 'Historical default'}
        . Separator calculation: historical settings.
      </p>
      {'numerical_profile' in pump.thermodynamics && (
        <p>
          Reference:{' '}
          {pump.thermodynamics.qualification_id.includes('BELOW')
            ? 'Below-boundary reference'
            : 'Above-boundary reference'}
          . Discharge: 8 MPa absolute; efficiency: 0.8.
        </p>
      )}
      <dl>
        <dt>
          {separator.thermodynamics.mode === 'adiabatic'
            ? 'Separator heat duty — imposed zero (W; positive into process)'
            : 'Separator heat duty — calculated (W; positive into process)'}
        </dt>
        <dd>{number(separator.duty_W)}</dd>
        <dt>Pump fluid power (W; work into process)</dt>
        <dd>{number(pump.work_W)}</dd>
        <dt>Liquid inlet temperature (K)</dt>
        <dd>{number(inlet.temperature_K)}</dd>
        <dt>Pumped liquid temperature (K)</dt>
        <dd>{number(outlet.temperature_K)}</dd>
        <dt>Preserved upstream enthalpy flow (W)</dt>
        <dd>{number(inlet.enthalpy_flow_W)}</dd>
        <dt>Reconstructed efficiency</dt>
        <dd>
          {pump.thermodynamics.reconstructed_efficiency === null
            ? 'Unavailable — equal-pressure identity'
            : number(pump.thermodynamics.reconstructed_efficiency)}
        </dd>
      </dl>
      {context?.specification_kind === 'upstream_derived' && (
        <p>
          Inlet phase: {context.phase}. Source saturation metadata:{' '}
          {context.saturation === 'unknown' ? 'unknown (unspecified)' : context.saturation}. Local
          phase evidence: {inletEvidence(pump.thermodynamics.diagnostics)}. Source:{' '}
          {context.source.equipment_id} / {context.source.port_id}. Pump outlet producer: {pump.id}{' '}
          / outlet; separator lineage retained.
        </p>
      )}
      {results.equipment.map((e) => (
        <p key={e.id}>
          {e.id}: mass balance {e.mass_balance.status}; energy residual{' '}
          {e.energy_residual_W.toExponential(3)} W.
        </p>
      ))}
      <p>
        Overall energy: {results.balances.energy.status}; residual{' '}
        {results.balances.energy.residual_W.toExponential(3)} W; allowance{' '}
        {results.balances.energy.tolerance_W.toExponential(3)} W.
      </p>
      <p>
        Local phase checks do not establish a continuous liquid path, bubble-pressure margin, NPSH
        or cavitation safety. Electrical power and hydraulic sizing are unavailable.
      </p>
    </section>
  );
}
