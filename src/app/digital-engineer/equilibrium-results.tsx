import type { z } from 'zod';
import type { equilibriumResultsSchema } from '@/lib/digital-engineer/contracts';
import styles from './workspace.module.css';

type EquilibriumResults = z.infer<typeof equilibriumResultsSchema>;
const display = (value: number | null) => (value === null ? '—' : value.toPrecision(12));
export function EquilibriumResults({ results }: { results: EquilibriumResults }) {
  const unit = results.equipment[0];
  const t = unit.thermodynamics;
  return (
    <section aria-label="Separator thermodynamic results">
      <h3>{unit.id} · PT-flash equilibrium</h3>
      <p>
        Model {unit.model.id}@{unit.model.version} · {t.property_package} · {t.component_dataset}
      </p>
      <p>
        Phase classification: <strong>{t.classification}</strong>. Convergence: {t.status};{' '}
        {t.iterations} flash iterations.
      </p>
      <p>
        Vapor molar fraction of total feed β = {display(t.beta)}; liquid fraction ={' '}
        {display(t.liquid_fraction)}. These are molar fractions (mol/mol), not mass fractions.
      </p>
      <p>
        Inlet: {display(t.inlet_molar_flow_kmol_h)} kmol/h; vapor:{' '}
        {display(t.vapor_molar_flow_kmol_h)} kmol/h; liquid: {display(t.liquid_molar_flow_kmol_h)}{' '}
        kmol/h.
      </p>
      <p>
        Z liquid: {display(t.Z_L)}; Z vapor: {display(t.Z_V)}. Absent-phase quantities are
        unavailable (—).
      </p>
      <div className={styles.tableWrap}>
        <table aria-label="PT flash phase compositions and checks">
          <thead>
            <tr>
              <th>Component</th>
              <th>Liquid x (mol/mol)</th>
              <th>Vapor y (mol/mol)</th>
              <th>φ liquid</th>
              <th>φ vapor</th>
              <th>Final K</th>
              <th>Log fugacity residual</th>
              <th>Material reconstruction (mol/mol)</th>
              <th>Molar residual (kmol/h)</th>
              <th>Mass residual (kg/h)</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(t.component_molar_residual_kmol_h).map((id) => (
              <tr key={id}>
                <th scope="row">{id}</th>
                {[
                  t.x?.[id],
                  t.y?.[id],
                  t.phi_L?.[id],
                  t.phi_V?.[id],
                  t.final_K?.[id],
                  t.fugacity_residual?.[id],
                  t.material_reconstruction_residual[id],
                  t.component_molar_residual_kmol_h[id],
                  t.component_mass_residual_kg_h[id],
                ].map((v, i) => (
                  <td key={i}>{display(v ?? null)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        Rachford–Rice residual (dimensionless): {display(t.rachford_rice_residual)}. Total mass
        residual: {display(t.total_mass_residual_kg_h)} kg/h. Component molar tolerance:{' '}
        {t.component_molar_tolerance_kmol_h} kmol/h.
      </p>
      <p>
        BIP: {t.bip.identifier}; kij = 0 for methane/n_hexane. {t.bip.source}
      </p>
      <p>
        Isothermal and isobaric at inlet conditions. Heat duty, shaft work and rigorous phase-change
        energy balance are unavailable. Density and phase volumetric flows are not calculated.
      </p>
    </section>
  );
}
