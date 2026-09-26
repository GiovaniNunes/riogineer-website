import type { Metadata } from 'next';
import { site } from '@/config/site';
export function pageMetadata(
  title: string,
  description: string,
  path: string,
  image?: string,
  draft = false,
): Metadata {
  title = path.startsWith('/demonstrations/')
    ? `${title} Demonstration`
    : path.startsWith('/articles/')
      ? `${title} Article`
      : title;
  const url = new URL(path, site.url).toString();
  const card = image || `/og${path === '/' ? '/home' : path}`;
  const images = [{ url: new URL(card, site.url).toString(), alt: `${site.name} — ${title}` }];
  return {
    title,
    description,
    alternates: { canonical: url },
    robots: { index: site.indexable && !draft, follow: true },
    openGraph: {
      title: `${title} | ${site.name}`,
      description,
      url,
      siteName: site.name,
      locale: 'en_US',
      type: 'website',
      images,
    },
    twitter: {
      card: 'summary_large_image',
      title: `${title} | ${site.name}`,
      description,
      images: images.map((item) => item.url),
    },
  };
}
export function jsonLd(data: Record<string, unknown>) {
  return JSON.stringify(data).replace(/</g, '\\u003c');
}
