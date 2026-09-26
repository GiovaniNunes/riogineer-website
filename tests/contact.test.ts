import { afterEach, describe, expect, it, vi } from 'vitest';
import { handleContactRequest, createRequestLimiter } from '@/lib/contact';
import { contactLimits } from '@/config/contact';
const valid = {
  name: 'Test Engineer',
  company: 'Example Organization',
  email: 'engineer@example.com',
  country: 'Brazil',
  interest: 'Process Engineering',
  message: 'I would like to discuss a demonstration.',
  website: '',
};
function request(
  body: unknown = valid,
  origin = 'http://localhost:3000',
  type = 'application/json',
) {
  return new Request('http://localhost:3000/api/contact', {
    method: 'POST',
    headers: { Origin: origin, 'Content-Type': type },
    body: JSON.stringify(body),
  });
}
afterEach(() => vi.unstubAllEnvs());
describe('contact endpoint', () => {
  it('validates a legitimate submission but never reports delivery', async () => {
    vi.stubEnv('SITE_URL', 'http://localhost:3000');
    const response = await handleContactRequest(request(), () => true);
    expect(response.status).toBe(503);
    expect(response.headers.get('cache-control')).toBe('no-store');
    const body = await response.json();
    expect(body.code).toBe('DELIVERY_DISABLED');
    expect(body.message).toContain('will not be sent or saved');
  });
  it('accepts the loopback development alias', async () => {
    const response = await handleContactRequest(
      request(valid, 'http://127.0.0.1:3000'),
      () => true,
    );
    expect(response.status).toBe(503);
  });
  it('rejects untrusted and missing origins', async () => {
    for (const origin of ['https://untrusted.example', ''])
      expect((await handleContactRequest(request(valid, origin), () => true)).status).toBe(403);
  });
  it('uses the configured origin for non-local sites', async () => {
    vi.stubEnv('SITE_URL', 'https://preview.example');
    expect(
      (await handleContactRequest(request(valid, 'http://localhost:3000'), () => true)).status,
    ).toBe(403);
    expect(
      (await handleContactRequest(request(valid, 'https://preview.example'), () => true)).status,
    ).toBe(503);
  });
  it('rejects invalid fields with actionable errors', async () => {
    const response = await handleContactRequest(
      request({
        ...valid,
        email: 'not-an-email',
        name: ' ',
        interest: 'Invalid',
        message: 'short',
      }),
      () => true,
    );
    expect(response.status).toBe(422);
    const body = await response.json();
    for (const field of ['email', 'name', 'interest', 'message'])
      expect(body.errors[field]).toBeDefined();
  });
  it('rejects a populated honeypot', async () => {
    expect(
      (await handleContactRequest(request({ ...valid, website: 'spam.example' }), () => true))
        .status,
    ).toBe(400);
  });
  it('rejects unexpected fields instead of accepting provider settings', async () => {
    expect(
      (await handleContactRequest(request({ ...valid, deliveryEnabled: true }), () => true)).status,
    ).toBe(422);
  });
  it('enforces payload limits even without Content-Length', async () => {
    expect(
      (
        await handleContactRequest(
          request({ ...valid, message: 'x'.repeat(contactLimits.bodyBytes) }),
          () => true,
        )
      ).status,
    ).toBe(413);
  });
  it('rejects malformed JSON and non-JSON submissions', async () => {
    const malformed = new Request('http://localhost:3000/api/contact', {
      method: 'POST',
      headers: { Origin: 'http://localhost:3000', 'Content-Type': 'application/json' },
      body: '{invalid',
    });
    expect((await handleContactRequest(malformed, () => true)).status).toBe(400);
    expect(
      (
        await handleContactRequest(
          request(valid, 'http://localhost:3000', 'text/plain'),
          () => true,
        )
      ).status,
    ).toBe(415);
  });
  it('honors the abuse-control ceiling', async () => {
    expect((await handleContactRequest(request(), () => false)).status).toBe(429);
    const limiter = createRequestLimiter(2, 1000);
    expect(limiter(0)).toBe(true);
    expect(limiter(1)).toBe(true);
    expect(limiter(2)).toBe(false);
    expect(limiter(1000)).toBe(true);
  });
});
