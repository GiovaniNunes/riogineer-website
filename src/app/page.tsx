import { HeroVideo } from '@/components/hero-video';
import Link from 'next/link';
import { DigitalEngineerWorkflow } from '@/components/workflow';
import { ContentRequired } from '@/components/content-required';
import { ContentCards } from '@/components/content-cards';
import { getContent } from '@/lib/content';
import { pageMetadata } from '@/lib/metadata';
import styles from './home.module.css';
export const metadata = pageMetadata(
  'AI-Powered Digital Engineering',
  'RIOGINEER develops AI-powered Digital Engineers combining engineering knowledge, physical models, simulation and artificial intelligence.',
  '/',
);
export default function Home() {
  return (
    <>
      <section className={styles.hero}>
        <div className="container">
          <div className={styles.heroGrid}>
            <div>
              <span className="eyebrow">RIOGINEER / AI-Powered Digital Engineering</span>
              <h1>
                <span>Engineering Intelligence.</span>
                <span>Built on Physics.</span>
                <span>Powered by AI.</span>
              </h1>
              <p className={styles.heroText}>
                AI-powered Digital Engineers combining engineering knowledge, physical models and
                artificial intelligence to design, simulate and optimize complex engineering
                systems.
              </p>
              <div className="buttonGroup">
                <Link className="button primary" href="/demonstrations">
                  Watch RIOGINEER at work <span aria-hidden="true">↗</span>
                </Link>
                <Link className="button secondary" href="/contact">
                  Request a demo <span aria-hidden="true">→</span>
                </Link>
              </div>
              <p className={styles.heroFootnote}>
                ENGINEERING KNOWLEDGE → COMPUTATIONAL TOOLS → TECHNICAL DECISIONS
              </p>
            </div>
            <HeroVideo />
          </div>
          <div className={styles.disciplines}>
            <span>Initial application areas</span>
            <span>Process engineering</span>
            <span>Offshore systems</span>
            <span>Reservoir engineering</span>
          </div>
        </div>
      </section>
      <section className={`section ${styles.internalSection} ${styles.meet}`}>
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">01 / The Digital Engineer</span>
              <h2>
                Meet the
                <br />
                Digital Engineer.
              </h2>
            </div>
            <p>From technical requirements to structured engineering workflows.</p>
          </div>
          <div className={styles.meetIntro}>
            <p>
              Traditional engineering workflows require engineers to translate technical
              requirements into models, simulations and design decisions.
            </p>
            <div>
              <p>
                RIOGINEER introduces a new approach. The Digital Engineer interprets engineering
                information, interacts with specialized engineering models and simulation tools, and
                assists engineers through complex engineering workflows.
              </p>
              <Link className="textLink" href="/technology">
                Explore the technology <span aria-hidden="true">↗</span>
              </Link>
            </div>
          </div>
          <DigitalEngineerWorkflow />
        </div>
      </section>
      <section className={`section ${styles.internalSection}`}>
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">02 / Connected disciplines</span>
              <h2>
                Engineering.
                <br />
                Physics. AI.
              </h2>
            </div>
            <p>
              Artificial Intelligence becomes significantly more valuable for engineering when
              combined with physical models and specialized engineering knowledge.
            </p>
          </div>
          <div className={styles.principles}>
            {[
              [
                '01 / DOMAIN',
                'Engineering knowledge',
                'Technical specifications, design practices and engineering procedures provide the context.',
              ],
              [
                '02 / MODELS',
                'Physical models',
                'Physical and mathematical models provide the basis for engineering calculations and simulations.',
              ],
              [
                '03 / ORCHESTRATION',
                'Artificial intelligence',
                'AI interprets information and organizes interactions with specialized computational tools.',
              ],
            ].map(([number, title, text]) => (
              <div className={styles.principle} key={title}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
          <div className={styles.convergence}>
            <span>RIOGINEER DIGITAL ENGINEER</span>
          </div>
        </div>
      </section>
      <section className={`section ${styles.internalSection}`}>
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">03 / Applications</span>
              <h2>
                Engineering challenges.
                <br />
                Connected workflows.
              </h2>
            </div>
            <p>Explore the initial application areas for AI-assisted engineering.</p>
          </div>
          <ContentCards entries={getContent('applications')} kind="application" />
        </div>
      </section>
      <section className={`section ${styles.demo}`}>
        <div className={`container ${styles.demoGrid}`}>
          <div>
            <span className={`eyebrow ${styles.demoEyebrow}`}>04 / Demonstrations</span>
            <h2>
              See the Digital
              <br />
              Engineer at work.
            </h2>
            <h3>
              From Engineering Specification
              <br />
              to Process Simulation
            </h3>
            <p>
              See how a Digital Engineer can interpret technical requirements, construct an
              engineering workflow and interact with process simulation models.
            </p>
            <div className="buttonGroup">
              <Link className="button secondary" href="/demonstrations/three-phase-separator">
                Watch demonstration <span aria-hidden="true">↗</span>
              </Link>
            </div>
          </div>
          <ContentRequired media>
            Three-phase separator demonstration. Verified video, screenshots and engineering results
            have not yet been supplied.
          </ContentRequired>
        </div>
      </section>
      <section className={`section ${styles.ctaSection}`}>
        <div className={`container ${styles.cta}`}>
          <div>
            <h2>
              Talk to our
              <br />
              Digital Engineers.
            </h2>
            <p>Explore your engineering application with RIOGINEER.</p>
          </div>
          <Link className="button primary" href="/contact">
            Request a demonstration <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </section>
    </>
  );
}
