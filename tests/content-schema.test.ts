import { describe, expect, it } from 'vitest';
import { contentSchema } from '@/lib/content-schema';
const outline = {
  title: 'Study outline',
  subtitle: 'Engineering workflow',
  summary: 'A conceptual study.',
  description: 'A study awaiting verified content.',
  status: 'awaiting-content',
};
describe('content metadata', () => {
  it('allows an honest outline without fabricated dates or media', () => {
    const data = contentSchema.parse(outline);
    expect(data.date).toBeUndefined();
    expect(data.youtubeId).toBeUndefined();
    expect(data.images).toEqual([]);
  });
  it('requires a real date before publication', () => {
    expect(contentSchema.safeParse({ ...outline, status: 'published' }).success).toBe(false);
    expect(
      contentSchema.safeParse({ ...outline, status: 'published', date: '2026-02-30' }).success,
    ).toBe(false);
    expect(
      contentSchema.safeParse({ ...outline, status: 'published', date: '2026-09-26' }).success,
    ).toBe(true);
  });
  it('rejects invalid video IDs and undescribed videos', () => {
    expect(contentSchema.safeParse({ ...outline, youtubeId: 'https://example.com' }).success).toBe(
      false,
    );
    expect(contentSchema.safeParse({ ...outline, youtubeId: 'abcdefghijk' }).success).toBe(false);
    expect(
      contentSchema.safeParse({
        ...outline,
        youtubeId: 'abcdefghijk',
        videoTitle: 'Study',
        videoDescription: 'Technical explanation.',
      }).success,
    ).toBe(true);
  });
  it('rejects remote asset URLs and missing accessibility descriptions', () => {
    expect(
      contentSchema.safeParse({
        ...outline,
        images: [{ src: 'https://example.com/image.png', alt: 'Image', caption: 'Caption' }],
      }).success,
    ).toBe(false);
    expect(
      contentSchema.safeParse({
        ...outline,
        images: [{ src: '/images/study.png', alt: '', caption: 'Caption' }],
      }).success,
    ).toBe(false);
  });
  it('keeps card illustrations optional and accepts approved local media metadata', () => {
    expect(contentSchema.parse(outline).cardIllustration).toBeUndefined();
    const illustration = {
      src: '/diagrams/approved-study.png',
      alt: 'Process equipment and stream connections',
      caption: 'Approved conceptual diagram.',
    };
    expect(
      contentSchema.parse({ ...outline, cardIllustration: illustration }).cardIllustration,
    ).toEqual(illustration);
  });
  it('rejects a card illustration without meaningful alt text or a local asset', () => {
    for (const illustration of [
      { src: '/diagrams/approved-study.png', alt: ' ' },
      { src: 'https://example.com/diagram.png', alt: 'Diagram' },
    ])
      expect(contentSchema.safeParse({ ...outline, cardIllustration: illustration }).success).toBe(
        false,
      );
  });
});
