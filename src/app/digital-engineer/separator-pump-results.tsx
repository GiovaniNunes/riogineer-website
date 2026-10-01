import type { Results } from '@/lib/digital-engineer/contracts';
const number = (v: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 }).format(v);
export function SeparatorPumpResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.14' }>;
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
        Qualified tuple: {pump.thermodynamics.qualification_id}. Listed reference cases only;
        arbitrary low-pressure inputs are unsupported.
      </p>
      <p>
        Separator: {separator.model.id}@{separator.model.version}. Pump: {pump.model.id}@
        {pump.model.version}.
      </p>
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
          Inlet phase: {context.phase}; evidence: {context.saturation}; source:{' '}
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
