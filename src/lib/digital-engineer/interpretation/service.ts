import { createHash, createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import {
  draftSchema,
  approvalSchema,
  sourceSchema,
  type Draft,
  type Envelope,
  type Source,
} from './contracts';
import { capabilityManifest, finalizeRequirements } from './review';
import { configuredProvider, type InterpretationProvider } from './provider';
import { extractPdf, MAX_PDF_BYTES } from './pdf';
import { boundedBytes, checkOrigin, failure, InterpretationError, response } from './http';
import { handleEngineeringRequest } from '../api';
import {
  parseProviderInterpretation,
  validateProviderEvidence,
  validateIssueEvidence,
  logReviewCoverage,
} from './validation';

// Process-lifetime signing prevents clients from deleting original facts/issues. No draft storage.
const serverState = globalThis as typeof globalThis & { riogineerReviewKey?: string };
const signingKey =
  process.env.RIOGINEER_REVIEW_SECRET ||
  (serverState.riogineerReviewKey ??= randomBytes(32).toString('hex'));
function signature(draft: Draft) {
  return createHmac('sha256', signingKey).update(JSON.stringify(draft)).digest('hex');
}
export function sealDraft(draft: Draft): Envelope {
  const parsed = draftSchema.parse(draft);
  return { draft: parsed, signature: signature(parsed) };
}
function verify(envelope: Envelope) {
  if (
    !timingSafeEqual(
      Buffer.from(envelope.signature, 'hex'),
      Buffer.from(signature(envelope.draft), 'hex'),
    )
  )
    throw new InterpretationError(
      'DRAFT_CHANGED',
      'The original interpretation changed or the server restarted. Interpret the specification again.',
      409,
    );
}
export async function interpretSources(
  sources: Source[],
  provider: InterpretationProvider,
): Promise<Envelope> {
  const facts: Draft['facts'] = [],
    issues: Draft['issues'] = [];
  // Separate source calls avoid an implicit preference for later user instructions over a PDF.
  for (const [sourceIndex, source] of sources.entries()) {
    const result = parseProviderInterpretation(
      await provider.interpret_specification(source, capabilityManifest),
    );
    validateProviderEvidence(result.facts, source, sourceIndex);
    facts.push(...result.facts);
    const sourceIssues = result.issues.map((i) => ({ ...i, id: randomUUID() }));
    validateIssueEvidence(sourceIssues, source, sourceIndex);
    issues.push(...sourceIssues);
  }
  const envelope = sealDraft({
    version: '1.0',
    id: randomUUID(),
    created_at: new Date().toISOString(),
    provider: provider.name,
    sources: sources.map((s) => ({
      id: s.id,
      type: s.type,
      label: s.label,
      pages: s.pages,
      sha256: createHash('sha256').update(JSON.stringify(s.pages)).digest('hex'),
    })),
    facts,
    issues,
  });
  logReviewCoverage(envelope.draft);
  return envelope;
}
async function sourcesFromRequest(
  request: Request,
): Promise<{ sources: Source[]; notices: string[] }> {
  if (!request.headers.get('content-type')?.startsWith('multipart/form-data;'))
    throw new InterpretationError(
      'CONTENT_TYPE',
      'Use a PDF upload and/or specification text.',
      415,
    );
  const bytes = await boundedBytes(request.body, MAX_PDF_BYTES + 256000);
  const form = await new Request(request.url, {
    method: 'POST',
    headers: { 'Content-Type': request.headers.get('content-type')! },
    body: bytes.buffer as ArrayBuffer,
  }).formData();
  if (
    [...form.keys()].some((k) => !['document', 'specification', 'instructions'].includes(k)) ||
    [...new Set(form.keys())].some((k) => form.getAll(k).length !== 1)
  )
    throw new InterpretationError('INVALID_FORM', 'Unexpected or duplicate input field.');
  const sources: Source[] = [],
    notices: string[] = [];
  const doc = form.get('document');
  if (doc !== null) {
    if (typeof doc === 'string')
      throw new InterpretationError('PDF_TYPE', 'Upload a PDF file.', 415);
    const result = await extractPdf(doc);
    sources.push({
      id: 'document',
      type: 'uploaded_document',
      label: doc.name.split(/[\\/]/).pop()!.slice(0, 200),
      pages: result.pages,
    });
    if (result.empty_pages.length)
      notices.push(
        `Pages ${result.empty_pages.join(', ')} contain no machine-readable text. Their content was not interpreted. Confirm that no engineering requirements are missing.`,
      );
  }
  for (const key of ['specification', 'instructions']) {
    const value = form.get(key);
    if (value !== null && typeof value !== 'string')
      throw new InterpretationError('INVALID_TEXT', 'Specification and instructions must be text.');
    if (typeof value === 'string' && value.trim()) {
      if (value.length > 20000)
        throw new InterpretationError(
          'TEXT_LIMIT',
          'Each text field is limited to 20,000 characters.',
          413,
        );
      sources.push({
        id: key,
        type: 'user_text',
        label: key === 'specification' ? 'Typed specification' : 'Additional user instructions',
        pages: [{ page: null, text: value }],
      });
    }
  }
  if (!sources.length)
    throw new InterpretationError(
      'EMPTY_SPECIFICATION',
      'Upload a PDF or enter an engineering specification.',
    );
  return { sources: sources.map((s) => sourceSchema.parse(s)), notices };
}
export async function handleInterpretRequest(request: Request, provider?: InterpretationProvider) {
  try {
    checkOrigin(request);
    const { sources, notices } = await sourcesFromRequest(request);
    const envelope = await interpretSources(sources, provider || configuredProvider());
    for (const notice of notices)
      envelope.draft.issues.push({
        id: randomUUID(),
        kind: 'ambiguity',
        field: null,
        component: null,
        message: notice,
      });
    return response(sealDraft(envelope.draft));
  } catch (e) {
    return failure(e);
  }
}
export async function handleApprovalRequest(request: Request, fetcher: typeof fetch = fetch) {
  try {
    checkOrigin(request);
    if (request.headers.get('content-type')?.split(';')[0] !== 'application/json')
      throw new InterpretationError('CONTENT_TYPE', 'Use application/json.', 415);
    const body = new TextDecoder('utf-8', { fatal: true }).decode(
      await boundedBytes(request.body, 524288),
    );
    const parsed = approvalSchema.safeParse(JSON.parse(body));
    if (!parsed.success)
      throw new InterpretationError(
        'INVALID_REVIEW',
        'The review does not match the interpretation contract.',
      );
    verify(parsed.data);
    let requirements;
    try {
      requirements = finalizeRequirements(
        parsed.data.draft,
        parsed.data.review,
        new Date().toISOString(),
      );
    } catch (e) {
      throw new InterpretationError(
        'APPROVAL_BLOCKED',
        e instanceof Error ? e.message : 'Resolve all review blockers before approval.',
      );
    }
    const raw = JSON.stringify(requirements);
    if (Buffer.byteLength(raw) > 131072)
      throw new InterpretationError(
        'AUDIT_SIZE_LIMIT',
        'The reviewed requirements exceed the engine document limit. Shorten the specification and interpret again.',
        413,
      );
    // Always call the unchanged deterministic validator before returning approved requirements.
    return handleEngineeringRequest(
      new Request(request.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Origin: request.headers.get('origin')! },
        body: raw,
      }),
      'validate-requirements',
      fetcher,
    );
  } catch (e) {
    return failure(e);
  }
}
