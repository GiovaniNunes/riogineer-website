import { PageIntro } from '@/components/page-intro';
import { pageMetadata } from '@/lib/metadata';
import reference from '../../../contracts/examples/requirements.json';
import networkReference from '../../../contracts/examples/milestone-4-requirements.json';
import equilibriumReference from '../../../contracts/examples/milestone-9-requirements.json';
import { EngineerWorkspace } from './workspace';
import sequentialReference from '../../../contracts/examples/milestone-5-requirements.json';
import compressionReference from '../../../contracts/examples/milestone-6-requirements.json';
export const metadata = pageMetadata(
  'Digital Engineer',
  'From engineering specifications to reviewed requirements and deterministic simulation.',
  '/digital-engineer',
);
export default function DigitalEngineer() {
  return (
    <>
      <PageIntro
        eyebrow="RIOGINEER DIGITAL ENGINEER"
        title="From Engineering Specifications to Simulation."
        description="Interpret your technical specification, review the evidence and approve requirements before generating a PFD and running the Python engineering calculation."
        crumbs={[{ label: 'Digital Engineer', href: '/digital-engineer' }]}
      />
      <EngineerWorkspace
        equilibriumReferenceText={JSON.stringify(equilibriumReference, null, 2)}
        referenceText={JSON.stringify(reference, null, 2)}
        compressionReferenceText={JSON.stringify(compressionReference, null, 2)}
        sequentialReferenceText={JSON.stringify(sequentialReference, null, 2)}
        networkReferenceText={JSON.stringify(networkReference, null, 2)}
      />
    </>
  );
}
