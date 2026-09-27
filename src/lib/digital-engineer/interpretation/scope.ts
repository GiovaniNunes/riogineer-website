// Only standalone, explicitly negative scope statements qualify. No keyword stripping,
// substring negation or global "this capability was excluded somewhere" suppression.
export function isExplicitScopeExclusion(excerpt: string | undefined): boolean {
  if (!excerpt) return false;
  return /^(?:rigorous (?:vapor-oil-water )?equilibrium|vapor-oil-water equilibrium|equilibrium|separator sizing|geometry-based separation efficiency) is outside the (?:requested )?calculation scope\.?$/i.test(
    excerpt.trim(),
  );
}
