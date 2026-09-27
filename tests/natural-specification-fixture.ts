import { fixture } from './interpretation-fixture';
import { type Fact } from '../src/lib/digital-engineer/interpretation/contracts';

// User-reported wording; numbers are the unchanged reference engineering basis.
export const componentText = `Methane mass flow: 22000 kg/h
n-Hexane mass flow: 77000 kg/h
Water mass flow: 11000 kg/h

Constant heat capacities:
Methane: 2200 J/(kg K)
n-Hexane: 2200 J/(kg K)
Water: 4180 J/(kg K)

Recoveries:
Methane: gas 1.0, oil 0.0, water 0.0
n-Hexane: gas 0.0, oil 1.0, water 0.0
Water: gas 0.0, oil 0.05, water 0.95`;
export const exclusionText = `Rigorous vapor-oil-water equilibrium is outside the requested calculation scope.
Separator sizing is outside the requested calculation scope.
Geometry-based separation efficiency is outside the requested calculation scope.`;
export const naturalSpecification = `Equipment: three-phase separator.
Topology: one feed, one separator, gas, oil and water outlets.
Components: methane, n_hexane, water.
Requested products: gas, oil and water.
Feed temperature: 313.15 K.
Feed pressure: 2000000 Pa abs.
Separator temperature: 313.15 K.
Separator pressure: 2000000 Pa abs.
Reference temperature: 273.15 K.

${componentText}

${exclusionText}`;

export function naturalFixture() {
  const result = fixture();
  const names: Record<string, string> = {
    methane: 'Methane',
    n_hexane: 'n-Hexane',
    water: 'Water',
  };
  // Deliberately return source names on facts, canonical IDs in the declared basis.
  result.draft.facts = result.draft.facts.filter((f) => f.field !== 'total_flow');
  for (const fact of result.draft.facts) {
    fact.origin = 'specified';
    if (fact.component) {
      fact.component = names[fact.component];
      const prefix =
        fact.field === 'component_flow' ? `${fact.component} mass flow:` : `${fact.component}:`;
      const block =
        fact.field === 'component_flow'
          ? componentText.split('\n\n')[0]
          : fact.field === 'cp'
            ? componentText.split('\n\n')[1]
            : componentText.split('\n\n')[2];
      fact.evidence.excerpt = block.split('\n').find((line) => line.startsWith(prefix))!;
    } else {
      const phrases: Record<string, string> = {
        equipment: 'Equipment:',
        topology: 'Topology:',
        components: 'Components:',
        outputs: 'Requested products:',
        feed_temperature: 'Feed temperature:',
        feed_pressure: 'Feed pressure:',
        separator_temperature: 'Separator temperature:',
        separator_pressure: 'Separator pressure:',
        reference_temperature: 'Reference temperature:',
      };
      fact.evidence.excerpt = naturalSpecification
        .split('\n')
        .find((line) => line.startsWith(phrases[fact.field]))!;
    }
  }
  result.source.pages[0].text = naturalSpecification;
  result.review.assumptions = {};
  result.draft.issues = exclusionText.split('\n').map((excerpt, index) => ({
    id: `exclusion-${index}`,
    kind: 'scope_exclusion',
    field: null,
    component: null,
    message: excerpt,
    evidence: { source_id: result.source.id, source_type: result.source.type, page: null, excerpt },
  }));
  return result;
}

export const componentFieldNames: Fact['field'][] = [
  'component_flow',
  'cp',
  'recovery_gas',
  'recovery_oil',
  'recovery_water',
];
