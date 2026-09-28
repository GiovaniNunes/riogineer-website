"""Development models only: no property prediction or general thermal mixing."""

SPLIT_TOLERANCE = 1e-12
TEMPERATURE_TOLERANCE_K = 1e-8
PRESSURE_TOLERANCE_PA = 1e-8


def separator(unit, inputs, evaluate):
    p = unit['operating_parameters']
    result = evaluate(inputs['inlet'], p['separator'], p['recovery_fractions'], p['caloric_model'])
    return {port: result['streams'][port.upper()] for port in ('gas', 'oil', 'water')}, result['separator_duty_W']


def state_from_rates(rates, temperature, pressure, enthalpy):
    total = sum(rates.values())
    return dict(component_mass_flow_kg_h=rates, mass_flow_kg_h=total,
                component_mass_fractions={c: v / total for c, v in rates.items()} if total else None,
                temperature_K=temperature, pressure_Pa_abs=pressure, enthalpy_flow_W=enthalpy)


def splitter(unit, inputs, _evaluate):
    feed = inputs['inlet']
    fractions = unit['operating_parameters']['fractions']
    if abs(sum(fractions.values()) - 1) >= SPLIT_TOLERANCE:
        raise ValueError('Splitter fractions must sum to one; values are not normalized')
    return {port: state_from_rates({c: v * fraction for c, v in feed['component_mass_flow_kg_h'].items()},
                                  feed['temperature_K'], feed['pressure_Pa_abs'], feed['enthalpy_flow_W'] * fraction)
            for port, fraction in fractions.items()}, 0.0


def mixer(_unit, inputs, _evaluate):
    ordered = [inputs[p] for p in sorted(inputs)]
    first = ordered[0]
    for field, tolerance in [('temperature_K', TEMPERATURE_TOLERANCE_K), ('pressure_Pa_abs', PRESSURE_TOLERANCE_PA)]:
        values = [s[field] for s in ordered]
        if max(values) - min(values) > tolerance:
            raise ValueError(f'Unsupported mixer inlet {field}: equal conditions required (tolerance {tolerance}); no thermodynamic mixing is calculated')
    rates = {c: sum(s['component_mass_flow_kg_h'][c] for s in ordered) for c in first['component_mass_flow_kg_h']}
    return {'outlet': state_from_rates(rates, first['temperature_K'], first['pressure_Pa_abs'],
                                      sum(s['enthalpy_flow_W'] for s in ordered))}, 0.0


def heater(unit, inputs, _evaluate):
    feed = inputs['inlet']
    p = unit['operating_parameters']
    cal = p['caloric_model']
    rates = dict(feed['component_mass_flow_kg_h'])
    temperature = p['outlet_temperature_K']
    if temperature < feed['temperature_K']:
        raise ValueError('Heater outlet temperature cannot be below inlet temperature; cooling is not supported')
    duty = sum(rate * cal['cp_J_kg_K'][c] * (temperature - feed['temperature_K']) / 3600
               for c, rate in rates.items())
    enthalpy = sum(rate * cal['cp_J_kg_K'][c] * (temperature - cal['reference_temperature_K']) / 3600
                   for c, rate in rates.items())
    return {'outlet': state_from_rates(rates, temperature, feed['pressure_Pa_abs'], enthalpy)}, duty


# Port definitions, capability identity and execution live together, not in parallel registries.
MODELS = {
    'heater': {'model': {'id': 'specified_outlet_temperature_constant_cp', 'version': '1.0'},
               'ports': {'inlet': 'in', 'outlet': 'out'}, 'execute': heater},
    'three_phase_separator': {'model': {'id': 'prescribed_component_recoveries', 'version': '1.0'},
                             'ports': {'inlet': 'in', 'gas': 'out', 'oil': 'out', 'water': 'out'}, 'execute': separator},
    'splitter': {'model': {'id': 'proportional_split', 'version': '1.0'},
                 'ports': {'inlet': 'in', 'outlet_a': 'out', 'outlet_b': 'out'}, 'execute': splitter},
    'mixer': {'model': {'id': 'equal_condition_mix', 'version': '1.0'},
              'ports': {'inlet_a': 'in', 'inlet_b': 'in', 'outlet': 'out'}, 'execute': mixer},
}


def ports(kind):
    definitions = {'source': {'outlet': 'out'}, 'sink': {'inlet': 'in'}}
    spec = definitions[kind] if kind in definitions else MODELS[kind]['ports']
    return [{'id': name, 'direction': direction, 'kind': 'material'} for name, direction in spec.items()]
