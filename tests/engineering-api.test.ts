import { afterEach, describe, expect, it, vi } from 'vitest';
import { handleEngineeringRequest } from '../src/lib/digital-engineer/api';
import {
  referenceRequirements as requirements,
  referenceFlowsheet as flowsheet,
  referenceResults as results,
} from './engine-fixture';
function request(body: unknown = requirements, headers: Record<string, string> = {}) {
  return new Request('http://localhost:3000/api/digital-engineer/build-flowsheet', {
    method: 'POST',
    headers: { origin: 'http://localhost:3000', 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
}
afterEach(() => vi.unstubAllEnvs());
describe('website to Python API boundary', () => {
  it('accepts same-port loopback aliases used by Next.js local requests', async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json(flowsheet));
    expect(
      (
        await handleEngineeringRequest(
          request(requirements, { origin: 'http://127.0.0.1:3000' }),
          'build-flowsheet',
          fetcher,
        )
      ).status,
    ).toBe(200);
    expect(
      (
        await handleEngineeringRequest(
          request(requirements, { origin: 'http://127.0.0.1:9999' }),
          'build-flowsheet',
          fetcher,
        )
      ).status,
    ).toBe(403);
  });
  it('rejects an otherwise schema-valid result with an empty or foreign stream basis', async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json({ ...results, streams: {} }));
    expect((await handleEngineeringRequest(request(flowsheet), 'calculate', fetcher)).status).toBe(
      502,
    );
  });
  it('forwards to the fixed local endpoint and validates the response', async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json(flowsheet));
    const response = await handleEngineeringRequest(request(), 'build-flowsheet', fetcher);
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('no-store');
    expect(String(fetcher.mock.calls[0][0])).toBe('http://127.0.0.1:8001/v1/build-flowsheet');
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual(requirements);
  });
  it('accepts actual Python calculation result', async () => {
    expect(
      (
        await handleEngineeringRequest(
          request(flowsheet),
          'calculate',
          vi.fn().mockResolvedValue(Response.json(results)),
        )
      ).status,
    ).toBe(200);
  });
  it.each([
    ['origin', 403],
    ['Content-Type', 415],
  ])('rejects invalid %s before invoking Python', async (header, status) => {
    const fetcher = vi.fn();
    const response = await handleEngineeringRequest(
      request(requirements, { [header]: 'invalid' }),
      'build-flowsheet',
      fetcher,
    );
    expect(response.status).toBe(status);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('rejects unknown operations, invalid schemas and oversized bodies', async () => {
    const fetcher = vi.fn();
    expect((await handleEngineeringRequest(request(), 'run-shell', fetcher)).status).toBe(404);
    expect((await handleEngineeringRequest(request({}), 'build-flowsheet', fetcher)).status).toBe(
      422,
    );
    expect(
      (
        await handleEngineeringRequest(
          request({ data: 'x'.repeat(140000) }),
          'build-flowsheet',
          fetcher,
        )
      ).status,
    ).toBe(413);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('reports unavailable engines without fabricated results', async () => {
    const response = await handleEngineeringRequest(
      request(),
      'build-flowsheet',
      vi.fn().mockRejectedValue(new Error('offline')),
    );
    expect(response.status).toBe(503);
    expect((await response.json()).error.code).toBe('ENGINE_UNAVAILABLE');
  });
  it('rejects malformed engine results', async () => {
    const response = await handleEngineeringRequest(
      request(flowsheet),
      'calculate',
      vi.fn().mockResolvedValue(Response.json({ status: 'completed' })),
    );
    expect(response.status).toBe(502);
  });
  it('preserves deterministic validation errors', async () => {
    const error = {
      error: {
        code: 'VALIDATION_FAILED',
        message: 'Recoveries must sum to one',
        issues: [
          {
            code: 'VALIDATION_FAILED',
            path: '/',
            severity: 'error',
            message: 'Recoveries must sum to one',
          },
        ],
      },
    };
    const response = await handleEngineeringRequest(
      request(),
      'build-flowsheet',
      vi.fn().mockResolvedValue(Response.json(error, { status: 422 })),
    );
    expect(response.status).toBe(422);
    expect(await response.json()).toEqual(error);
  });
  it('does not allow a remote engine in this milestone', async () => {
    vi.stubEnv('RIOGINEER_ENGINE_URL', 'https://example.com');
    const fetcher = vi.fn();
    expect((await handleEngineeringRequest(request(), 'build-flowsheet', fetcher)).status).toBe(
      503,
    );
    expect(fetcher).not.toHaveBeenCalled();
  });
});
