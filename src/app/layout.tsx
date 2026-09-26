import type { Metadata } from 'next';
import { Header } from '@/components/header';
import { Footer } from '@/components/footer';
import { site } from '@/config/site';
import { jsonLd } from '@/lib/metadata';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: { default: `${site.name} | ${site.descriptor}`, template: `%s | ${site.name}` },
  description: site.description,
  robots: { index: site.indexable, follow: true },
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>
        <Footer />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: jsonLd({
              '@context': 'https://schema.org',
              '@type': 'Organization',
              name: site.name,
              legalName: site.legalName,
              description: site.description,
              ...(site.indexable ? { url: site.url } : {}),
            }),
          }}
        />
      </body>
    </html>
  );
}
