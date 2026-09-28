import type { Flowsheet } from '@/lib/digital-engineer/contracts';
import { graphLayout } from '@/lib/digital-engineer/pfd-layout';
import { streamLabel } from '@/lib/digital-engineer/stream-label';
export function Pfd({ flowsheet }: { flowsheet: Flowsheet }) {
  if (flowsheet.schema_version === '1.2' || flowsheet.schema_version === '1.3')
    return <NetworkPfd flowsheet={flowsheet} />;
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
                {streamLabel(stream)}
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

function NetworkPfd({ flowsheet }: { flowsheet: Flowsheet }) {
  const { nodes, positions, point, width, height } = graphLayout(flowsheet);
  return (
    <figure
      aria-label="Read-only process flow diagram"
      style={{ overflowX: 'auto', marginInline: 0 }}
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ minWidth: 1100 }}
        role="img"
        aria-labelledby="network-pfd-title"
      >
        <title id="network-pfd-title">Multi-equipment PFD</title>
        <defs>
          <marker
            id="network-flow-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
          </marker>
        </defs>
        {flowsheet.connections.map((c) => {
          const a = point(c.source.owner_id, c.source.port_id),
            b = point(c.target.owner_id, c.target.port_id);
          const mid = (a.x + b.x) / 2;
          const stream = flowsheet.streams.find((s) => s.id === c.stream_id)!;
          return (
            <g key={c.id} data-stream-id={stream.id}>
              <path
                d={`M ${a.x} ${a.y} H ${mid} V ${b.y} H ${b.x}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                markerEnd="url(#network-flow-arrow)"
              />
              <text x={b.x - 8} y={b.y - 10} textAnchor="end" fontSize="13">
                {streamLabel(stream)}
              </text>
            </g>
          );
        })}
        {nodes.map((node) => {
          const p = positions.get(node.id)!;
          return (
            <g key={node.id} data-equipment-id={node.id}>
              <rect
                x={p.x}
                y={p.y}
                width="160"
                height="90"
                rx={node.type === 'three_phase_separator' ? 25 : 6}
                fill="var(--color-surface)"
                stroke="currentColor"
                strokeWidth="2"
              />
              {node.type === 'heater' && (
                <path
                  data-symbol="heater"
                  d={`M ${p.x + 20} ${p.y + 75} l 15 -8 l 15 16 l 15 -16 l 15 16 l 15 -16 l 15 8`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              )}
              <text
                x={p.x + 80}
                y={p.y + 37}
                textAnchor="middle"
                fontSize="16"
                fontWeight="bold"
                textLength={node.id.length > 14 ? 140 : undefined}
                lengthAdjust="spacingAndGlyphs"
              >
                {node.id}
              </text>
              <text x={p.x + 80} y={p.y + 60} textAnchor="middle" fontSize="11">
                {node.type.replaceAll('_', ' ')}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption>
        Read-only PFD · Numbered material streams and ports from the structured flowsheet · Scroll
        horizontally if needed
      </figcaption>
    </figure>
  );
}
