import type { Results } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';
const number = (v: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 9 }).format(v);
export function PumpResults({
  results,
}: {
  results: Extract<Results, { schema_version: '1.12' }>;
}) {
  const e = results.equipment[0];
  const d = e.thermodynamics;
  return (
    <section aria-label="Liquid pump results">
      <h3>Guarded liquid pump — {e.id}</h3>
      <dl>
        <dt>Specified discharge pressure (Pa absolute)</dt>
        <dd>{number(d.outlet_pressure_Pa_abs)}</dd>
        <dt>Specified isentropic efficiency</dt>
        <dd>{number(d.isentropic_efficiency)}</dd>
        <dt>Inlet temperature (K)</dt>
        <dd>{number(d.inlet.temperature_K)}</dd>
        <dt>Calculated outlet temperature (K)</dt>
        <dd>{number(d.actual_outlet.temperature_K)}</dd>
        <dt>Power transferred to fluid (W)</dt>
        <dd>{number(d.fluid_power_W)}</dd>
        <dt>Imposed heat duty (W)</dt>
        <dd>0</dd>
        <dt>Mass check</dt>
        <dd>{e.mass_balance.status}</dd>
        <dt>Energy check</dt>
        <dd>
          {results.balances.energy.status}; residual {d.energy_residual_W.toExponential(3)} W
        </dd>
        <dt>Molar flow (kmol/h)</dt>
        <dd>{number(3.6 * d.F_mol_s)}</dd>
        <dt>Isentropic reference temperature (K)</dt>
        <dd>
          {d.isentropic_outlet
            ? number(d.isentropic_outlet.temperature_K)
            : 'Unavailable — equal-pressure identity'}
        </dd>
        <dt>Reconstructed efficiency</dt>
        <dd>
          {d.reconstructed_efficiency === null
            ? 'Unavailable — zero work'
            : number(d.reconstructed_efficiency)}
        </dd>
      </dl>
      <p>
        The isentropic reference is an equipment diagnostic. Power is positive into the fluid. The
        energy check verifies algebraic consistency.
      </p>
      <details>
        <summary>Technical phase, witness and solver diagnostics</summary>
        <p>
          Fresh 16 MPa witnesses test liquid admissibility; they are auxiliary calculations, not
          material streams. Work screening is a numerical allowance, not certified uncertainty. NPSH
          and cavitation safety are not calculated.
        </p>
        <pre className={styles.json}>
          {JSON.stringify(
            {
              guard_status: d.guard_status,
              mode: d.mode,
              work_screening_allowance_J_mol: d.work_screening_allowance_J_mol,
              work_screening_ratio: d.work_screening_ratio,
              ps: d.ps,
              ph: d.ph,
              witnesses: d.witnesses,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}
