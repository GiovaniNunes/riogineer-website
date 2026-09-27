export class InterpretationError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 422,
  ) {
    super(message);
  }
}
export async function boundedBytes(body: ReadableStream<Uint8Array> | null, limit: number) {
  if (!body) return new Uint8Array();
  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > limit) {
        await reader.cancel();
        throw new InterpretationError(
          'BODY_TOO_LARGE',
          'Request or response exceeds the supported size limit.',
          413,
        );
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const output = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.length;
  }
  return output;
}
export function checkOrigin(request: Request) {
  const url = new URL(request.url);
  const origins = new Set([url.origin]);
  if (url.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname))
    for (const host of ['localhost', '127.0.0.1', '[::1]'])
      origins.add(`http://${host}${url.port ? ':' + url.port : ''}`);
  if (!origins.has(request.headers.get('origin') || ''))
    throw new InterpretationError('ORIGIN', 'Request origin is not allowed.', 403);
}
export function response(body: unknown, status = 200) {
  return Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
}
export function failure(error: unknown) {
  const e =
    error instanceof InterpretationError
      ? error
      : new InterpretationError(
          'INVALID_REQUEST',
          'The interpretation request could not be processed. Check the supplied fields and retry.',
          400,
        );
  return response({ error: { code: e.code, message: e.message, issues: [] } }, e.status);
}
