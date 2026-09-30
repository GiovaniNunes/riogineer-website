import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';

export function ThrottlingValveResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.10' }>;
}) {
  const format = (value: number) =>
    new Intl.NumberFormat('en-US', { maximumSignificantDigits: 10 }).format(value);
  return (
    <section aria-label="Rigorous throttling valve results">
      <h3>Peng–Robinson isenthalpic throttling valve</h3>
      <p>
        One overall outlet stream, including internal equilibrium phases. Single-phase inlet
        service. Outlet pressure is specified; outlet temperature is calculated.
      </p>
      {results.equipment.map((e) => {
        const d = e.thermodynamics;
        return (
          <section key={e.id} aria-label={`${e.id} rigorous throttling`}>
            <h4>
              {e.id} — {e.model.id}@{e.model.version}
            </h4>
            <div className={styles.tableWrap}>
              <table aria-label={`${e.id} thermodynamic states`}>
                <thead>
                  <tr>
                    <th>State</th>
                    <th>Phase</th>
                    <th>T (K)</th>
                    <th>P (Pa absolute)</th>
                    <th>H (J/mol)</th>
                    <th>S (J/(mol K))</th>
                    <th>Vapor mole fraction</th>
                  </tr>
                </thead>
                <tbody>
                  {(
                    [
                      ['Inlet', d.inlet],
                      ['Outlet', d.outlet],
                    ] as const
                  ).map(([label, s]) => (
                    <tr key={label}>
                      <th scope="row">{label}</th>
                      <td>{s.classification}</td>
                      <td>{format(s.temperature_K)}</td>
                      <td>{format(s.pressure_Pa_abs)}</td>
                      <td>{format(s.H_eq_J_mol)}</td>
                      <td>{format(s.S_eq_J_mol_K)}</td>
                      <td>{format(s.beta)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <dl>
              {(
                [
                  ['Molar flow (mol/s)', d.F_mol_s],
                  ['Pressure ratio (P out / P in)', d.pressure_ratio],
                  ['Pressure drop (Pa)', d.pressure_drop_Pa],
                  ['Outlet enthalpy target (J/mol)', d.H_out_target_J_mol],
                  ['Enthalpy change (J/mol)', d.delta_H_J_mol],
                  ['Entropy change (J/(mol K))', d.delta_S_J_mol_K],
                  ['Enthalpy residual (J/mol)', d.enthalpy_residual_J_mol],
                  ['Energy closure residual (W)', d.energy_residual_W],
                  ['PH residual (J/mol)', d.ph.enthalpy_residual_J_mol],
                  ['PH candidate count', d.ph.candidate_count],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{format(value)}</dd>
                </div>
              ))}
            </dl>
            <p>
              PH: {d.ph.status}; {d.ph.capability}; {d.ph.pt_profile}. Property package:{' '}
              {d.property_package}. BIP: {d.bip.identifier} — {d.bip.source}.
            </p>
            {Object.entries(d.outlet.phases).map(([name, phase]) => (
              <p key={name}>
                {name}: Z = {format(phase.Z)}; H = {format(phase.h_J_mol)} J/mol; S ={' '}
                {format(phase.s_J_mol_K)} J/(mol K); mole fractions:{' '}
                {Object.entries(phase.composition)
                  .map(([id, x]) => `${id} ${format(x)}`)
                  .join(', ')}
                .
              </p>
            ))}
          </section>
        );
      })}
      <p>
        Adiabatic isenthalpic equilibrium model. Energy residual is a closure diagnostic. No valve
        sizing, Cv/Kv, hydraulic flow prediction, shaft power, efficiency, choking or cavitation
        calculation.
      </p>
    </section>
  );
}
