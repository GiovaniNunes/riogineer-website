import type { Flowsheet } from './contracts';

// Presentation only. Stable IDs and engineering numbers are never assigned here.
export function graphLayout(flowsheet: Flowsheet) {
  const nodes = [...flowsheet.boundaries, ...flowsheet.equipment];
  const levels = new Map<string, number>();
  const pending = new Set(nodes.map((n) => n.id));
  while (pending.size) {
    const ready = [...pending]
      .sort()
      .filter((id) =>
        flowsheet.connections
          .filter((c) => c.target.owner_id === id)
          .every((c) => levels.has(c.source.owner_id)),
      );
    if (!ready.length) throw new Error('Acyclic PFD layout requires a validated graph.');
    for (const id of ready) {
      const incoming = flowsheet.connections.filter((c) => c.target.owner_id === id);
      levels.set(id, Math.max(0, ...incoming.map((c) => levels.get(c.source.owner_id)! + 1)));
      pending.delete(id);
    }
  }
  const layers = Array.from({ length: Math.max(...levels.values()) + 1 }, (_, level) =>
    nodes.filter((n) => levels.get(n.id) === level).sort((a, b) => a.id.localeCompare(b.id)),
  );
  const height = Math.max(...layers.map((layer) => layer.length)) * 180 + 60;
  const positions = new Map(
    layers.flatMap((layer, level) =>
      layer.map(
        (node, index) =>
          [
            node.id,
            { x: 30 + level * 320, y: ((index + 0.5) * (height - 60)) / layer.length + 30 - 45 },
          ] as const,
      ),
    ),
  );
  function point(owner: string, port: string) {
    const node = nodes.find((n) => n.id === owner)!;
    const direction = node.ports.find((p) => p.id === port)!.direction;
    const ports = node.ports
      .filter((p) => p.direction === direction)
      .sort((a, b) => a.id.localeCompare(b.id));
    const p = positions.get(owner)!;
    return {
      x: p.x + (direction === 'out' ? 160 : 0),
      y: p.y + (90 * (ports.findIndex((p) => p.id === port) + 1)) / (ports.length + 1),
    };
  }
  return { nodes, positions, point, height, width: layers.length * 320 - 100 };
}
