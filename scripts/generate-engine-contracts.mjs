import { writeFileSync, readFileSync } from 'node:fs';
import { z } from 'zod';
import {
  requirementsSchema,
  flowsheetSchema,
  resultsSchema,
  validationResponseSchema,
  errorSchema,
} from '../src/lib/digital-engineer/contracts.ts';

const check = process.argv.includes('--check');
for (const [name, schema] of Object.entries({
  requirements: requirementsSchema,
  flowsheet: flowsheetSchema,
  results: resultsSchema,
  validation: validationResponseSchema,
  error: errorSchema,
})) {
  const file = new URL(`../contracts/v1/${name}.schema.json`, import.meta.url);
  const text = JSON.stringify(z.toJSONSchema(schema, { target: 'draft-2020-12' }), null, 2) + '\n';
  if (check) {
    if (readFileSync(file, 'utf8') !== text) throw new Error(`Contract drift: ${name}`);
  } else writeFileSync(file, text);
}
