import { contactSchema } from './validation';
import { contactAvailability, contactLimits } from '@/config/contact';
import { resolveSiteConfig } from '@/config/site';

// Small process-wide ceiling for a disabled endpoint. No IP addresses or form data are retained.
// Replace with a shared, provider-backed abuse control before enabling delivery on serverless hosting.
export function createRequestLimiter(max = 60, windowMs = 60000) {
  let count = 0;
  let reset = 0;
  return (now = Date.now()) => {
    if (now >= reset) {
      count = 0;
      reset = now + windowMs;
    }
    return ++count <= max;
  };
}
const permitRequest = createRequestLimiter();
function response(status: number, body: Record<string, unknown>) {
  return Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
}
class PayloadTooLarge extends Error {}
async function readLimitedBody(request: Request) {
  if (Number(request.headers.get('content-length') || 0) > contactLimits.bodyBytes)
    throw new PayloadTooLarge();
  const reader = request.body?.getReader();
  if (!reader) return '';
  const decoder = new TextDecoder();
  let bytes = 0;
  let text = '';
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > contactLimits.bodyBytes) {
        await reader.cancel();
        throw new PayloadTooLarge();
      }
      text += decoder.decode(value, { stream: true });
    }
    return text + decoder.decode();
  } finally {
    reader.releaseLock();
  }
}
export async function handleContactRequest(request: Request, limiter = permitRequest) {
  const config = resolveSiteConfig(process.env);
  const allowedOrigins = new Set([config.url]);
  if (
    new URL(config.url).hostname === 'localhost' ||
    new URL(config.url).hostname === '127.0.0.1'
  ) {
    const port = new URL(config.url).port;
    allowedOrigins.add(`http://localhost${port ? `:${port}` : ''}`);
    allowedOrigins.add(`http://127.0.0.1${port ? `:${port}` : ''}`);
  }
  if (!allowedOrigins.has(request.headers.get('origin') || ''))
    return response(403, { message: 'This request origin is not allowed.' });
  if (!limiter()) return response(429, { message: 'Too many requests. Please try again later.' });
  if (request.headers.get('content-type')?.split(';')[0].trim() !== 'application/json')
    return response(415, { message: 'Use a JSON request.' });
  let raw: unknown;
  try {
    raw = JSON.parse(await readLimitedBody(request));
  } catch (error) {
    return response(error instanceof PayloadTooLarge ? 413 : 400, {
      message:
        error instanceof PayloadTooLarge
          ? 'The submission is too large.'
          : 'The submission could not be read.',
    });
  }
  const parsed = contactSchema.safeParse(raw);
  if (!parsed.success)
    return response(422, {
      message: 'Check the highlighted fields.',
      errors: parsed.error.flatten().fieldErrors,
    });
  if (parsed.data.website)
    return response(400, { message: 'The submission could not be accepted.' });
  // Deliberately no delivery adapter, external request, logging, database, or persistence.
  // A valid submission is NOT a sent message. There is no environment flag that enables delivery.
  return response(503, { code: 'DELIVERY_DISABLED', message: contactAvailability.message });
}
