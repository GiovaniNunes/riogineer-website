import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';
const format = (value: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 6 }).format(value);
export function CompressionResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.4' }>;
}) {
  const energy = results.balances.energy;
  return (
    <section aria-label="Compression and network work">
      <h3>Process energy boundary</h3>
      <p>
        Positive heat and process work enter the material streams. Shaft input includes mechanical
        losses outside this boundary. Driver power is not calculated.
      </p>
      <dl>
        <dt>Network heat input (W)</dt>
        <dd>{format(energy.duty_W)}</dd>
        <dt>Network gas/process work input (W)</dt>
        <dd>{format(energy.process_work_W)}</dd>
        <dt>Network shaft power (W)</dt>
        <dd>{format(energy.shaft_power_W)}</dd>
        <dt>Mechanical losses outside process boundary (W)</dt>
        <dd>{format(energy.mechanical_loss_W)}</dd>
        <dt>External sensible enthalpy-flow change (W)</dt>
        <dd>{format(energy.external_enthalpy_change_W)}</dd>
        <dt>Network energy residual (W)</dt>
        <dd>{format(energy.residual_W)}</dd>
      </dl>
      {results.equipment.map(
        (e) =>
          e.type === 'compressor' && (
            <section key={e.id} aria-label={`${e.id} compression results`}>
              <h3>{e.id} — ideal-gas development model</h3>
              <div className={styles.tableWrap}>
                <table aria-label={`${e.id} compression values`}>
                  <thead>
                    <tr>
                      <th>Quantity</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(
                      [
                        ['Inlet pressure (Pa absolute)', e.compression.inlet_pressure_Pa_abs],
                        [
                          'Discharge pressure (Pa absolute)',
                          e.compression.discharge_pressure_Pa_abs,
                        ],
                        ['Pressure ratio (dimensionless)', e.compression.pressure_ratio],
                        ['Inlet temperature (K)', e.compression.inlet_temperature_K],
                        [
                          'Isentropic discharge temperature (K)',
                          e.compression.isentropic_discharge_temperature_K,
                        ],
                        ['Actual discharge temperature (K)', e.compression.discharge_temperature_K],
                        ['Cp (J/(kg K))', e.compression.cp_J_kg_K],
                        ['k = Cp/Cv (dimensionless)', e.compression.heat_capacity_ratio],
                        [
                          'Isentropic efficiency (dimensionless)',
                          e.compression.isentropic_efficiency,
                        ],
                        ['Gas/process power W_gas (W)', e.compression.gas_power_W],
                        [
                          'Mechanical efficiency (dimensionless)',
                          e.compression.mechanical_efficiency,
                        ],
                        ['Shaft power W_shaft (W)', e.compression.shaft_power_W],
                        ['Mechanical loss (W)', e.compression.mechanical_loss_W],
                        ['Heat duty (W)', e.duty_W],
                        ['Total mass residual (kg/h)', e.mass_balance.total_residual_kg_h],
                        ['Energy residual (W)', e.energy_residual_W],
                      ] as const
                    ).map(([label, value]) => (
                      <tr key={label}>
                        <th scope="row">{label}</th>
                        <td>{format(value)}</td>
                      </tr>
                    ))}
                    {Object.entries(e.mass_balance.component_residual_kg_h).map(([c, v]) => (
                      <tr key={c}>
                        <th scope="row">{c} residual (kg/h)</th>
                        <td>{format(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ),
      )}
    </section>
  );
}
