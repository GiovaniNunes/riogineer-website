// Bounded grammar for the existing single-separator capability. Every character
// must be consumed: extra equipment, counts, branches and unknown clauses fail.
export const singleSeparatorTopology = 'one_feed_one_separator_gas_oil_water';

function wording(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[‐‑–—]/g, '-')
    .replace(/\s+/g, ' ')
    .replace(/[.]$/, '')
    .trim();
}
function outlets(value: string): boolean {
  const list = wording(value)
    .replace(
      /^(?:(?:the )?(?:three|3) )?(?:outlet streams are|outlets are|outlet streams|outlets)\s*:?\s*/,
      '',
    )
    .replace(/\s+(?:outlets|outlet streams)$/, '');
  const ids = list
    .replace(/^\((.*)\)$/, '$1')
    .split(/\s*(?:,\s*(?:and\s+)?|\band\b|\+|\/)\s*/)
    .map((part) => part.replace(/\s+(?:outlet|outlet stream)$/, '').trim());
  return (
    ids.length === 3 &&
    new Set(ids).size === 3 &&
    ids.every((id) => ['gas', 'oil', 'water'].includes(id))
  );
}

export function normalizeTopology(value: string, explicitOutputs?: string): string {
  const text = wording(value);
  if (
    text === singleSeparatorTopology ||
    text === 'uma alimentação, um separador, saídas de gás, óleo e água'
  )
    return singleSeparatorTopology;
  const one = '(?:exactly one|one|1|a single|single|a)';
  const feed = `${one} feed(?: stream)?`;
  const separator = `${one} (?:three[- ]phase )?separator`;
  const prefix =
    '(?:(?:the )?process (?:shall comprise|comprises|consists of|shall consist of) |topology: )?';
  const connection =
    '(?:entering|enters|feeding|feeds|flows into|flowing into|connected to|to|->|→|,)';
  const match =
    text.match(new RegExp(`^${prefix}${feed}\\s*${connection}\\s*${separator}(.*)$`)) ||
    text.match(new RegExp(`^${prefix}${separator} (?:receiving|receives|fed by) ${feed}(.*)$`));
  if (!match) return value;
  const remainder = match[1].trim();
  if (!remainder)
    return explicitOutputs && outlets(explicitOutputs) ? singleSeparatorTopology : value;
  const suffix = remainder.replace(
    /^(?:[,;]\s*|with\s+|producing\s+|->\s*|→\s*|\.\s*(?:the separator )?(?:shall have|has)\s+)/,
    '',
  );
  // A suffix needs an explicit connection/separator; do not accept concatenation.
  if (suffix === remainder || !outlets(suffix)) return value;
  return singleSeparatorTopology;
}
