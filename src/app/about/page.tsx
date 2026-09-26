import { PageIntro } from '@/components/page-intro';
import { pageMetadata, jsonLd } from '@/lib/metadata';
import styles from './about.module.css';
export const metadata = pageMetadata(
  'About RIOGINEER',
  'Meet RIOGINEER, an engineering technology company developing AI-powered Digital Engineers, and its founders.',
  '/about',
);
const people = [
  {
    name: 'Giovani Cavalcanti Nunes',
    role: 'Founder',
    paragraphs: [
      'Professor and engineer with extensive experience in petroleum engineering, process engineering, research, technology development and innovation.',
      'He worked for approximately 30 years at Petrobras, including research and development activities at CENPES and corporate technology management.',
      'His activities include engineering education, applied research, process engineering, petroleum production systems, simulation, optimization and development of engineering technologies.',
    ],
  },
  {
    name: 'Gustavo Alves de Carvalho',
    role: 'Co-Founder',
    paragraphs: [
      'Engineer with experience in machine learning, reservoir modeling, numerical simulation and software development.',
      'His technical work includes neural networks, reduced-order reservoir representations, dynamic simulation, optimization and engineering software development using Python and C++.',
    ],
  },
];
export default function About() {
  return (
    <>
      <PageIntro
        eyebrow="About RIOGINEER"
        title="Engineering knowledge. A new digital expression."
        description="RIOGINEER was created to transform advanced engineering knowledge into Digital Engineers."
        crumbs={[{ label: 'About', href: '/about' }]}
      />
      <section className="section">
        <div className="container detailGrid">
          <div className="prose">
            <h2>An engineering technology company</h2>
            <p>
              The company combines extensive industrial engineering experience with research and
              development in artificial intelligence, numerical simulation, machine learning and
              engineering software.
            </p>
            <p>
              RIOGINEER develops AI-powered Digital Engineers that combine engineering knowledge,
              physical models, simulation and artificial intelligence to design, analyze and
              optimize complex engineering systems.
            </p>
          </div>
          <aside className="aside">
            <h2>A distinct company</h2>
            <p>
              RIOGINEER LTDA is a new technology company, separate from Rio Petróleo. The founders’
              experience does not establish RIOGINEER customer contracts, partnerships or project
              history.
            </p>
          </aside>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <div className="sectionHeading">
            <div>
              <span className="eyebrow">People / Founders</span>
              <h2>
                Engineering experience.
                <br />
                Technical curiosity.
              </h2>
            </div>
          </div>
          <div className={styles.people}>
            {people.map((person) => (
              <article className={styles.person} key={person.name}>
                <span className="eyebrow">{person.role}</span>
                <h3>{person.name}</h3>
                {person.paragraphs.map((text) => (
                  <p key={text}>{text}</p>
                ))}
                <script
                  type="application/ld+json"
                  dangerouslySetInnerHTML={{
                    __html: jsonLd({
                      '@context': 'https://schema.org',
                      '@type': 'Person',
                      name: person.name,
                      jobTitle: person.role,
                      description: person.paragraphs.join(' '),
                    }),
                  }}
                />
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
