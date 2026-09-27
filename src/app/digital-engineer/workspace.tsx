'use client';
import { useReducer } from 'react';
import {
  requirementsSchema,
  flowsheetSchema,
  resultsSchema,
  validationResponseSchema,
  errorSchema,
} from '@/lib/digital-engineer/contracts';
import {
  initialWorkflow,
  workflowReducer,
  resultsAreCurrent,
} from '@/lib/digital-engineer/workflow';
import { Pfd } from './pfd';
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
const number = (value: number) =>
  new Intl.NumberFormat('en-US', { maximumFractionDigits: 6 }).format(value);
export function EngineerWorkspace({ referenceText }: { referenceText: string }) {
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
  return (
    <div className={`container ${styles.workspace}`}>
      <aside className={styles.model}>
        <strong>Calculation model: Prescribed Component Recoveries — Development Model</strong>
        <p>
          Specified recoveries distribute components between outlets. Assumed constant heat
          capacities provide the available energy accounting. This does not predict rigorous
          vapor-oil-water equilibrium, vessel sizing or separation efficiency.
        </p>
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
          Developer access to the approved Milestone 1 contracts and Bia regression reference.
          Manual JSON validation is an advanced deterministic workflow, separate from specification
          approval.
        </p>
        <section aria-labelledby="inputs-title">
          <span className={styles.eyebrow}>01 / Engineering inputs</span>
          <h2 id="inputs-title">Requirements</h2>
          <p>
            The current Bia reference uses <strong>110,000 kg/h</strong>: methane 22,000, n-hexane
            77,000 and water 11,000. The historical 100,000 kg/h README basis is superseded for this
            workspace.
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
          <div className={styles.actions}>
            <button disabled={state.busy} onClick={() => void operate('validate-requirements')}>
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
              disabled={!state.validated || state.busy}
              onClick={() => download('requirements.json', JSON.parse(state.draft))}
            >
              Download requirements
            </button>
          </div>
        </section>
        <h3>flowsheet.json</h3>
        <pre className={styles.json}>{JSON.stringify(state.flowsheet, null, 2)}</pre>
        <h3>results.json {current ? '' : '(not current)'}</h3>
        <pre className={styles.json}>{JSON.stringify(state.results, null, 2)}</pre>
      </details>
      <section className={styles.panel} aria-labelledby="pfd-section-title">
        <span className={styles.eyebrow}>04–05 / PFD & simulation</span>
        <h2 id="pfd-section-title">Process flow diagram</h2>
        <p>
          One feed source, one separator and three product sinks. The structured flowsheet controls
          connections and calculation inputs.
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
          <div className={styles.empty}>Approve the requirements, then generate the PFD.</div>
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
        <pre aria-label="Engineering error" role="alert" className={styles.error}>
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
                    ['Enthalpy flow (W; assumed Cp)', 'enthalpy_flow_W'],
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
            <div>
              <h3>Available energy balance</h3>
              <p>
                Status: <strong>{r.balances.energy.status}</strong> within the constant-Cp model.
              </p>
              <p>
                Calculated separator duty: <strong>{number(r.balances.energy.duty_W)} W</strong>{' '}
                (positive into the separator).
              </p>
              <p>
                Residual: {r.balances.energy.residual_W.toExponential(3)} W; tolerance:{' '}
                {r.balances.energy.tolerance_W.toExponential()} W.
              </p>
              <p>
                Enthalpy reference: {r.balances.energy.reference_temperature_K} K. A zero duty at
                equal temperatures is calculated by this model.
              </p>
            </div>
          </div>
          <h3>Warnings and model limitations</h3>
          <ul>
            {r.warnings.map((w) => (
              <li key={w.code}>{w.message}</li>
            ))}
            {r.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
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
