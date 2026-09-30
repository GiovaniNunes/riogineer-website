import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';

export function RigorousCompressionResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.8' }>;
}) {
  const format = (value: number) =>
    new Intl.NumberFormat('en-US', { maximumFractionDigits: 6 }).format(value);
  return (
    <section aria-label="Rigorous compressor results">
      <h3>Peng–Robinson adiabatic compressor</h3>
      <p>
        Vapor service only. Positive fluid power enters the material stream. Mechanical losses and
        driver power are not calculated.
      </p>
      {results.equipment.map((e) => (
        <section key={e.id} aria-label={`${e.id} rigorous compression`}>
          <h4>
            {e.id} — {e.model.id}@{e.model.version}
          </h4>
          <div className={styles.tableWrap}>
            <table aria-label={`${e.id} thermodynamic states`}>
              <thead>
                <tr>
                  <th>State</th>
                  <th>Phase</th>
                  <th>Temperature (K)</th>
                  <th>Pressure (Pa absolute)</th>
                  <th>H (J/mol)</th>
                  <th>S (J/(mol K))</th>
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ['Inlet', e.thermodynamics.inlet],
                    ['Isentropic outlet', e.thermodynamics.isentropic_outlet],
                    ['Actual outlet', e.thermodynamics.actual_outlet],
                  ] as const
                ).map(([label, state]) => (
                  <tr key={label}>
                    <th scope="row">{label}</th>
                    <td>{state.classification}</td>
                    <td>{format(state.temperature_K)}</td>
                    <td>{format(state.pressure_Pa_abs)}</td>
                    <td>{format(state.H_eq_J_mol)}</td>
                    <td>{format(state.S_eq_J_mol_K)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <dl>
            {(
              [
                ['Isentropic efficiency', e.thermodynamics.isentropic_efficiency],
                ['Recovered efficiency', e.thermodynamics.reconstructed_efficiency],
                ['Molar flow (mol/s)', e.thermodynamics.F_mol_s],
                ['Isentropic fluid power (W)', e.thermodynamics.isentropic_fluid_power_W],
                ['Actual fluid power (W)', e.thermodynamics.fluid_power_W],
                ['Energy residual (W)', e.thermodynamics.energy_residual_W],
              ] as const
            ).map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{format(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </section>
  );
}
