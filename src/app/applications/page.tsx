import { PageIntro } from '@/components/page-intro';
import { ContentCards } from '@/components/content-cards';
import { getContent } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
export const metadata = pageMetadata(
  'Engineering Applications',
  'Explore RIOGINEER application concepts in process engineering, offshore field development, reservoir engineering and Engineering Knowledge Intelligence.',
  '/applications',
);
export default function Applications() {
  return (
    <>
      <PageIntro
        eyebrow="Applications / Engineering domains"
        title="Engineering knowledge. Applied."
        description="Initial application areas for Digital Engineers, connecting technical requirements with engineering models and specialized computational tools."
        crumbs={[{ label: 'Applications', href: '/applications' }]}
      />
      <section className="section">
        <div className="container">
          <ContentCards entries={getContent('applications')} kind="application" />
        </div>
      </section>
      <section className="section">
        <div className="container prose">
          <h2>Built for future expansion</h2>
          <p>
            The content architecture can accommodate renewable energy, chemical processing, energy
            systems and infrastructure. These are future expansion areas, not claims of current
            deployments.
          </p>
        </div>
      </section>
    </>
  );
}
