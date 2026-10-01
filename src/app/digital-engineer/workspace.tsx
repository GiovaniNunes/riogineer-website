'use client';

import { PumpResults } from './pump-results';
import variablePumpReference from '../../../contracts/examples/milestone-19-pump-requirements.json';
import pumpReference from '../../../contracts/examples/milestone-18-pump-requirements.json';
import { SeparatorEnergyResults } from './separator-energy-results';
import separatorPtReference from '../../../contracts/examples/milestone-17-pt-requirements.json';
import separatorPhReference from '../../../contracts/examples/milestone-17-ph-requirements.json';
import { ThrottlingValveResults } from './throttling-valve-results';
import { useReducer } from 'react';
import {
  engineeringRequirementsSchema as requirementsSchema,
  flowsheetSchema,
  resultsSchema,
  engineeringValidationResponseSchema as validationResponseSchema,
  errorSchema,
} from '@/lib/digital-engineer/contracts';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '@/lib/digital-engineer/workflow';
import { EquilibriumResults } from './equilibrium-results';
import { CompressionResults } from './compression-results';
import { TwoStreamHeatExchangerResults } from './two-stream-heat-exchanger-results';
import { RigorousCompressionResults } from './rigorous-compression-results';
import { Pfd } from './pfd';
import { StreamTable } from './stream-table';
import { SpecificationWorkspace } from './specification';
import styles from './workspace.module.css';

function download(name: string, value: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2) + '\n'], { type: 'application/json' }),
  );
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
const number = (value: number | null) =>
  value === null ? '—' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 6 }).format(value);
