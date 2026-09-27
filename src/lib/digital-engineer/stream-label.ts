import type { Flowsheet } from './contracts';

// Format stored identity only; numbering belongs to the structured flowsheet builder.
export function streamLabel(stream: Flowsheet['streams'][number]) {
  const number = 'engineering_number' in stream ? stream.engineering_number : 'Unnumbered';
  return `${number} — ${stream.service.toUpperCase()}`;
}
