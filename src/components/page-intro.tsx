import Link from 'next/link';
import { site } from '@/config/site';
import { jsonLd } from '@/lib/metadata';
export function PageIntro({
  eyebrow,
  title,
  description,
  crumbs = [],
}: {
  eyebrow: string;
  title: string;
  description: string;
  crumbs?: { label: string; href: string }[];
}) {
  const items = [{ label: 'Home', href: '/' }, ...crumbs];
  return (
    <section className="pageIntro">
      <div className="container">
        <nav aria-label="Breadcrumb">
          <ol className="breadcrumbs">
            {items.map((item, index) => (
              <li key={item.href}>
                {index === items.length - 1 ? (
                  <span aria-current="page">{item.label}</span>
                ) : (
                  <Link href={item.href}>{item.label}</Link>
                )}
              </li>
            ))}
          </ol>
        </nav>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: jsonLd({
              '@context': 'https://schema.org',
              '@type': 'BreadcrumbList',
              itemListElement: items.map((item, index) => ({
                '@type': 'ListItem',
                position: index + 1,
                name: item.label,
                item: new URL(item.href, site.url).toString(),
              })),
            }),
          }}
        />
      </div>
    </section>
  );
}
