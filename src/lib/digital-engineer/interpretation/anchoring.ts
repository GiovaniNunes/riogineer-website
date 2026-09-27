// A locator, never a semantic rewrite. Tokens retain case, numbers, signs,
// identifiers and unit operators. Offsets always refer to the untouched input.
type Token = { value: string; start: number; end: number };
function tokens(text: string): Token[] {
  const result: Token[] = [];
  const pattern =
    /[\p{L}_][\p{L}\p{N}_]*(?:[-‐‑‒–—][\p{L}\p{N}_]+)*|[+\-−‐‑‒–—]?\s*(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][+\-−]?\d+)?|[^\s]/gu;
  for (const match of text.matchAll(pattern)) {
    const raw = match[0];
    const start = match.index;
    // List markers are removable only at line starts before words, never numbers.
    if (
      /^[•*\-‐‑‒–—]$/.test(raw) &&
      /(?:^|\n)[\t ]*$/.test(text.slice(0, start)) &&
      /^[\t ]+[\p{L}_]/u.test(text.slice(start + raw.length))
    )
      continue;
    // Separators cannot join digits; numeric commas/decimals are one token above.
    if (
      /^[,:;]$/.test(raw) &&
      !(/\d\s*$/.test(text.slice(0, start)) && /^\s*\d/.test(text.slice(start + 1)))
    )
      continue;
    if (raw === '.' && !/\d/.test(text[start - 1] || '') && !/\d/.test(text[start + 1] || ''))
      continue;
    result.push({
      value: raw
        .trim()
        .replace(/[‐‑‒–—−]/g, '-')
        .replace(/\s+/g, ''),
      start: start + raw.length - raw.trimStart().length,
      end: start + raw.length,
    });
  }
  return result;
}

export function anchorEvidence(
  text: string,
  candidate: string,
):
  | { excerpt: string; start: number; end: number }
  | { reason: 'excerpt_not_exact' | 'excerpt_ambiguous' } {
  const source = tokens(text),
    locator = tokens(candidate);
  if (!locator.length) return { reason: 'excerpt_not_exact' };
  const matches: { start: number; end: number }[] = [];
  for (let i = 0; i <= source.length - locator.length; i++) {
    if (!locator.every((token, j) => token.value === source[i + j].value)) continue;
    // A locator cannot truncate a unit or mathematical expression at its edges.
    const before = source[i - 1];
    const after = source[i + locator.length];
    if ((before && /^[/+\-^−]$/.test(before.value)) || (after && /^[/^]$/.test(after.value)))
      continue;
    matches.push({ start: source[i].start, end: source[i + locator.length - 1].end });
    if (matches.length > 1) return { reason: 'excerpt_ambiguous' };
  }
  if (!matches.length) return { reason: 'excerpt_not_exact' };
  const match = matches[0];
  // Retain the entire exact candidate, including harmless edge punctuation,
  // only after checking uniqueness across formatting-equivalent occurrences.
  const exact = text.indexOf(candidate);
  if (exact !== -1 && exact <= match.start && exact + candidate.length >= match.end)
    return { excerpt: candidate, start: exact, end: exact + candidate.length };
  return { ...match, excerpt: text.slice(match.start, match.end) };
}
