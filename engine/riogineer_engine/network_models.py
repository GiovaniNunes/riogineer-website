"""Development models only: no property prediction or general thermal mixing."""

from dataclasses import dataclass, field
import math


@dataclass
class EquipmentResult:
    streams: dict
    duty_W: float | None
    work_W: float | None = 0.0
    details: dict = field(default_factory=dict)


def equipment_result(value):
    """Adapt existing heat-only models without changing their qualified equations."""
    return value if isinstance(value, EquipmentResult) else EquipmentResult(*value)


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
    if unit['model']['id'] == 'equilibrium_energy_balance_pr':
        from .heater_cooler_energy import heater as rigorous_heater
        return rigorous_heater(unit, inputs, _evaluate)
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


def compressor(unit, inputs, _evaluate):
    if unit['model']['id'] == 'rigorous_isentropic_pr':
        from .compressor_energy import compressor as rigorous_compressor
        return rigorous_compressor(unit, inputs, _evaluate)
    if set(inputs) != {'inlet'}:
        raise ValueError('Compressor requires exactly one inlet')
    feed = inputs['inlet']
    p = unit['operating_parameters']
    t1, p1 = feed['temperature_K'], feed['pressure_Pa_abs']
    p2, cp, k = p['discharge_pressure_Pa_abs'], p['cp_J_kg_K'], p['heat_capacity_ratio']
    eta, mechanical = p['isentropic_efficiency'], p['mechanical_efficiency']
    rates = dict(feed['component_mass_flow_kg_h'])
    mass = sum(rates.values())
    if any(not math.isfinite(v) or v <= 0 for v in (t1, p1, p2, cp, mass)):
        raise ValueError('Compressor requires finite positive temperature, pressures, Cp and mass flow')
    if any(not math.isfinite(v) or v < 0 for v in rates.values()):
        raise ValueError('Compressor component flows must be finite and nonnegative')
    if p2 <= p1:
        raise ValueError('Compressor discharge pressure must exceed inlet pressure')
    if not math.isfinite(k) or k <= 1:
        raise ValueError('Compressor heat capacity ratio k must be finite and greater than one')
    if any(not math.isfinite(v) or not 0 < v <= 1 for v in (eta, mechanical)):
        raise ValueError('Compressor efficiencies must be finite and in (0, 1]')
    if p['inlet_phase'] != 'gas':
        raise ValueError('Compressor requires an explicitly assumed gas inlet; no liquid handling')
    ratio = p2 / p1
    t2s = t1 * ratio ** ((k - 1) / k)
    t2 = t1 + (t2s - t1) / eta
    gas = mass / 3600 * cp * (t2 - t1)
    shaft = gas / mechanical
    enthalpy = feed['enthalpy_flow_W'] + gas
    if any(not math.isfinite(v) for v in (ratio, t2s, t2, gas, shaft, enthalpy)):
        raise ValueError('Compressor calculated temperatures and powers must be finite')
    details = dict(inlet_pressure_Pa_abs=p1, discharge_pressure_Pa_abs=p2, pressure_ratio=ratio,
                   inlet_temperature_K=t1, isentropic_discharge_temperature_K=t2s, discharge_temperature_K=t2,
                   cp_J_kg_K=cp, heat_capacity_ratio=k, isentropic_efficiency=eta,
                   mechanical_efficiency=mechanical, gas_power_W=gas, shaft_power_W=shaft,
                   mechanical_loss_W=shaft-gas)
    return EquipmentResult({'outlet': state_from_rates(rates, t2, p2, enthalpy)}, 0.0, gas,
                           {'compression': details})


def equilibrium_separator(unit, inputs, evaluate):
    if unit['model']['id'] == 'equilibrium_separator_energy_pr':
        from .separator_energy import separator as energy_separator
        return energy_separator(unit, inputs, evaluate)
    from .equilibrium_separator import separator
    return separator(unit, inputs, evaluate)


def two_stream_heat_exchanger(unit, inputs, _evaluate):
    from .two_stream_heat_exchanger_energy import exchanger
    return exchanger(unit, inputs)


def throttling_valve(unit, inputs, _evaluate):
    from .throttling_valve_energy import valve
    return valve(unit, inputs)


# Port definitions, capability identity and execution live together, not in parallel registries.
def pump(unit, inputs, evaluate):
    from .pump_energy import pump as execute
    return execute(unit, inputs, evaluate)


MODELS = {
    'pump': {'model': {'id': 'rigorous_isentropic_pump_pr', 'version': '1.0'},
             'ports': {'inlet': 'in', 'outlet': 'out'}, 'execute': pump},
    'throttling_valve': {'model': {'id': 'rigorous_isenthalpic_pr', 'version': '1.0'},
        'ports': {'inlet': 'in', 'outlet': 'out'}, 'execute': throttling_valve},
    'two_stream_heat_exchanger': {'model': {'id': 'rigorous_two_stream_pr', 'version': '1.0'},
        'ports': {'hot_in': 'in', 'hot_out': 'out', 'cold_in': 'in', 'cold_out': 'out'},
        'execute': two_stream_heat_exchanger},
    'equilibrium_separator_2phase': {'model': {'id': 'pt_flash_separator', 'version': '1.0'},
        'ports': {'inlet': 'in', 'vapor': 'out', 'liquid': 'out'}, 'execute': equilibrium_separator},
    'compressor': {'model': {'id': 'ideal_gas_isentropic_efficiency', 'version': '1.0'},
                   'ports': {'inlet': 'in', 'outlet': 'out'}, 'execute': compressor},
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
