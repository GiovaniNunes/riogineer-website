import type { MetadataRoute } from 'next';
import { site } from '@/config/site';
import { pages } from '@/config/pages';
import { getContent } from '@/lib/content';
export default function sitemap(): MetadataRoute.Sitemap {
  // Preview sites intentionally expose no indexable URLs; production requires an approved origin.
  if (!site.indexable) return [];
  const articles = getContent('articles').filter((entry) => entry.metadata.status === 'published');
  return [
    ...pages
      .filter((page) => page.path !== '/articles' || articles.length > 0)
      .map((page) => ({ url: `${site.url}${page.path}` })),
    ...getContent('applications').map((entry) => ({ url: `${site.url}${entry.href}` })),
    ...[...getContent('demonstrations'), ...articles]
      .filter((entry) => entry.metadata.status === 'published')
      .map((entry) => ({
        url: `${site.url}${entry.href}`,
        ...(entry.metadata.date ? { lastModified: entry.metadata.date } : {}),
      })),
  ];
}
