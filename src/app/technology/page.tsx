import { PageIntro } from '@/components/page-intro';
import { ContentRequired } from '@/components/content-required';
import { pageMetadata } from '@/lib/metadata';
import styles from './technology.module.css';
export const metadata = pageMetadata(
  'Technology',
  'The conceptual architecture behind the Digital Engineer: AI orchestration connected to engineering knowledge, physical models and specialized software.',
  '/technology',
);
export default function Technology() {
  return (
    <>
      <PageIntro
        eyebrow="Technology / System architecture"
        title="The technology behind the Digital Engineer."
        description="Engineering knowledge, physical and mathematical models, simulation and specialized software—connected through an intelligent engineering layer."
        crumbs={[{ label: 'Technology', href: '/technology' }]}
      />
      <section className="section">
        <div className={`container ${styles.architecture}`}>
          <div className="prose">
            <span className="eyebrow">A layered approach</span>
            <h2>AI reasoning and orchestration</h2>
            <p>
              AI interprets engineering information, organizes workflows and interacts with
              computational tools. The concept includes specialized artificial intelligence, Small
              Language Models where appropriate, machine learning and neural networks.
            </p>
            <h2>Deterministic engineering calculations</h2>
            <p>
              Engineering calculations remain associated with appropriate physical models,
              mathematical models, simulators and specialized engineering software. A language model
              is not presented as independently performing these calculations.
            </p>
            <h2>Engineering results and decisions</h2>
            <p>
              The Digital Engineer assists engineers through the workflow, connecting technical
              information to engineering models and results that support technical decisions.
            </p>
          </div>
          <figure>
            <div className={styles.layers}>
              {[
                ['Engineering information', 'Documents · Specifications · Procedures · Data'],
                ['AI engineering layer', 'Interpretation · Reasoning · Workflow orchestration'],
                ['Engineering knowledge', 'Technical context · Engineering practices'],
                [
                  'Computational tools',
                  'Physical models · Mathematical models · Simulators · Specialized software',
                ],
                ['Engineering results', 'Outputs from the associated engineering models'],
                ['Engineering decisions', 'Technical decision support'],
              ].map(([title, text], index, layers) => (
                <div key={title}>
                  <div className={styles.layer} data-highlight={index === 1}>
                    <h3>{title}</h3>
                    <p>{text}</p>
                  </div>
                  {index < layers.length - 1 && (
                    <div className={styles.connector} aria-hidden="true">
                      ↓
                    </div>
                  )}
                </div>
              ))}
            </div>
            <figcaption className={styles.legend}>
              CONCEPTUAL ARCHITECTURE / Not a representation of a verified deployment.
            </figcaption>
          </figure>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">Technical building blocks</span>
              <h2>
                Specialized intelligence.
                <br />
                Engineering foundations.
              </h2>
            </div>
            <p>
              The concept brings together complementary disciplines. The particular combination
              depends on the engineering application.
            </p>
          </div>
          <ul className={styles.capabilities}>
            {[
              'Specialized Artificial Intelligence',
              'Small Language Models',
              'Machine Learning',
              'Neural Networks',
              'Engineering Knowledge',
              'Physical Models',
              'Mathematical Models',
              'Engineering Simulators',
              'Specialized Software',
              'Automated Engineering Workflows',
            ].map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <ContentRequired>
            Implementation-specific model details, supported software interfaces, validation
            evidence, operating boundaries and technical limitations.
          </ContentRequired>
        </div>
      </section>
    </>
  );
}
