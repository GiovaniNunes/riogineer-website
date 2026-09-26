import { digitalEngineerWorkflow } from '@/config/workflow';
import styles from './workflow.module.css';
export function Workflow({
  steps,
  title = 'Engineering workflow',
}: {
  steps: readonly string[];
  title?: string;
}) {
  return (
    <figure className={styles.figure}>
      <figcaption className={styles.caption}>
        <span>{title}</span>
        <span>CONCEPTUAL WORKFLOW</span>
      </figcaption>
      <ol className={styles.flow}>
        {steps.map((step, index) => (
          <li key={step}>
            <span className={styles.index}>{String(index + 1).padStart(2, '0')}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
    </figure>
  );
}
/** Use this component wherever the general Digital Engineer workflow is shown. */
export function DigitalEngineerWorkflow() {
  return (
    <Workflow title="From information to engineering decisions" steps={digitalEngineerWorkflow} />
  );
}

export function HeroWorkflow() {
  return (
    <figure className={styles.panel} aria-label="Conceptual Digital Engineer workflow">
      <figcaption className={styles.panelTop}>
        <span>DE / WORKFLOW ARCHITECTURE</span>
        <span>01 — 07</span>
      </figcaption>
      <ol className={styles.heroFlow}>
        {digitalEngineerWorkflow.map((step, index) => (
          <li key={step}>
            <div className={styles.node}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              {step}
            </div>
          </li>
        ))}
      </ol>
      <div className={styles.panelBottom}>
        <span>PHYSICS + ENGINEERING + AI</span>
        <span>Conceptual sequence</span>
      </div>
    </figure>
  );
}
