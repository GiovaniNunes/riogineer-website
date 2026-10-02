/** Display rounding only: never change the underlying calculation or export. */
export function formatEngineeringNumber(value: number | null, maximumFractionDigits = 6) {
  if (value === null) return '—';
  const rendered = new Intl.NumberFormat('en-US', { maximumFractionDigits }).format(value);
  // With zero minimum fraction digits, any rounded negative zero renders as "-0".
  return rendered === '-0' ? '0' : rendered;
}