export function EngineerWorkspace({
  referenceText,
  networkReferenceText,
  sequentialReferenceText,
  compressionReferenceText,
  equilibriumReferenceText,
}: {
  referenceText: string;
  networkReferenceText: string;
  sequentialReferenceText: string;
  compressionReferenceText: string;
  equilibriumReferenceText: string;
}) {
  const [state, dispatch] = useReducer(workflowReducer, referenceText, initialWorkflow);
  const current = resultsAreCurrent(state);
  async function operate(operation: 'validate-requirements' | 'build-flowsheet' | 'calculate') {
    const revision = state.revision;
    dispatch({ type: 'start', revision });
    try {
      const input =
        operation === 'calculate'
          ? flowsheetSchema.parse(state.flowsheet)
          : requirementsSchema.parse(JSON.parse(state.draft));
      const response = await fetch(`/api/digital-engineer/${operation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
        signal: AbortSignal.timeout(20000),
      });
      const body: unknown = await response.json();
      if (!response.ok) {
        const error = errorSchema.parse(body).error;
        throw new Error(
          error.issues.map((i) => `${i.path}: ${i.message}`).join('\n') || error.message,
        );
      }
      if (operation === 'validate-requirements') {
        validationResponseSchema.parse(body);
        dispatch({ type: 'validated', revision });
      } else if (operation === 'build-flowsheet')
        dispatch({ type: 'built', revision, flowsheet: flowsheetSchema.parse(body) });
      else dispatch({ type: 'calculated', revision, results: resultsSchema.parse(body) });
    } catch (e) {
      dispatch({
        type: 'error',
        revision,
        error: e instanceof Error ? e.message : 'The operation could not complete.',
      });
    }
  }
  const r = state.results;
  let pump = false;
  let variablePump = false;
  let separatorEnergy = false;
  let equilibrium = false;
  let exchanger = false;
  try {
    variablePump = JSON.parse(state.draft).profile === 'variable_pump_energy';
    pump = variablePump || JSON.parse(state.draft).profile === 'pump_energy';
    separatorEnergy = JSON.parse(state.draft).profile === 'separator_energy';
    equilibrium = JSON.parse(state.draft).profile === 'pt_flash_separator';
    exchanger = JSON.parse(state.draft).profile === 'two_stream_heat_exchanger_energy';
  } catch {
    /* Draft may be incomplete. */
  }
  return (
    <div className={`container ${styles.workspace}`}>
      <aside className={styles.model}>
        {pump ? (
          <>
            <strong>Calculation model: Guarded Peng–Robinson liquid pump</strong>
            <p>
              {variablePump
                ? 'Methane mole fraction 0.01–0.55, n-hexane balance'
                : 'Fixed equimolar methane/n-hexane'}{' '}
              with explicit constant zero kij. Inlet 300–350 K and 20–25 MPa absolute; discharge
              equals inlet pressure exactly or rises by at least 10,000 Pa, up to 30 MPa. Isentropic
              efficiency 0.6–1; molar flow 5–200 mol/s. Each accepted state must pass the liquid and
              numerical guards. No pump sizing or cavitation prediction.
            </p>
          </>
        ) : separatorEnergy ? (
          <>
            <strong>Calculation model: Peng–Robinson energy-qualified two-phase separator</strong>
            <p>
              PT mode calculates heat duty at specified vessel pressure and temperature. Adiabatic
              PH imposes zero duty and calculates temperature at specified pressure. Both modes
              publish separate vapor and liquid material outlets.
            </p>
          </>
        ) : exchanger ? (
          <>
            <strong>Calculation model: Peng–Robinson two-stream heat exchanger</strong>
            <p>
              Two separate material paths coupled by heat transfer. One outlet temperature and both
              outlet pressures are specified; PT and PH determine the terminal states. Single-phase
              service only. No exchanger sizing or hydraulic pressure-drop calculation.
            </p>
          </>
        ) : equilibrium ? (
          <>
            <strong>Calculation model: Peng–Robinson PT-flash separator</strong>
            <p>
              Methane/n-hexane vapor–liquid equilibrium at inlet temperature and pressure. Phase
              fractions are molar. Rigorous energy balance, heat duty and shaft work are
              unavailable.
            </p>
          </>
        ) : (
          <>
            <strong>Calculation model: Prescribed Component Recoveries — Development Model</strong>
            <p>
              Specified recoveries distribute components between outlets. Assumed constant heat
              capacities provide the available energy accounting. This does not predict rigorous
              vapor-oil-water equilibrium, vessel sizing or separation efficiency.
            </p>
          </>
        )}
      </aside>
      <ol className={styles.steps} aria-label="Engineering workflow">
        <li>1. Specification</li>
        <li>2. RIOGINEER interpretation</li>
        <li>3. Review &amp; approve</li>
        <li>4. PFD</li>
        <li>5. Simulation</li>
        <li>6. Engineering results</li>
      </ol>
      <SpecificationWorkspace
        onInvalidate={() => dispatch({ type: 'invalidate' })}
        onApproved={(requirements) =>
          dispatch({ type: 'approved', draft: JSON.stringify(requirements, null, 2) })
        }
      />
      <details className={styles.panel}>
        <summary>Engineering data / Advanced</summary>
        <p>
          Developer access to the Bia, Milestone 4 branch/merge and Milestone 5 sequential
          references, plus the Milestone 9 PT-flash separator. Manual JSON validation is an advanced
          deterministic workflow, separate from specification approval.
        </p>
        <section aria-labelledby="inputs-title">
          <span className={styles.eyebrow}>01 / Engineering inputs</span>
          <h2 id="inputs-title">Requirements</h2>
          <p>
            The current Bia reference uses <strong>110,000 kg/h</strong>: methane 22,000, n-hexane
            77,000 and water 11,000. The historical 100,000 kg/h README basis is superseded for this
            workspace.
          </p>
          <p>
            Milestone 4 adds an explicit 60/40 oil split and equal-condition recombination. This
            deterministic reference does not expand natural-language interpretation support.
          </p>
          <label htmlFor="requirements">
            requirements.json — explicit units and development assumptions
          </label>
          <textarea
            id="requirements"
            spellCheck={false}
            value={state.draft}
            onChange={(e) => dispatch({ type: 'edit', draft: e.target.value })}
            aria-describedby="input-help"
          />
          <p id="input-help">
            Advanced contract editing. Changes invalidate validation and previous results. Normal
            specification review uses the engineering form above.
          </p>
          <div aria-label="Requirements validation" aria-live="polite">
            {state.validated ? (
              <p>
                <strong>Requirements validated.</strong>{' '}
                {state.flowsheet
                  ? 'The PFD is available below.'
                  : 'Next: generate the process flow diagram.'}{' '}
                <a href="#pfd-section">Generate PFD</a>. Validation does not run the engineering
                calculation.
              </p>
            ) : state.error ? (
              <p>
                Requirements are not validated.{' '}
                <a href="#engineering-error">Review the engineering error</a>.
              </p>
            ) : (
              <p>Validate requirements to enable PFD generation.</p>
            )}
          </div>
          <div className={styles.actions}>
            <button
              disabled={state.busy}
              onClick={() =>
                dispatch({ type: 'edit', draft: JSON.stringify(pumpReference, null, 2) })
              }
            >
              Load Milestone 18 pump reference
            </button>
            <button
              type="button"
              onClick={() =>
                dispatch({ type: 'edit', draft: JSON.stringify(variablePumpReference, null, 2) })
              }
            >
              Load Milestone 19 variable pump reference
            </button>
            <button
              disabled={state.busy}
              onClick={() =>
                dispatch({ type: 'edit', draft: JSON.stringify(separatorPtReference, null, 2) })
              }
            >
              Load Milestone 17 PT reference
            </button>
            <button
              disabled={state.busy}
              onClick={() =>
                dispatch({ type: 'edit', draft: JSON.stringify(separatorPhReference, null, 2) })
              }
            >
              Load Milestone 17 adiabatic PH reference
            </button>
            <button
              disabled={state.busy || state.validated}
              onClick={() => void operate('validate-requirements')}
            >
              Validate requirements
            </button>
            <button
              className={styles.secondary}
              disabled={state.busy}
              onClick={() => dispatch({ type: 'edit', draft: referenceText })}
            >
              Restore reference
            </button>
            <button
              className={styles.secondary}
              disabled={state.busy}
              onClick={() => dispatch({ type: 'edit', draft: networkReferenceText })}
            >
              Load Milestone 4 reference
            </button>
            <button
              className={styles.secondary}
              disabled={state.busy}
              onClick={() => dispatch({ type: 'edit', draft: sequentialReferenceText })}
            >
              Load Milestone 5 reference
            </button>
            <button
              className={styles.secondary}
              disabled={state.busy}
              onClick={() => dispatch({ type: 'edit', draft: compressionReferenceText })}
            >
              Load Milestone 6 reference
            </button>
            <button
              className={styles.secondary}
              disabled={state.busy}
              onClick={() => dispatch({ type: 'edit', draft: equilibriumReferenceText })}
            >
              Load Milestone 9 reference
            </button>
            <button
              className={styles.secondary}
              disabled={!state.validated || state.busy}
              onClick={() => download('requirements.json', JSON.parse(state.draft))}
            >
              Download requirements
            </button>
          </div>
        </section>
        <h3>flowsheet.json</h3>
        <pre aria-label="flowsheet.json" className={styles.json}>
          {JSON.stringify(state.flowsheet, null, 2)}
        </pre>
        <h3>results.json {current ? '' : '(not current)'}</h3>
        <pre aria-label="results.json" className={styles.json}>
          {JSON.stringify(state.results, null, 2)}
        </pre>
      </details>
      <section id="pfd-section" className={styles.panel} aria-labelledby="pfd-section-title">
        <span className={styles.eyebrow}>04–05 / PFD & simulation</span>
        <h2 id="pfd-section-title">Process flow diagram</h2>
        <p>
          The structured flowsheet controls equipment, material-stream connections and calculation
          inputs.
        </p>
        <div className={styles.actions}>
          <button
            disabled={!state.validated || state.busy}
            onClick={() => void operate('build-flowsheet')}
          >
            Generate PFD
          </button>
          {state.flowsheet && (
            <>
              <button className={styles.secondary} onClick={() => dispatch({ type: 'layout' })}>
                Change display layout
              </button>
              <button
                className={styles.secondary}
                onClick={() => download('flowsheet.json', state.flowsheet)}
              >
                Download flowsheet
              </button>
            </>
          )}
        </div>
        {state.flowsheet ? (
          <div
            className={
              state.flowsheet.presentation.layout === 'compact' ? styles.compact : styles.diagram
            }
          >
            <Pfd flowsheet={state.flowsheet} />
          </div>
        ) : (
          <div className={styles.empty}>
            {state.validated
              ? 'Requirements validated. Select Generate PFD to create the process flow diagram.'
              : 'Approve the requirements, then generate the PFD.'}
          </div>
        )}
        {state.flowsheet && (
          <StreamTable flowsheet={state.flowsheet} results={current ? r : null} />
        )}
        <p>
          Display layout changes do not invalidate engineering results. Diagram editing is not
          available.
        </p>
        <button
          disabled={!state.validated || !state.flowsheet || state.busy}
          onClick={() => void operate('calculate')}
        >
          Run engineering calculation
        </button>
      </section>
      <div role="status" aria-live="polite" className={styles.status}>
        {state.busy
          ? 'Working with the local Python engine…'
          : current
            ? 'Calculation complete — results current.'
            : state.validated && state.flowsheet
              ? 'PFD ready. Run the engineering calculation.' +
                (r ? ' Previous results remain stale.' : '')
              : state.validated
                ? 'Requirements valid. Ready to generate PFD.' +
                  (r ? ' Previous results remain stale.' : '')
                : r
                  ? 'Previous results are stale. Validate, generate the PFD and calculate again.'
                  : 'Requirements await validation.'}
      </div>
      {state.error && (
        <pre
          id="engineering-error"
          aria-label="Engineering error"
          role="alert"
          className={styles.error}
        >
          {state.error}
        </pre>
      )}
      {r && (
        <section
          className={styles.panel}
          aria-labelledby="results-title"
          data-results-status={current ? 'current' : 'stale'}
        >
          <span className={styles.eyebrow}>06 / Deterministic engineering</span>
          <h2 id="results-title">Engineering results {current ? '' : '— STALE'}</h2>
          {!current && (
            <p className={styles.model}>
              These values belong to a previous calculation. They do not describe the current
              inputs.
            </p>
          )}
          <div className={styles.actions}>
            <button
              className={styles.secondary}
              disabled={!current || state.busy}
              onClick={() => download('results.json', r)}
            >
              Download results
            </button>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <caption>
                Stream conditions and component mass flows — scroll horizontally on narrow screens
              </caption>
              <thead>
                <tr>
                  <th scope="col">Property</th>
                  {Object.keys(r.streams).map((s) => (
                    <th key={s} scope="col">
                      {s}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.keys(Object.values(r.streams)[0].component_mass_flow_kg_h).map((c) => (
                  <tr key={c}>
                    <th scope="row">{c} (kg/h)</th>
                    {Object.entries(r.streams).map(([id, s]) => (
                      <td key={id}>{number(s.component_mass_flow_kg_h[c])}</td>
                    ))}
                  </tr>
                ))}
                {(
                  [
                    ['Total mass flow (kg/h)', 'mass_flow_kg_h'],
                    ['Temperature (K)', 'temperature_K'],
                    ['Pressure (Pa absolute)', 'pressure_Pa_abs'],
                    [
                      r.schema_version === '1.6'
                        ? 'Enthalpy flow (W; unavailable)'
                        : r.schema_version === '1.9' ||
                            r.schema_version === '1.10' ||
                            r.schema_version === '1.11' ||
                            r.schema_version === '1.12' ||
                            r.schema_version === '1.13'
                          ? 'Enthalpy flow (W; Peng–Robinson)'
                          : 'Enthalpy flow (W; assumed Cp)',
                      'enthalpy_flow_W',
                    ],
                  ] as const
                ).map(([label, key]) => (
                  <tr key={key}>
                    <th scope="row">{label}</th>
                    {Object.entries(r.streams).map(([id, s]) => (
                      <td key={id}>{number(s[key])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.columns}>
            {r.schema_version !== '1.9' && (
              <div>
                <h3>Mass-balance checks</h3>
                <p>
                  Status: <strong>{r.balances.mass.status}</strong>
                </p>
                <ul>
                  {Object.entries(r.balances.mass.component_residual_kg_h).map(([c, v]) => (
                    <li key={c}>
                      {c}: residual {v.toExponential(3)} kg/h
                    </li>
                  ))}
                </ul>
                <p>
                  Component tolerance: {r.balances.mass.component_tolerance_kg_h.toExponential()}{' '}
                  kg/h.
                </p>
                <p>
                  Total residual: {r.balances.mass.total_residual_kg_h.toExponential(3)} kg/h. Total
                  tolerance: {r.balances.mass.total_tolerance_kg_h.toExponential(2)} kg/h.
                </p>
              </div>
            )}
            <div>
              <h3>Available energy balance</h3>
              {r.balances.energy.status === 'not_calculated' ? (
                <p>{r.balances.energy.reason}</p>
              ) : (
                <>
                  <p>
                    Status: <strong>{r.balances.energy.status}</strong> within the{' '}
                    {r.schema_version === '1.7' ||
                    r.schema_version === '1.8' ||
                    r.schema_version === '1.9' ||
                    r.schema_version === '1.10' ||
                    r.schema_version === '1.11' ||
                    r.schema_version === '1.12' ||
                    r.schema_version === '1.13'
                      ? 'PR equilibrium energy'
                      : 'constant-Cp'}{' '}
                    model.
                  </p>
                  {r.schema_version !== '1.10' && (
                    <p>
                      {r.schema_version === '1.12' || r.schema_version === '1.13'
                        ? 'Imposed pump heat duty: '
                        : r.schema_version === '1.11'
                          ? r.equipment[0].thermodynamics.mode === 'adiabatic'
                            ? 'Imposed separator duty: '
                            : 'Calculated separator duty: '
                          : 'execution' in r
                            ? 'Calculated network duty: '
                            : 'Calculated separator duty: '}
                      <strong>{number(r.balances.energy.duty_W)} W</strong>{' '}
                      {'execution' in r && r.schema_version !== '1.11'
                        ? '(positive into the network).'
                        : '(positive into the separator).'}
                    </p>
                  )}
                  <p>
                    Residual: {r.balances.energy.residual_W.toExponential(3)} W; tolerance:{' '}
                    {r.balances.energy.tolerance_W.toExponential()} W.
                  </p>
                  {'reference_temperature_K' in r.balances.energy && (
                    <p>
                      Enthalpy reference: {r.balances.energy.reference_temperature_K} K. A zero duty
                      at equal temperatures is calculated by this model.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
          {'execution' in r &&
            r.schema_version !== '1.6' &&
            r.schema_version !== '1.9' &&
            r.schema_version !== '1.10' &&
            r.schema_version !== '1.11' &&
            r.schema_version !== '1.12' &&
            r.schema_version !== '1.13' && (
              <>
                <h3>Equipment checks</h3>
                <p>Execution order: {r.execution.equipment_order.join(' → ')}</p>
                <div className={styles.tableWrap}>
                  <table aria-label="Equipment balance checks">
                    <thead>
                      <tr>
                        <th>Equipment</th>
                        <th>Duty (W, positive into process)</th>
                        <th>Total residual (kg/h)</th>
                        <th>Component residuals (kg/h)</th>
                        <th>Constant-Cp energy residual (W)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.equipment.map((e) => (
                        <tr key={e.id}>
                          <th scope="row">{e.id}</th>
                          <td>{number(e.duty_W)}</td>
                          <td>{number(e.mass_balance.total_residual_kg_h)}</td>
                          <td>
                            {Object.entries(e.mass_balance.component_residual_kg_h)
                              .map(([c, v]) => `${c}: ${number(v)}`)
                              .join('; ')}
                          </td>
                          <td>{number(e.energy_residual_W)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p>
                  Mixing is restricted to equal inlet temperature and pressure. Energy accounting
                  uses only the shared constant-Cp development basis; it is not a general plant
                  thermodynamic solution.
                </p>
              </>
            )}
          {r.schema_version === '1.6' && current && <EquilibriumResults results={r} />}
          {(r.schema_version === '1.4' ||
            (r.schema_version === '1.5' && r.process_result_version === '1.4')) && (
            <CompressionResults results={r} />
          )}
          {r.schema_version === '1.9' && current && <TwoStreamHeatExchangerResults results={r} />}
          {r.schema_version === '1.8' && current && <RigorousCompressionResults results={r} />}
          {(r.schema_version === '1.12' || r.schema_version === '1.13') && current && (
            <PumpResults results={r} />
          )}
          {r.schema_version === '1.11' && current && <SeparatorEnergyResults results={r} />}
          {r.schema_version === '1.10' && current && <ThrottlingValveResults results={r} />}
          <h3>Warnings and model limitations</h3>
          <ul aria-label="Warnings and model limitations">
            {[...new Set([...r.warnings.map((w) => w.message), ...r.limitations])].map(
              (message) => (
                <li key={message}>{message}</li>
              ),
            )}
          </ul>
          <h3>Unavailable calculations</h3>
          <ul>
            {r.unavailable.map((u) => (
              <li key={u.calculation}>
                <strong>
                  {u.calculation}: {u.status}.
                </strong>{' '}
                {u.reason}
              </li>
            ))}
          </ul>
          <details>
            <summary>Calculation provenance</summary>
            <p>
              Engine {r.engine.version}; model {r.engine.model.id}@{r.engine.model.version}
            </p>
            <p className={styles.hash}>Input fingerprint: {r.input_sha256}</p>
            <p className={styles.hash}>Run: {r.run_id}</p>
          </details>
        </section>
      )}
    </div>
  );
}
