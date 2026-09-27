"""Engineering stream identity metadata; no property estimation or equations."""
from collections import deque


def number_streams(streams, connections, source_ids):
    """Preserve existing numbers; number new IDs by deterministic directed breadth-first walk.

    Start at source IDs in lexical order, visit outgoing ports in lexical order,
    then target owner/port and stream ID. Disconnected/cyclic remainder uses the
    same endpoint ordering. This helper does not authorize any process topology.
    """
    by_id = {s['id']: s for s in streams}
    if len(by_id) != len(streams) or {c['stream_id'] for c in connections} != set(by_id) or len(connections) != len(streams):
        raise ValueError('Every unique stream needs exactly one connection')
    used = [s['engineering_number'] for s in streams if 'engineering_number' in s]
    if any(type(n) is not int or n <= 0 for n in used) or len(set(used)) != len(used):
        raise ValueError('Stream numbers must be unique positive integers')
    key = lambda c: (c['source']['owner_id'], c['source']['port_id'], c['target']['owner_id'], c['target']['port_id'], c['stream_id'])
    ordered = sorted(connections, key=key)
    queue = deque(sorted(set(source_ids)))
    visited, assigned = set(), set()
    next_number = max(used, default=0) + 1

    def assign(c):
        nonlocal next_number
        stream = by_id[c['stream_id']]
        if 'engineering_number' not in stream:
            stream['engineering_number'] = next_number
            next_number += 1
        assigned.add(stream['id'])

    while queue:
        owner = queue.popleft()
        if owner in visited:
            continue
        visited.add(owner)
        for connection in ordered:
            if connection['source']['owner_id'] == owner:
                assign(connection)
                queue.append(connection['target']['owner_id'])
    for connection in ordered:
        if connection['stream_id'] not in assigned:
            assign(connection)


def unavailable_properties():
    units = {'molar_flow': 'kmol/h', 'molecular_mass': 'kg/kmol', 'density': 'kg/m3',
             'gas_volumetric_flow': 'm3/h', 'oil_volumetric_flow': 'm3/h', 'water_volumetric_flow': 'm3/h',
             'molar_composition': 'mol/mol'}
    return {name: {'value': None, 'status': 'not_calculated', 'unit': unit}
            for name, unit in units.items()}
