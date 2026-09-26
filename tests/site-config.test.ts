import { describe, expect, it } from 'vitest';
import { resolveSiteConfig } from '@/config/site';
import { jsonLd, pageMetadata } from '@/lib/metadata';
describe('site origin and metadata', () => {
  it('defaults to a non-indexable development origin', () => {
    expect(resolveSiteConfig({})).toEqual({ url: 'http://localhost:3000', indexable: false });
  });
  it('does not allow accidental indexing of a local or insecure origin', () => {
    expect(() => resolveSiteConfig({ SITE_INDEXABLE: 'true' })).toThrow();
    expect(() =>
      resolveSiteConfig({ SITE_URL: 'http://example.com', SITE_INDEXABLE: 'true' }),
    ).toThrow();
  });
  it('rejects origins containing credentials, paths or unsupported schemes', () => {
    for (const SITE_URL of [
      'https://user:password@example.com',
      'https://example.com/path',
      'javascript:alert(1)',
      'https://example.com?x=1',
    ])
      expect(() => resolveSiteConfig({ SITE_URL })).toThrow();
  });
  it('supports explicitly configured public HTTPS origins', () => {
    expect(resolveSiteConfig({ SITE_URL: 'https://example.com', SITE_INDEXABLE: 'true' })).toEqual({
      url: 'https://example.com',
      indexable: true,
    });
  });
  it('creates distinct canonical and share URLs for content pages', () => {
    const first = pageMetadata('First study', 'First description', '/demonstrations/first');
    const second = pageMetadata('Second study', 'Second description', '/demonstrations/second');
    expect(first.alternates?.canonical).not.toEqual(second.alternates?.canonical);
    expect(first.openGraph?.images).not.toEqual(second.openGraph?.images);
    expect(first.twitter?.description).toBe('First description');
  });
  it('escapes script-closing content in JSON-LD', () => {
    expect(jsonLd({ name: '</script><script>' })).not.toContain('<');
  });
});
