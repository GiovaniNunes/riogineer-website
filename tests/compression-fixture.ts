import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import {
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
const data = JSON.parse(
  execFileSync(
    process.env.ENGINE_PYTHON || resolve('engine/.venv/bin/python'),
    [
      '-B',
      '-c',
      "import json; from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate; r=loads((ROOT/'contracts/examples/milestone-6-requirements.json').read_text()); f=build_flowsheet(r); print(json.dumps(dict(requirements=r,flowsheet=f,results=calculate(f))))",
    ],
    { cwd: resolve('engine'), encoding: 'utf8' },
  ),
);
export const requirements = engineeringRequirementsSchema.parse(data.requirements);
export const flowsheet = flowsheetSchema.parse(data.flowsheet);
const historicalResults = resultsSchema.parse(data.results);
if (
  historicalResults.schema_version !== '1.5' ||
  historicalResults.process_result_version !== '1.4'
)
  throw new Error('Compression fixture requires the historical molecular compression result.');
export const results = historicalResults;
