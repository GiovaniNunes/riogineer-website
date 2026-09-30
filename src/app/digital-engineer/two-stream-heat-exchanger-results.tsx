import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';

export function TwoStreamHeatExchangerResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.9' }>;
}) {
  const format = (value: number) =>
    new Intl.NumberFormat('en-US', { maximumFractionDigits: 6 }).format(value);
  return (
    <section aria-label="Rigorous two-stream heat exchanger results">
      <h3>Peng–Robinson two-stream heat exchanger</h3>
      <p>
        Energy transfers between separate material streams. Outlet pressures are specifications.
        This terminal-state balance does not calculate exchanger sizing, area or a minimum approach
        temperature.
      </p>
      {results.equipment.map((e) => {
        const d = e.thermodynamics;
        const hotSpecified = d.specification_mode === 'specified_hot_outlet_temperature';
        return (
          <section key={e.id} aria-label={`${e.id} rigorous heat exchange`}>
            <h4>
              {e.id} — {e.model.id}@{e.model.version}
            </h4>
            <p>
              {hotSpecified
                ? 'Mode A: hot outlet specified; cold outlet recovered by PH.'
                : 'Mode B: cold outlet specified; hot outlet recovered by PH.'}
            </p>
            <div className={styles.tableWrap}>
              <table aria-label={`${e.id} thermodynamic states`}>
                <thead>
                  <tr>
                    <th>State</th>
                    <th>Material port</th>
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
                      ['Hot inlet', 'hot_in', d.hot_inlet],
                      ['Hot outlet', 'hot_out', d.hot_outlet],
                      ['Cold inlet', 'cold_in', d.cold_inlet],
                      ['Cold outlet', 'cold_out', d.cold_outlet],
                    ] as const
                  ).map(([label, port, s]) => (
                    <tr key={port}>
                      <th scope="row">{label}</th>
                      <td>
                        {port} · {e.material_streams[port]}
                      </td>
                      <td>{s.classification}</td>
                      <td>{format(s.temperature_K)}</td>
                      <td>{format(s.pressure_Pa_abs)}</td>
                      <td>{format(s.H_eq_J_mol)}</td>
                      <td>{format(s.S_eq_J_mol_K)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <dl>
              {(
                [
                  ['Hot molar flow (mol/s)', d.hot_molar_flow_mol_s],
                  ['Cold molar flow (mol/s)', d.cold_molar_flow_mol_s],
                  ['Q_hot (W; heat into hot stream)', d.Q_hot_W],
                  ['Q_cold (W; heat into cold stream)', d.Q_cold_W],
                  ['Exchanged duty (W)', d.Q_exchanged_W],
                  ['Energy residual (W)', d.energy_residual_W],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{format(value)}</dd>
                </div>
              ))}
            </dl>
            <p>
              Independent material balances: hot {e.material_balances.hot.status}; cold{' '}
              {e.material_balances.cold.status}. No material transfer between sides.
            </p>
            <details>
              <summary>Thermodynamic diagnostics</summary>
              <p>
                {d.property_package}; BIP: {d.bip.identifier} — {d.bip.source}
              </p>
              <p>
                Recovered PH: {d.ph.status}; {d.ph.pt_profile}; qualified candidates:{' '}
                {d.ph.candidate_count}; enthalpy residual:{' '}
                {d.ph.enthalpy_residual_J_mol.toExponential(3)} J/mol.
              </p>
            </details>
          </section>
        );
      })}
    </section>
  );
}
