/** Public form choices and limits; no provider credentials belong in this module. */
export const interests = [
  'Process Engineering',
  'Offshore Field Development',
  'Reservoir Engineering',
  'Artificial Intelligence',
  'Field Design',
  'Technology Partnership',
  'Other',
] as const;
export const contactLimits = {
  name: 120,
  company: 160,
  email: 254,
  country: 100,
  message: 5000,
  bodyBytes: 24576,
} as const;
export const contactAvailability = {
  enabled: false,
  message:
    'Message delivery is not available yet. This form can validate your entries, but your message will not be sent or saved.',
} as const;
