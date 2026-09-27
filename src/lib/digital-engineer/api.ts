import {
  requirementsSchema,
  flowsheetSchema,
  resultsSchema,
  validationResponseSchema,
  errorSchema,
} from './contracts';

const operations = {
  'validate-requirements': { input: requirementsSchema, output: validationResponseSchema },
  'build-flowsheet': { input: requirementsSchema, output: flowsheetSchema },
  calculate: { input: flowsheetSchema, output: resultsSchema },
} as const;
const MAX_BODY = 131072;
function reply(body: unknown, status = 200) {
  return Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
}
function error(status: number, code: string, message: string) {
  return reply(
    { error: { code, message, issues: [{ code, path: '/', severity: 'error', message }] } },
    status,
  );
}
async function boundedText(body: ReadableStream<Uint8Array> | null, limit: number) {
  if (!body) return '';
  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let text = '';
  let bytes = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > limit) {
        await reader.cancel();
        throw new RangeError('Body too large');
      }
      text += decoder.decode(value, { stream: true });
    }
    return text + decoder.decode();
  } finally {
    reader.releaseLock();
  }
}
export async function handleEngineeringRequest(
  request: Request,
  operation: string,
  fetcher: typeof fetch = fetch,
) {
  if (!Object.hasOwn(operations, operation)) return error(404, 'NOT_FOUND', 'Unknown operation.');
  if (request.method !== 'POST') return error(405, 'METHOD_NOT_ALLOWED', 'Use POST.');
  const requestUrl = new URL(request.url);
  const origins = new Set([requestUrl.origin]);
  // Next's local request URL may use localhost while the browser uses 127.0.0.1.
  if (
    requestUrl.protocol === 'http:' &&
    ['localhost', '127.0.0.1', '[::1]'].includes(requestUrl.hostname)
  ) {
    for (const host of ['localhost', '127.0.0.1', '[::1]'])
      origins.add(`http://${host}${requestUrl.port ? ':' + requestUrl.port : ''}`);
  }
  if (!origins.has(request.headers.get('origin') || ''))
    return error(403, 'ORIGIN', 'Request origin is not allowed.');
  if (request.headers.get('content-type')?.split(';')[0].trim() !== 'application/json')
    return error(415, 'CONTENT_TYPE', 'Use application/json.');
  const contract = operations[operation as keyof typeof operations];
  let raw: string;
  try {
    raw = await boundedText(request.body, MAX_BODY);
    const parsed = contract.input.safeParse(JSON.parse(raw));
    if (!parsed.success)
      return reply(
        {
          error: {
            code: 'VALIDATION_FAILED',
            message: 'The document does not match the versioned contract.',
            issues: parsed.error.issues.map((i) => ({
              code: 'VALIDATION_FAILED',
              path: '/' + i.path.join('/'),
              severity: 'error',
              message: i.message,
            })),
          },
        },
        422,
      );
  } catch (e) {
    return error(
      e instanceof RangeError ? 413 : 400,
      'INVALID_BODY',
      e instanceof RangeError ? 'Request body too large.' : 'Provide valid JSON.',
    );
  }
  try {
    const base = new URL(process.env.RIOGINEER_ENGINE_URL || 'http://127.0.0.1:8001');
    if (
      base.protocol !== 'http:' ||
      !['127.0.0.1', 'localhost', '[::1]'].includes(base.hostname) ||
      base.username ||
      base.password ||
      base.pathname !== '/' ||
      base.search ||
      base.hash
    ) {
      return error(503, 'ENGINE_CONFIGURATION', 'Milestone 1 requires a local engine URL.');
    }
    const response = await fetcher(new URL(`/v1/${operation}`, base), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: raw,
      cache: 'no-store',
      redirect: 'error',
      signal: AbortSignal.timeout(15000),
    });
    const data: unknown = JSON.parse(await boundedText(response.body, 2097152));
    if (!response.ok) {
      const parsed = errorSchema.safeParse(data);
      if (!parsed.success)
        return error(502, 'ENGINE_PROTOCOL', 'The engine returned an invalid error response.');
      return reply(parsed.data, response.status === 422 ? 422 : 502);
    }
    const parsed = contract.output.safeParse(data);
    if (!parsed.success)
      return error(
        502,
        'ENGINE_PROTOCOL',
        'The engine returned data outside the supported contract.',
      );
    if (operation === 'calculate') {
      const input = flowsheetSchema.parse(JSON.parse(raw));
      const result = resultsSchema.parse(parsed.data);
      const sameKeys = (a: string[], b: string[]) =>
        JSON.stringify(a.sort()) === JSON.stringify(b.sort());
      if (
        result.case_id !== input.case_id ||
        result.requirements_sha256 !== input.requirements_sha256 ||
        !sameKeys(
          Object.keys(result.streams),
          input.streams.map((s) => s.id),
        ) ||
        Object.values(result.streams).some(
          (s) => !sameKeys(Object.keys(s.component_mass_flow_kg_h), [...input.components]),
        )
      ) {
        return error(
          502,
          'ENGINE_PROTOCOL',
          'The engine result does not match the submitted case and stream basis.',
        );
      }
    }
    return reply(parsed.data);
  } catch {
    return error(
      503,
      'ENGINE_UNAVAILABLE',
      'The local Python engine is unavailable or its response could not be read. Start the engine and retry.',
    );
  }
}
