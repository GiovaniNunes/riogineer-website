import { brand } from './brand';

export function resolveSiteConfig(env: Record<string, string | undefined>) {
  const url = new URL(env.SITE_URL || 'http://localhost:3000');
  if (
    !['http:', 'https:'].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.pathname !== '/' ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      'SITE_URL must be a plain HTTP(S) origin without credentials, a path, query, or fragment.',
    );
  }
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  const indexable = env.SITE_INDEXABLE === 'true';
  if (indexable && (local || url.protocol !== 'https:')) {
    throw new Error('Indexing requires an approved public HTTPS SITE_URL.');
  }
  return { url: url.origin, indexable };
}

export const site = {
  ...resolveSiteConfig(process.env),
  ...brand,
  description:
    'AI-powered Digital Engineers combining engineering knowledge, physical models, simulation and artificial intelligence.',
};
