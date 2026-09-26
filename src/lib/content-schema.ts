import { z } from 'zod';
const localAsset = z
  .string()
  .regex(/^\/(?!\/)[a-zA-Z0-9/_ .-]+$/, 'Use a local public asset path.');
export const contentSchema = z
  .object({
    title: z.string().min(1).max(120),
    subtitle: z.string().min(1).max(180),
    summary: z.string().min(1).max(400),
    description: z.string().min(1).max(300),
    order: z.number().int().nonnegative().default(100),
    status: z.enum(['conceptual', 'awaiting-content', 'published']),
    workflow: z.array(z.string().min(1)).default([]),
    relatedApplications: z.array(z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/)).default([]),
    date: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/)
      .refine(
        (value) =>
          !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value,
        'Use a valid date.',
      )
      .optional(),
    images: z
      .array(z.object({ src: localAsset, alt: z.string().min(1), caption: z.string().min(1) }))
      .default([]),
    diagrams: z
      .array(z.object({ src: localAsset, alt: z.string().min(1), caption: z.string().min(1) }))
      .default([]),
    cardIllustration: z
      .object({
        src: localAsset,
        alt: z.string().trim().min(1),
        caption: z.string().trim().min(1).optional(),
      })
      .optional(),
    socialImage: localAsset.optional(),
    youtubeId: z
      .string()
      .regex(/^[a-zA-Z0-9_-]{11}$/)
      .optional(),
    videoTitle: z.string().min(1).optional(),
    videoDescription: z.string().min(1).optional(),
    videoUploadDate: z.string().datetime({ offset: true }).optional(),
    videoThumbnail: localAsset.optional(),
  })
  .superRefine((data, ctx) => {
    if (data.status === 'published' && !data.date)
      ctx.addIssue({
        code: 'custom',
        path: ['date'],
        message: 'Published content requires a real publication date.',
      });
    if (data.youtubeId && (!data.videoTitle || !data.videoDescription))
      ctx.addIssue({
        code: 'custom',
        path: ['youtubeId'],
        message: 'Videos require a title and technical description.',
      });
  });
export type ContentMetadata = z.infer<typeof contentSchema>;
