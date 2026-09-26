import type { MetadataRoute } from 'next';
import { site } from '@/config/site';
export default function robots(): MetadataRoute.Robots {
  return site.indexable
    ? {
        rules: { userAgent: '*', allow: '/', disallow: ['/api/'] },
        sitemap: `${site.url}/sitemap.xml`,
      }
    : { rules: { userAgent: '*', disallow: '/' } };
}
