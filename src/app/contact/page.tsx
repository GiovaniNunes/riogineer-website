import { PageIntro } from '@/components/page-intro';
import { ContactForm } from '@/components/contact-form';
import { ContentRequired } from '@/components/content-required';
import { pageMetadata } from '@/lib/metadata';
export const metadata = pageMetadata(
  'Contact',
  'Explore your engineering application with RIOGINEER. The demonstration request form is available for validation; message delivery is currently disabled.',
  '/contact',
);
export default function Contact() {
  return (
    <>
      <PageIntro
        eyebrow="Contact / Start a conversation"
        title="Talk to our Digital Engineers."
        description="Tell us about your engineering application and area of interest. Message delivery will become available once contact services are configured."
        crumbs={[{ label: 'Contact', href: '/contact' }]}
      />
      <section className="section">
        <div className="container detailGrid">
          <ContactForm />
          <aside className="aside">
            <h2>Engineering conversations</h2>
            <p>
              Process engineering. Offshore field development. Reservoir engineering. AI and
              specialized engineering software.
            </p>
            <p>
              Technology partnership is an inquiry category, not a statement of an existing
              partnership.
            </p>
            <ContentRequired>
              Approved contact details and privacy/data-handling wording before message delivery is
              enabled.
            </ContentRequired>
          </aside>
        </div>
      </section>
    </>
  );
}
