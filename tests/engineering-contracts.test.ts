import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { z } from 'zod';
import {
  requirementsSchema,
  engineeringRequirementsSchema,
  flowsheetSchema,
  resultsSchema,
  engineeringValidationResponseSchema as validationResponseSchema,
  errorSchema,
} from '../src/lib/digital-engineer/contracts';
import {
  referenceRequirements as requirements,
  referenceFlowsheet as flowsheet,
  referenceResults as results,
} from './engine-fixture';
describe('shared engineering contracts', () => {
  it('matches all committed Python JSON schemas', () => {
    for (const [name, schema] of Object.entries({
      requirements: engineeringRequirementsSchema,
      flowsheet: flowsheetSchema,
      results: resultsSchema,
      validation: validationResponseSchema,
      error: errorSchema,
    })) {
      expect(JSON.parse(readFileSync(`contracts/v1/${name}.schema.json`, 'utf8'))).toEqual(
        z.toJSONSchema(schema, { target: 'draft-2020-12' }),
      );
    }
  });
  it('accepts real Python outputs and reproduces the current mass flows', () => {
    expect(flowsheet.boundaries).toHaveLength(4);
    expect(Object.values(results.streams).map((s) => s.mass_flow_kg_h)).toEqual([
      110000, 22000, 77550, 10450,
    ]);
    expect(results.balances.energy.duty_W).toBe(0);
  });
  it.each([
    { ...requirements, schema_version: '2.0' },
    { ...requirements, unknown: true },
    { ...requirements, units: { ...requirements.units, pressure: 'bar' } },
    { ...requirements, equipment: [...requirements.equipment, ...requirements.equipment] },
    {
      ...requirements,
      feeds: [
        {
          ...requirements.feeds[0],
          state: { ...requirements.feeds[0].state, temperature_K: Infinity },
        },
      ],
    },
  ])('rejects unsupported or unsafe requirements', (value) =>
    expect(requirementsSchema.safeParse(value).success).toBe(false),
  );
  it('rejects fabricated unavailable values', () => {
    expect(
      resultsSchema.safeParse({
        ...results,
        unavailable: [{ ...results.unavailable[0], value: 0 }],
      }).success,
    ).toBe(false);
  });
});
