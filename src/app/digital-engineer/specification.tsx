'use client';
import { useRef, useState } from 'react';
import {
  errorSchema,
  validationResponseSchema,
  type Requirements,
} from '@/lib/digital-engineer/contracts';
import {
  envelopeSchema,
  emptyReview,
  factKey,
  labels,
  unitsFor,
  type Envelope,
  type Review,
  type Correction,
} from '@/lib/digital-engineer/interpretation/contracts';
import {
  blockers,
  effectiveValues,
  reviewFields,
  capabilityManifest,
  sameValue,
  normalize,
  isMissingValue,
  isOrdinaryMissingInput,
} from '@/lib/digital-engineer/interpretation/review';
import styles from './workspace.module.css';

type Props = { onInvalidate: () => void; onApproved: (requirements: Requirements) => void };
export function SpecificationWorkspace({ onInvalidate, onApproved }: Props) {
  const [specification, setSpecification] = useState('');
  const [instructions, setInstructions] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [envelope, setEnvelope] = useState<Envelope | null>(null);
  const [review, setReview] = useState<Review>(emptyReview);
  const [busy, setBusy] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const revision = useRef(0);
  function invalidate(source = false) {
    revision.current += 1;
    onInvalidate();
    setApproved(false);
    setBusy(false);
    setError(null);
    if (source) {
      setEnvelope(null);
      setReview(emptyReview());
    }
  }
  function changeReview(next: Review) {
    invalidate();
    setReview(next);
  }
  async function submit(operation: 'interpret-specification' | 'approve-requirements') {
    invalidate();
    const currentRevision = revision.current;
    setBusy(true);
    try {
      const form = new FormData();
      form.set('specification', specification);
      form.set('instructions', instructions);
      if (file) form.set('document', file);
      const res = await fetch(`/api/digital-engineer/${operation}`, {
        method: 'POST',
        ...(operation === 'approve-requirements'
          ? {
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...envelope, review }),
            }
          : { body: form }),
        signal: AbortSignal.timeout(operation === 'interpret-specification' ? 160000 : 20000),
      });
      const body: unknown = await res.json();
      if (currentRevision !== revision.current) return;
      if (!res.ok) {
        const e = errorSchema.parse(body).error;
        throw new Error(e.issues.map((i) => `${i.path}: ${i.message}`).join('\n') || e.message);
      }
      if (operation === 'interpret-specification') {
        setEnvelope(envelopeSchema.parse(body));
        setReview(emptyReview());
      } else {
        onApproved(validationResponseSchema.parse(body).requirements);
        setApproved(true);
      }
    } catch (e) {
      if (currentRevision === revision.current)
        setError(e instanceof Error ? e.message : 'The request could not complete.');
    } finally {
      if (currentRevision === revision.current) setBusy(false);
    }
  }
  const draft = envelope?.draft;
  const values = draft ? effectiveValues(draft, review) : new Map();
  const pending = draft ? blockers(draft, review) : [];
  const conflicts = draft
    ? [...Map.groupBy(draft.facts, factKey)].filter(([, facts]) =>
        facts.some((fact) => !sameValue(fact, facts[0], values.get('outputs'))),
      )
    : [];
  function correct(
    field: Correction['field'],
    component: string | null,
    value: Correction['value'],
    unit: Correction['unit'],
  ) {
    const item = {
      field,
      component,
      value,
      unit,
      note: 'Value explicitly entered or confirmed by the user in the engineering review.',
    };
    changeReview({
      ...review,
      corrections: [...review.corrections.filter((c) => factKey(c) !== factKey(item)), item],
    });
  }
  function renderFields(fields: ReturnType<typeof reviewFields>) {
    return (
      <div className={styles.fieldGrid}>
        {fields.map((f) => {
          const key = factKey(f),
            originalValue = values.get(key);
          const value =
            originalValue?.unit === 'text'
              ? normalize(originalValue, values.get('outputs'))
              : originalValue;
          const numeric = unitsFor(f.field)[0] !== 'text';
          const missing = numeric && f.field !== 'total_flow' && isMissingValue(value);
          const unit = value?.unit || unitsFor(f.field)[0];
          const label = `${f.component ? f.component + ' — ' : ''}${labels[f.field]}`;
          const evidence = draft!.facts
            .map((fact, index) => ({ fact, index }))
            .filter(({ fact }) => factKey(fact) === key);
          const correction = review.corrections.find((c) => factKey(c) === key);
          return (
            <div
              className={`${styles.field} ${missing ? styles.missingField : ''}`}
              data-missing={missing || undefined}
              key={key}
            >
              <label htmlFor={'review-' + key}>{label}</label>
              <div className={styles.valueRow}>
                {['equipment', 'topology', 'outputs'].includes(f.field) ? (
                  <select
                    id={'review-' + key}
                    value={value?.value ?? ''}
                    onChange={(e) => correct(f.field, f.component, e.target.value, 'text')}
                  >
                    <option value="">Select after reviewing the source</option>
                    {value?.value &&
                      ![
                        capabilityManifest.equipment,
                        capabilityManifest.topology,
                        capabilityManifest.outputs,
                      ].includes(String(value.value) as typeof capabilityManifest.equipment) && (
                        <option value={String(value.value)}>{value.value} — unsupported</option>
                      )}
                    <option
                      value={
                        f.field === 'equipment'
                          ? capabilityManifest.equipment
                          : f.field === 'topology'
                            ? capabilityManifest.topology
                            : capabilityManifest.outputs
                      }
                    >
                      {f.field === 'equipment'
                        ? 'Three-Phase Separator'
                        : f.field === 'topology'
                          ? 'One feed → one separator → gas + oil + water'
                          : 'Gas, oil, water; streams and mass/energy balances'}
                    </option>
                  </select>
                ) : (
                  <input
                    id={'review-' + key}
                    type={numeric ? 'number' : 'text'}
                    step={numeric ? 'any' : undefined}
                    value={value?.value ?? ''}
                    placeholder="Not specified"
                    aria-invalid={missing || undefined}
                    aria-describedby={missing ? 'missing-' + key : undefined}
                    onChange={(e) =>
                      correct(
                        f.field,
                        f.component,
                        numeric && e.target.value !== '' ? Number(e.target.value) : e.target.value,
                        unit,
                      )
                    }
                  />
                )}
                {numeric && (
                  <select
                    aria-label={`${label} unit`}
                    value={unit}
                    onChange={(e) =>
                      correct(
                        f.field,
                        f.component,
                        value?.value ?? '',
                        e.target.value as Correction['unit'],
                      )
                    }
                  >
                    {!unitsFor(f.field).includes(unit) && (
                      <option value={unit}>{unit} — clarify</option>
                    )}
                    {unitsFor(f.field).map((u) => (
                      <option value={u} key={u}>
                        {u === 'Pa_abs' ? 'Pa abs' : u === 'bar_abs' ? 'bar abs' : u}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              {missing && <small id={'missing-' + key}>Required — missing</small>}
              <small>
                {correction
                  ? 'User-specified / reviewed; earlier interpretation preserved below.'
                  : value
                    ? 'Interpreted — review evidence before approval.'
                    : f.field === 'total_flow'
                      ? 'Optional when all component mass flows are supplied.'
                      : 'Not supplied.'}
              </small>
              {!!evidence.length && (
                <details>
                  <summary>Source evidence ({evidence.length})</summary>
                  {evidence.map(({ fact, index }) => (
                    <div key={index} className={styles.evidence}>
                      <strong>
                        {fact.evidence.source_type === 'uploaded_document'
                          ? 'Document'
                          : fact.evidence.source_id === 'instructions'
                            ? 'Additional user instruction'
                            : 'Typed specification'}
                        {fact.evidence.page ? ` · page ${fact.evidence.page}` : ''}
                      </strong>
                      <p>
                        {fact.value} {fact.unit === 'text' ? '' : fact.unit} · {fact.origin} ·{' '}
                        {fact.confidence} confidence
                      </p>
                      <blockquote>{fact.evidence.excerpt}</blockquote>
                      <button
                        className={styles.secondary}
                        onClick={() => correct(f.field, f.component, fact.value, fact.unit)}
                      >
                        Use / confirm this value for {label}
                      </button>
                    </div>
                  ))}
                </details>
              )}
            </div>
          );
        })}
      </div>
    );
  }
  const formFields = draft ? reviewFields(draft, review) : [];
  const select = (names: string[]) => formFields.filter((f) => names.includes(f.field));
  return (
    <>
      <section className={styles.panel} aria-labelledby="spec-title">
        <span className={styles.eyebrow}>01 / Specification</span>
        <h2 id="spec-title">Engineering specification</h2>
        <p>
          <strong>Current engineering scope: Three-Phase Separator — Development Model</strong>
        </p>
        <label htmlFor="spec-pdf">Upload Technical Specification PDF</label>
        <input
          id="spec-pdf"
          type="file"
          accept="application/pdf,.pdf"
          onChange={(e) => {
            invalidate(true);
            setFile(e.target.files?.[0] || null);
          }}
        />
        <p>
          Text-based PDF only · up to 5 MiB and 40 pages · no OCR. Uploaded files are processed in
          memory and discarded.
        </p>
        <label htmlFor="spec-text">Describe or paste your engineering specification</label>
        <textarea
          id="spec-text"
          className={styles.specText}
          maxLength={20000}
          value={specification}
          placeholder="Describe the feed, separator conditions, component flows, prescribed recoveries and caloric assumptions. Missing values will be requested for review."
          onChange={(e) => {
            invalidate(true);
            setSpecification(e.target.value);
          }}
        />
        <label htmlFor="spec-instructions">Additional instructions (optional)</label>
        <textarea
          id="spec-instructions"
          className={styles.instructions}
          maxLength={20000}
          value={instructions}
          onChange={(e) => {
            invalidate(true);
            setInstructions(e.target.value);
          }}
        />
        <p>
          PDF, typed specification and additional instructions retain separate evidence.
          Interpretation sends extracted text to the server-configured provider.
        </p>
        <button
          disabled={busy || (!file && !specification.trim() && !instructions.trim())}
          onClick={() => void submit('interpret-specification')}
        >
          Interpret specification
        </button>
        <p aria-live="polite">
          {busy
            ? 'Processing specification / review…'
            : approved
              ? 'Requirements approved and deterministically validated. Generate the PFD below.'
              : draft
                ? 'Interpretation ready. Review all values and evidence below.'
                : 'Interpretation will not run an engineering calculation.'}
        </p>
        {error && (
          <pre aria-label="Specification error" role="alert" className={styles.error}>
            {error}
          </pre>
        )}
      </section>
      {draft && (
        <section className={styles.panel} aria-labelledby="understood-title">
          <span className={styles.eyebrow}>02–03 / Interpretation · Review &amp; approve</span>
          <h2 id="understood-title">WHAT RIOGINEER UNDERSTOOD</h2>
          <p>
            Correct or complete the fields below. Units must be explicit; pressure is absolute.
            Changes invalidate approval, PFD and previous results.
          </p>
          <h3>Process</h3>
          {renderFields(select(['equipment', 'topology']))}
          <h3>Feed</h3>
          {renderFields(
            select([
              'components',
              'total_flow',
              'feed_temperature',
              'feed_pressure',
              'component_flow',
            ]),
          )}
          <h3>Separator operating conditions</h3>
          {renderFields(select(['separator_temperature', 'separator_pressure']))}
          <h3>Separation model</h3>
          <p>Prescribed Component Recoveries — Development Model</p>
          <h3>Model inputs</h3>
          {renderFields(
            select([
              'reference_temperature',
              'cp',
              'recovery_gas',
              'recovery_oil',
              'recovery_water',
            ]),
          )}
          <h3>Outputs</h3>
          <p>
            Gas · Oil · Water. Available calculations: stream conditions, mass balance and
            constant-Cp energy accounting.
          </p>
          {renderFields(select(['outputs']))}
          <h3>Assumptions requiring approval</h3>
          {!draft.facts.some((f) => f.origin === 'assumed') && (
            <p>No proposed engineering assumptions.</p>
          )}
          {draft.facts.map((f, index) =>
            f.origin !== 'assumed' ? null : (
              <div key={index} className={styles.evidence}>
                <p>
                  <strong>
                    {f.component ? f.component + ' — ' : ''}
                    {labels[f.field]}: {f.value} {f.unit}
                  </strong>
                </p>
                <blockquote>{f.evidence.excerpt}</blockquote>
                <label>
                  Assumption {index + 1} decision
                  <select
                    value={review.assumptions[String(index)] || ''}
                    onChange={(e) =>
                      changeReview({
                        ...review,
                        assumptions: {
                          ...review.assumptions,
                          [index]: e.target.value as 'accepted' | 'rejected',
                        },
                      })
                    }
                  >
                    <option value="" disabled>
                      Choose explicitly
                    </option>
                    <option value="accepted">Accept proposed assumption</option>
                    <option value="rejected">
                      Reject (supply a replacement above if required)
                    </option>
                  </select>
                </label>
              </div>
            ),
          )}
          {(['missing', 'ambiguity', 'conflict', 'unsupported', 'scope_exclusion'] as const).map(
            (kind) => (
              <div key={kind}>
                <h3>
                  {
                    {
                      missing: 'Missing information',
                      ambiguity: 'Ambiguities',
                      conflict: 'Conflicts',
                      unsupported: 'Unsupported requests',
                      scope_exclusion: 'Source scope exclusions',
                    }[kind]
                  }
                </h3>
                {kind === 'missing' && (
                  <p>Complete the required highlighted engineering inputs before approval.</p>
                )}
                {kind === 'conflict' &&
                  conflicts.map(([key, facts]) => (
                    <div className={styles.evidence} key={key}>
                      <strong>
                        {review.corrections.some((c) => factKey(c) === key)
                          ? 'Resolved by user'
                          : 'CONFLICT DETECTED'}{' '}
                        — {labels[facts[0].field]}
                        {facts[0].component ? ` (${facts[0].component})` : ''}
                      </strong>
                      {facts.map((fact, index) => (
                        <p key={index}>
                          {fact.evidence.source_type === 'uploaded_document'
                            ? 'Document'
                            : fact.evidence.source_id === 'instructions'
                              ? 'Additional user instruction'
                              : 'Typed specification'}
                          : {fact.value} {fact.unit === 'text' ? '' : fact.unit}
                        </p>
                      ))}
                      <p>
                        Select a source value in the evidence panel above, or enter a replacement.
                        All alternatives remain in provenance.
                      </p>
                      <label>
                        Resolution note for {labels[facts[0].field]}
                        {facts[0].component ? ` (${facts[0].component})` : ''}
                        <input
                          value={review.resolutions[`conflict:${key}`] || ''}
                          onChange={(e) =>
                            changeReview({
                              ...review,
                              resolutions: {
                                ...review.resolutions,
                                [`conflict:${key}`]: e.target.value,
                              },
                            })
                          }
                        />
                      </label>
                    </div>
                  ))}
                {draft.issues
                  .filter((i) => i.kind === kind && !isOrdinaryMissingInput(i, draft, review))
                  .map((issue) => (
                    <div key={issue.id} className={styles.evidence}>
                      <p>
                        {issue.kind === 'unsupported' ? 'UNSUPPORTED CAPABILITY: ' : ''}
                        {kind === 'scope_exclusion' ? issue.evidence?.excerpt : issue.message}
                      </p>
                      {kind !== 'unsupported' && kind !== 'scope_exclusion' && (
                        <label>
                          Resolution note
                          <input
                            value={review.resolutions[issue.id] || ''}
                            placeholder="Explain the correction, then update the related field"
                            onChange={(e) =>
                              changeReview({
                                ...review,
                                resolutions: { ...review.resolutions, [issue.id]: e.target.value },
                              })
                            }
                          />
                        </label>
                      )}
                    </div>
                  ))}
                {kind !== 'missing' && !draft.issues.some((i) => i.kind === kind) && (
                  <p>
                    {kind === 'conflict' && conflicts.length
                      ? 'Resolve each conflicting field explicitly before approval.'
                      : kind === 'scope_exclusion'
                        ? 'No explicit scope exclusions reported by the interpreter.'
                        : `No ${kind} issues reported by the interpreter. See the required review checks below.`}
                  </p>
                )}
              </div>
            ),
          )}
          <label className={styles.check}>
            <input
              type="checkbox"
              checked={review.model_accepted}
              onChange={(e) => changeReview({ ...review, model_accepted: e.target.checked })}
            />
            I approve use of prescribed component recoveries and assumed constant heat capacities
            for this development calculation. No rigorous equilibrium, separator sizing or
            geometry-based efficiency is predicted.
          </label>
          <h3>Required review checks</h3>
          {pending.length ? (
            <ul className={styles.blockers}>
              {pending.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          ) : (
            <p aria-live="polite" className={approved ? styles.status : undefined}>
              {approved
                ? 'Requirements approved and deterministically validated. Next: Generate PFD below.'
                : 'Review complete. Approval will run mandatory deterministic validation.'}
            </p>
          )}
          <button
            disabled={busy || approved || pending.length > 0}
            onClick={() => void submit('approve-requirements')}
          >
            {approved ? 'Requirements approved' : 'Approve requirements'}
          </button>
        </section>
      )}
    </>
  );
}
