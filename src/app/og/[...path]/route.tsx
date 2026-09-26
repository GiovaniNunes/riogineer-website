import { ImageResponse } from 'next/og';
import { pages } from '@/config/pages';
import { brand } from '@/config/brand';
import { getContent } from '@/lib/content';
import { designTokens as tokens } from '@/generated/design-tokens';
export const runtime = 'nodejs';
export const dynamic = 'force-static';
export const dynamicParams = false;
function cards() {
  return [
    ...pages.map((page) => ({
      path: page.path === '/' ? '/home' : page.path,
      title: page.title,
      subtitle: page.subtitle,
      pending: false,
    })),
    ...(['applications', 'demonstrations', 'articles'] as const).flatMap((collection) =>
      getContent(collection).map((entry) => ({
        path: entry.href,
        title: entry.metadata.title,
        subtitle: entry.metadata.subtitle,
        pending: entry.metadata.status === 'awaiting-content',
      })),
    ),
  ];
}
export function generateStaticParams() {
  return cards().map((card) => ({ path: card.path.slice(1).split('/') }));
}
export async function GET(_request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const path = `/${(await params).path.join('/')}`;
  const card = cards().find((item) => item.path === path);
  if (!card) return new Response('Not found', { status: 404 });
  return new ImageResponse(
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
        padding: Number(tokens['--share-padding']),
        background: tokens['--color-paper'],
        color: tokens['--color-ink'],
        fontFamily: tokens['--share-font'],
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: `1px solid ${tokens['--color-line']}`,
          paddingBottom: Number(tokens['--share-gap']),
        }}
      >
        <span style={{ fontSize: Number(tokens['--share-brand-size']), fontWeight: 700 }}>
          {brand.name}
        </span>
        <span
          style={{
            fontSize: Number(tokens['--share-label-size']),
            color: tokens['--color-accent'],
          }}
        >
          {brand.descriptor}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: Number(tokens['--share-gap']) }}>
        <div
          style={{
            fontSize: Number(tokens['--share-title-size']),
            lineHeight: Number(tokens['--line-heading']),
            letterSpacing: tokens['--tracking-heading'],
          }}
        >
          {card.title}
        </div>
        <div
          style={{
            fontSize: Number(tokens['--share-subtitle-size']),
            color: tokens['--color-muted'],
          }}
        >
          {card.subtitle}
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          color: tokens['--color-accent'],
          fontSize: Number(tokens['--share-label-size']),
        }}
      >
        <span>ENGINEERING / PHYSICS / AI</span>
        <span>{card.pending ? '[CONTENT REQUIRED]' : 'RIOGINEER'}</span>
      </div>
    </div>,
    { width: Number(tokens['--share-width']), height: Number(tokens['--share-height']) },
  );
}
