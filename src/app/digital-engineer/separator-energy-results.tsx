import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';
const show = (v: number | null) => (v === null ? '—' : v.toPrecision(12));
export function SeparatorEnergyResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.11' }>;
}) {
  const u = results.equipment[0];
  const d = u.thermodynamics;
  return (
    <section aria-label="Separator energy results">
      <h3>{u.id} · Energy-qualified two-phase separator</h3>
      <p>
        Model {u.model.id}@{u.model.version} · {d.property_package} · {d.caloric_dataset}
      </p>
      <p>
        Operating mode:{' '}
        <strong>
          {d.mode === 'adiabatic' ? 'Adiabatic PH' : 'Specified pressure and temperature (PT)'}
        </strong>
        .
      </p>
      <p>
        Inlet: {show(d.inlet.temperature_K)} K, {show(d.inlet.pressure_Pa_abs)} Pa absolute;{' '}
        {d.inlet.classification}.
      </p>
      <p>
        Separator pressure: {show(d.outlet.pressure_Pa_abs)} Pa absolute.{' '}
        {d.mode === 'adiabatic' ? 'Calculated temperature' : 'Specified temperature'}:{' '}
        {show(d.outlet.temperature_K)} K.
      </p>
      <p>
        {d.mode === 'adiabatic' ? 'Imposed zero duty' : 'Calculated heat duty'}:{' '}
        <strong>{show(d.duty_W)} W</strong> (positive into the equipment). Shaft work: 0 W.
      </p>
      <p>
        Outlet state: {d.outlet.classification}. Vapor molar fraction β: {show(d.outlet.beta)}.
        Inlet enthalpy flow: {show(d.inlet_enthalpy_flow_W)} W.
      </p>
      <div className={styles.tableWrap}>
        <table aria-label="Separator phase energy and material outlets">
          <thead>
            <tr>
              <th>Phase</th>
              <th>Mass flow (kg/h)</th>
              <th>Molar flow (mol/s)</th>
              <th>Molar composition</th>
              <th>Specific enthalpy (J/mol)</th>
              <th>Enthalpy flow (W)</th>
            </tr>
          </thead>
          <tbody>
            {(['vapor', 'liquid'] as const).map((name) => {
              const p = d.phases[name];
              return (
                <tr key={name}>
                  <th scope="row">{name}</th>
                  <td>{show(results.streams[u.material_streams[name]].mass_flow_kg_h)}</td>
                  <td>{show(p.molar_flow_mol_s)}</td>
                  <td>
                    {p.composition
                      ? Object.entries(p.composition)
                          .map(([k, v]) => `${k}: ${show(v)}`)
                          .join('; ')
                      : '—'}
                  </td>
                  <td>{show(p.h_J_mol)}</td>
                  <td>{show(p.enthalpy_flow_W)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p>
        Mass balance: {u.mass_balance.status}. Energy residual: {show(d.energy_residual_W)} W;
        tolerance: {show(d.energy_allowance_W)} W.
      </p>
      {d.ph && (
        <p>
          PH: {d.ph.status}; {d.ph.candidate_count} candidate; high-accuracy PT, fresh final
          acceptance; enthalpy residual {show(d.ph.enthalpy_residual_J_mol)} J/mol.
        </p>
      )}
      <p>
        Absent-phase intensive properties are unavailable; its enthalpy-flow contribution is zero.
        Qualified methane/n-hexane, explicit zero kij and tested 200–500 K matrix only. No water,
        vessel sizing, entrainment, hydraulics or mixed equipment networks.
      </p>
    </section>
  );
}
