import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  requirementsSchema,
  flowsheetSchema,
  resultsSchema,
} from '../src/lib/digital-engineer/contracts';
const python =
  process.env.ENGINE_PYTHON ||
  (existsSync('engine/.venv/bin/python') ? resolve('engine/.venv/bin/python') : 'python3');
const data = JSON.parse(
  execFileSync(
    python,
    [
      '-B',
      '-c',
      "import json; from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate; r=loads((ROOT/'contracts/examples/requirements.json').read_text()); f=build_flowsheet(r); print(json.dumps(dict(requirements=r,flowsheet=f,results=calculate(f))))",
    ],
    { cwd: resolve('engine'), encoding: 'utf8' },
  ),
);
export const referenceRequirements = requirementsSchema.parse(data.requirements);
export const referenceFlowsheet = flowsheetSchema.parse(data.flowsheet);
const parsedResults = resultsSchema.parse(data.results);
if (parsedResults.schema_version === '1.2' || parsedResults.schema_version === '1.3')
  throw new Error('Single-separator fixture changed version');
export const referenceResults = parsedResults;
