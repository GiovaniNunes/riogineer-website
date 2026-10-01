import { describe, expect, it } from 'vitest';
import pt from '../contracts/examples/milestone-17-pt-requirements.json';
import ph from '../contracts/examples/milestone-17-ph-requirements.json';
import historical from '../contracts/examples/milestone-9-requirements.json';
import {
  engineeringRequirementsSchema,
  separatorEnergyDetailsSchema,
} from '../src/lib/digital-engineer/contracts';
const copy = (x: unknown) => JSON.parse(JSON.stringify(x));
describe('M17 additive contracts', () => {
  it('accepts both explicit modes and historical M9 unchanged', () => {
    for (const r of [pt, ph, historical]) expect(engineeringRequirementsSchema.parse(r)).toEqual(r);
  });
  it.each([pt, ph])('rejects contradictory, missing and unsupported specifications', (r) => {
    for (const [key, value] of [
      ['duty_W', 0],
      ['mode', 'unknown'],
      ['separator_pressure_Pa_abs', 0],
      ['separator_pressure_Pa_abs', Infinity],
      ['water', 0],
    ]) {
      const bad = copy(r);
      bad.equipment[0].parameters[key as string] = value;
      expect(engineeringRequirementsSchema.safeParse(bad).success).toBe(false);
    }
    for (const key of Object.keys(r.equipment[0].parameters)) {
      const bad = copy(r);
      delete bad.equipment[0].parameters[key];
      expect(engineeringRequirementsSchema.safeParse(bad).success).toBe(false);
    }
  });
  it('rejects PH temperature, PT out-of-domain temperature and independent inlet H', () => {
    const a = copy(ph);
    a.equipment[0].parameters.separator_temperature_K = 300;
    const b = copy(pt);
    b.equipment[0].parameters.separator_temperature_K = 501;
    const c = copy(pt);
    c.feeds[0].state.enthalpy_flow_W = 0;
    const d = copy(pt);
    d.components.push('water');
    for (const bad of [a, b, c, d])
      expect(engineeringRequirementsSchema.safeParse(bad).success).toBe(false);
  });
  it('makes mode-specific energy requirements explicit', () => {
    const modes = separatorEnergyDetailsSchema.options;
    expect(modes[0].shape.ph.safeParse({}).success).toBe(false);
    expect(modes[1].shape.duty_W.safeParse(1).success).toBe(false);
    expect(modes[1].shape.ph.safeParse(null).success).toBe(false);
  });
});
