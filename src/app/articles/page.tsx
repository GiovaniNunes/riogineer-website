import { PageIntro } from '@/components/page-intro';
import { ContentCards } from '@/components/content-cards';
import { ContentRequired } from '@/components/content-required';
import { getContent } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
export const metadata = pageMetadata(
  'Technical Articles',
  'Technical articles on Digital Engineers, engineering models and specialized computational workflows.',
  '/articles',
  undefined,
  getContent('articles').length === 0,
);
export default function Articles() {
  const entries = getContent('articles');
  return (
    <>
      <PageIntro
        eyebrow="Knowledge / Technical articles"
        title="Engineering in detail."
        description="A space for technical explanations, model discussions and engineering studies."
        crumbs={[{ label: 'Articles', href: '/articles' }]}
      />
      <section className="section">
        <div className="container">
          {entries.length ? (
            <ContentCards entries={entries} kind="article" />
          ) : (
            <ContentRequired>
              Approved technical articles. No articles have been published yet.
            </ContentRequired>
          )}
        </div>
      </section>
    </>
  );
}
