import type { ComponentType } from 'react';
import { contentRegistry } from '@/generated/content-registry';
import { contentSchema, type ContentMetadata } from './content-schema';
export type Collection = 'applications' | 'demonstrations' | 'articles';
export type ContentEntry = {
  collection: Collection;
  slug: string;
  href: string;
  metadata: ContentMetadata;
  Content: ComponentType;
};
const entries: ContentEntry[] = contentRegistry.map((entry) => ({
  ...entry,
  href: `/${entry.collection}/${entry.slug}`,
  metadata: contentSchema.parse(entry.metadata),
}));
for (const entry of entries) {
  for (const slug of entry.metadata.relatedApplications) {
    if (!entries.some((item) => item.collection === 'applications' && item.slug === slug))
      throw new Error(`Unknown application ${slug} referenced by ${entry.slug}`);
  }
}
export function getContent(collection: Collection) {
  return entries
    .filter((entry) => entry.collection === collection)
    .sort((a, b) => a.metadata.order - b.metadata.order || a.slug.localeCompare(b.slug));
}
export function getContentEntry(collection: Collection, slug: string) {
  return getContent(collection).find((entry) => entry.slug === slug);
}
