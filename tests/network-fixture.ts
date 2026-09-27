import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  engineeringRequirementsSchema,
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
      "import json; from riogineer_engine.core import ROOT, loads, build_flowsheet, calculate; r=loads((ROOT/'contracts/examples/milestone-4-requirements.json').read_text()); f=build_flowsheet(r); print(json.dumps(dict(requirements=r,flowsheet=f,results=calculate(f))))",
    ],
    { cwd: resolve('engine'), encoding: 'utf8' },
  ),
);
export const networkRequirements = engineeringRequirementsSchema.parse(data.requirements);
export const networkFlowsheet = flowsheetSchema.parse(data.flowsheet);
export const networkResults = resultsSchema.parse(data.results);
