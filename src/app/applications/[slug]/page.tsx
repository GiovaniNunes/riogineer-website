import { notFound } from 'next/navigation';
import Link from 'next/link';
import { PageIntro } from '@/components/page-intro';
import { Workflow } from '@/components/workflow';
import { getContent, getContentEntry } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
export const dynamicParams = false;
export function generateStaticParams() {
  return getContent('applications').map(({ slug }) => ({ slug }));
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const entry = getContentEntry('applications', (await params).slug);
  if (!entry) notFound();
  return pageMetadata(
    entry.metadata.title,
    entry.metadata.description,
    entry.href,
    entry.metadata.socialImage,
  );
}
export default async function Application({ params }: { params: Promise<{ slug: string }> }) {
  const entry = getContentEntry('applications', (await params).slug);
  if (!entry) notFound();
  const related = getContent('demonstrations').filter((item) =>
    item.metadata.relatedApplications.includes(entry.slug),
  );
  return (
    <>
      <PageIntro
        eyebrow="Application / Conceptual workflow"
        title={entry.metadata.subtitle}
        description={entry.metadata.summary}
        crumbs={[
          { label: 'Applications', href: '/applications' },
          { label: entry.metadata.title, href: entry.href },
        ]}
      />
      <section className="section">
        <div className="container">
          <Workflow steps={entry.metadata.workflow} title={entry.metadata.title} />
        </div>
      </section>
      <section className="section">
        <div className="container detailGrid">
          <article className="prose">
            <entry.Content />
          </article>
          <aside className="aside">
            <h2>Explore further</h2>
            <ul>
              {related.map((item) => (
                <li key={item.slug}>
                  <Link href={item.href}>{item.metadata.title}</Link>
                </li>
              ))}
              <li>
                <Link href="/technology">The technology behind the Digital Engineer</Link>
              </li>
            </ul>
            <Link className="textLink" href="/contact">
              Request a demonstration <span aria-hidden="true">↗</span>
            </Link>
          </aside>
        </div>
      </section>
    </>
  );
}
