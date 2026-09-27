// Identity-only normalization, never a property database or a numerical default.
// Every case registers its own explicit component basis. No fuzzy/chemical matching.
export function componentIdentifier(sourceName: string): string {
  const name = sourceName.trim();
  return /^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(name)
    ? name.toLowerCase().replaceAll('-', '_')
    : name;
}

export function registeredComponentIds(basis: unknown): string[] {
  return typeof basis === 'string' ? basis.split(',').map(componentIdentifier).filter(Boolean) : [];
  // Intentionally retain duplicates: collisions must block approval, not merge silently.
}
