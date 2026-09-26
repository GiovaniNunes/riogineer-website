import { PageIntro } from '@/components/page-intro';
import { ContentCards } from '@/components/content-cards';
import { getContent } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
export const metadata = pageMetadata(
  'Demonstrations',
  'Explore the planned Digital Engineer demonstrations: three-phase separation, process recycles, PFD generation and offshore field development.',
  '/demonstrations',
);
export default function Demonstrations() {
  return (
    <>
      <PageIntro
        eyebrow="Demonstrations / Technical library"
        title="See the Digital Engineer at work."
        description="Explore engineering problems, model interactions and technical explanations. Demonstration videos and verified results are currently awaiting content."
        crumbs={[{ label: 'Demonstrations', href: '/demonstrations' }]}
      />
      <section className="section">
        <div className="container">
          <ContentCards entries={getContent('demonstrations')} kind="demonstration" />
        </div>
      </section>
    </>
  );
}
