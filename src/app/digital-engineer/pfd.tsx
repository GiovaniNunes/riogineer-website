import type { Flowsheet } from '@/lib/digital-engineer/contracts';
export function Pfd({ flowsheet }: { flowsheet: Flowsheet }) {
  const nodes = [...flowsheet.boundaries, ...flowsheet.equipment];
  const sinks = flowsheet.boundaries.filter((n) => n.type === 'sink');
  const positions = Object.fromEntries(
    nodes.map((n) => [
      n.id,
      n.type === 'source'
        ? { x: 15, y: 145 }
        : n.type === 'sink'
          ? { x: 675, y: 35 + sinks.indexOf(n) * 115 }
          : { x: 300, y: 140 },
    ]),
  );
  function point(owner: string, port: string) {
    const n = positions[owner];
    const equipment = flowsheet.equipment.some((e) => e.id === owner);
    return {
      x: n.x + (port === 'inlet' ? 0 : 200),
      y:
        n.y +
        (equipment && port !== 'inlet'
          ? { gas: 15, oil: 40, water: 65 }[port as 'gas' | 'oil' | 'water']
          : 40),
    };
  }
  return (
    <figure aria-label="Read-only process flow diagram">
      <svg viewBox="0 0 900 390" role="img" aria-labelledby="pfd-title pfd-desc">
        <title id="pfd-title">Three-phase separator PFD</title>
        <desc id="pfd-desc">
          Generated from flowsheet.json equipment, ports and connections. One feed source and three
          product sinks. Read-only.
        </desc>
        <defs>
          <marker
            id="flow-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
          </marker>
        </defs>
        {flowsheet.connections.map((c) => {
          const a = point(c.source.owner_id, c.source.port_id),
            b = point(c.target.owner_id, c.target.port_id);
          const stream = flowsheet.streams.find((s) => s.id === c.stream_id)!;
          const mid = (a.x + b.x) / 2;
          return (
            <g key={c.id} data-stream-id={stream.id}>
              <path
                d={`M ${a.x} ${a.y} H ${mid} V ${b.y} H ${b.x}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                markerEnd="url(#flow-arrow)"
              />
              <text x={mid} y={b.y - 9} fontSize="14" textAnchor="middle">
                {'engineering_number' in stream ? `${stream.engineering_number} · ` : ''}
                {stream.service.toUpperCase()}
              </text>
            </g>
          );
        })}
        {nodes.map((n) => {
          const p = positions[n.id];
          return (
            <g key={n.id}>
              <rect
                x={p.x}
                y={p.y}
                width="200"
                height="80"
                rx={n.type === 'three_phase_separator' ? 30 : 5}
                fill="var(--color-surface)"
                stroke="currentColor"
                strokeWidth="2"
              />
              <text x={p.x + 100} y={p.y + 35} textAnchor="middle" fontSize="15" fontWeight="bold">
                {n.id}
              </text>
              <text x={p.x + 100} y={p.y + 58} textAnchor="middle" fontSize="12">
                {n.type.replaceAll('_', ' ')}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption>
        Read-only PFD · Generated from flowsheet.json · Ports: inlet, gas, oil, water
      </figcaption>
    </figure>
  );
}
