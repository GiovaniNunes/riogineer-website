import Link from 'next/link';
import { PageIntro } from '@/components/page-intro';
import { Workflow } from '@/components/workflow';
import { ContentRequired } from '@/components/content-required';
import { pageMetadata } from '@/lib/metadata';
export const metadata = pageMetadata(
  'Field Design',
  'Field Design is an engineering platform for conceptual evaluation and optimization of offshore petroleum production systems, distinct from RIOGINEER.',
  '/field-design',
);
export default function FieldDesign() {
  return (
    <>
      <PageIntro
        eyebrow="Specialized engineering software"
        title="Field Design"
        description="Integrated Offshore Production System Design and Optimization"
        crumbs={[{ label: 'Field Design', href: '/field-design' }]}
      />
      <section className="section">
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">From reservoir to economics</span>
              <h2>
                An integrated
                <br />
                engineering perspective.
              </h2>
            </div>
            <p>
              Field Design is an engineering platform for conceptual evaluation and optimization of
              offshore petroleum production systems.
            </p>
          </div>
          <Workflow
            title="Field Design / System concept"
            steps={[
              'Reservoir',
              'Wells',
              'Subsea',
              'Flow assurance',
              'FPSO',
              'Processing',
              'Economics',
              'Optimization',
            ]}
          />
        </div>
      </section>
      <section className="section">
        <div className="container detailGrid">
          <div className="prose">
            <h2>Engineering scope</h2>
            <p>
              Potential components include reservoir production representation, production
              forecasting, wells, subsea systems, multiphase flow, production facilities, processing
              capacity, CAPEX, OPEX, economic evaluation and optimization.
            </p>
            <h2>Connected to a Digital Engineer</h2>
            <p>
              RIOGINEER Digital Engineers can interact with specialized engineering platforms such
              as Field Design. The concepts have distinct roles:
            </p>
            <ul>
              <li>
                <strong>Field Design:</strong> engineering calculation, conceptual design and
                optimization platform.
              </li>
              <li>
                <strong>RIOGINEER:</strong> AI-powered Digital Engineer that interacts with
                engineering knowledge, physical models, simulators and specialized software.
              </li>
            </ul>
            <h2>Technical documentation</h2>
            <ContentRequired>
              Approved Field Design screenshots, supported components, integration details, model
              assumptions, validation evidence and documented limitations.
            </ContentRequired>
          </div>
          <aside className="aside">
            <h2>Corporate distinction</h2>
            <p>
              RIOGINEER LTDA and Rio Petróleo are separate companies. RIOGINEER and Field Design are
              not the same product.
            </p>
            <p>
              This description makes no statement about ownership, licensing, intellectual property
              transfer or commercial agreements.
            </p>
            <Link className="textLink" href="/applications/offshore-field-development">
              Explore offshore applications ↗
            </Link>
          </aside>
        </div>
      </section>
    </>
  );
}
