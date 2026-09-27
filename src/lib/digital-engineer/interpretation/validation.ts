import { anchorEvidence } from './anchoring';
import { randomUUID } from 'node:crypto';
import {
  componentFields,
  fields,
  interpretationSchema,
  factKey,
  emptyReview,
  type Fact,
  type Source,
  type Draft,
} from './contracts';
import { InterpretationError } from './http';
import { isExplicitScopeExclusion } from './scope';
import { componentIds, effectiveValues } from './review';

// Only allowlisted field names, indices and rule codes enter development logs.
// Never log Zod messages, unknown keys, source text, values, provider bodies or errors.
const pathKeys = new Set<string>([
  'facts',
  'issues',
  'field',
  'component',
  'value',
  'unit',
  'origin',
  'evidence',
  'confidence',
  'source_id',
  'source_type',
  'excerpt',
  'page',
  'kind',
  'message',
]);
function diagnostic(stage: 'schema' | 'evidence', failures: object[]) {
  if (process.env.NODE_ENV === 'development')
    console.warn(
      '[riogineer:interpretation-validation]',
      JSON.stringify({
        event_id: randomUUID(),
        stage,
        failures,
      }),
    );
}

export function parseProviderInterpretation(raw: unknown) {
  const result = interpretationSchema.safeParse(raw);
  if (result.success) return result.data;
  diagnostic(
    'schema',
    result.error.issues.map((issue) => ({
      path: issue.path
        .map((part) =>
          typeof part === 'number' || (typeof part === 'string' && pathKeys.has(part))
            ? part
            : '[unknown]',
        )
        .join('.'),
      reason: issue.code,
      // The schema rejects unknown fields (including model/capability metadata).
      // Never print the rejected value or an unknown property name.
      field: (() => {
        const index = issue.path[0] === 'facts' ? issue.path[1] : undefined;
        const fact =
          typeof raw === 'object' &&
          raw !== null &&
          'facts' in raw &&
          Array.isArray(raw.facts) &&
          typeof index === 'number'
            ? raw.facts[index]
            : null;
        return fact && fields.includes(fact.field) ? fact.field : null;
      })(),
    })),
  );
  throw new InterpretationError(
    'PROVIDER_MALFORMED',
    'The provider returned data outside the interpretation contract.',
    502,
  );
}

export function validateProviderEvidence(facts: Fact[], source: Source, sourceIndex: number) {
  const failures = facts.flatMap((fact, factIndex) => {
    const reasons: string[] = [];
    if (fact.evidence.source_id !== source.id) reasons.push('source_id_mismatch');
    if (fact.evidence.source_type !== source.type) reasons.push('source_type_mismatch');
    const pages = source.pages.filter((page) => page.page === fact.evidence.page);
    if (!pages.length) reasons.push('page_not_found');
    else if (pages.length !== 1) reasons.push('excerpt_ambiguous');
    else {
      const anchored = anchorEvidence(pages[0].text, fact.evidence.excerpt);
      if ('reason' in anchored) reasons.push(anchored.reason);
      else if (anchored.excerpt !== fact.evidence.excerpt) {
        fact.evidence = {
          ...fact.evidence,
          provider_excerpt: fact.evidence.excerpt,
          excerpt: anchored.excerpt,
          source_start: anchored.start,
          source_end: anchored.end,
        };
      }
    }
    if (componentFields.includes(fact.field) !== (fact.component !== null))
      reasons.push('component_scope_mismatch');
    if (fact.origin === 'derived') reasons.push('derived_origin_forbidden');
    return reasons.map((reason) => ({
      source_index: sourceIndex,
      fact_index: factIndex,
      field: fact.field,
      reason,
    }));
  });
  if (!failures.length) return;
  diagnostic('evidence', failures);
  throw new InterpretationError(
    'PROVIDER_EVIDENCE',
    'The provider returned an unsupported derived fact or evidence that does not match the source. No requirements were approved.',
    502,
  );
}

export function validateIssueEvidence(
  issues: Draft['issues'],
  source: Source,
  sourceIndex: number,
) {
  const failures = issues.flatMap((issue, issueIndex) => {
    const reasons: string[] = [];
    if (issue.evidence) {
      const evidence = issue.evidence;
      const pages = source.pages.filter((page) => page.page === evidence.page);
      const anchored = pages.length === 1 ? anchorEvidence(pages[0].text, evidence.excerpt) : null;
      if (
        evidence.source_id !== source.id ||
        evidence.source_type !== source.type ||
        !anchored ||
        'reason' in anchored
      )
        reasons.push(
          anchored && 'reason' in anchored && anchored.reason === 'excerpt_ambiguous'
            ? 'issue_evidence_ambiguous'
            : 'issue_evidence_not_exact',
        );
      else if (anchored.excerpt !== evidence.excerpt)
        issue.evidence = {
          ...evidence,
          provider_excerpt: evidence.excerpt,
          excerpt: anchored.excerpt,
          source_start: anchored.start,
          source_end: anchored.end,
        };
    }
    if (issue.kind === 'scope_exclusion' && !isExplicitScopeExclusion(issue.evidence?.excerpt))
      reasons.push('not_an_explicit_scope_exclusion');
    return reasons.map((reason) => ({
      source_index: sourceIndex,
      issue_index: issueIndex,
      reason,
    }));
  });
  if (!failures.length) return;
  diagnostic('evidence', failures);
  throw new InterpretationError(
    'PROVIDER_EVIDENCE',
    'The provider returned an invalid source statement or evidence. No requirements were approved.',
    502,
  );
}

// Successful extraction also needs diagnostics: rejection-only logs cannot explain
// facts returned under aliases, omitted facts, or assumptions awaiting acceptance.
export function reviewCoverage(draft: Draft) {
  const values = effectiveValues(draft, emptyReview());
  const basis = componentIds(values);
  const fields = basis.flatMap((component, componentIndex) =>
    componentFields.map((field) => {
      const key = factKey({ field, component });
      const candidates = draft.facts.flatMap((fact, index) =>
        factKey(fact) === key ? [{ fact, index }] : [],
      );
      return {
        component_index: componentIndex,
        field,
        returned_fact_indices: candidates.map(({ index }) => index),
        identity_mapped: candidates.some(({ fact }) => fact.component !== component),
        state: values.has(key)
          ? 'populated'
          : candidates.some(({ fact }) => fact.origin === 'assumed')
            ? 'awaiting_assumption_review'
            : 'not_returned_for_component',
      };
    }),
  );
  const orphanFactIndices = draft.facts.flatMap((fact, index) =>
    fact.component &&
    !basis.some((component) => factKey({ field: fact.field, component }) === factKey(fact))
      ? [index]
      : [],
  );
  return {
    registered_components: basis.length,
    component_fields: fields,
    orphan_fact_indices: orphanFactIndices,
  };
}
export function logReviewCoverage(draft: Draft) {
  if (process.env.NODE_ENV !== 'development') return;
  console.info(
    '[riogineer:interpretation-review]',
    JSON.stringify({
      event_id: randomUUID(),
      ...reviewCoverage(draft),
      scope_exclusions: draft.issues.filter((i) => i.kind === 'scope_exclusion').length,
      unsupported_requests: draft.issues.filter((i) => i.kind === 'unsupported').length,
    }),
  );
}
