import { notFound } from 'next/navigation';
import { ContentDetail } from '@/components/content-detail';
import { getContent, getContentEntry } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
export const dynamicParams = false;
export function generateStaticParams() {
  return getContent('articles').map(({ slug }) => ({ slug }));
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const entry = getContentEntry('articles', (await params).slug);
  if (!entry) notFound();
  return pageMetadata(
    entry.metadata.title,
    entry.metadata.description,
    entry.href,
    entry.metadata.socialImage,
    entry.metadata.status !== 'published',
  );
}
export default async function Article({ params }: { params: Promise<{ slug: string }> }) {
  const entry = getContentEntry('articles', (await params).slug);
  if (!entry) notFound();
  return <ContentDetail entry={entry} />;
}
