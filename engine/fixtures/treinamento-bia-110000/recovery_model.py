"""Prescribed separator material model v1.0; existing balance equations extracted for reuse."""
import math

IDS = ('FEED', 'GAS', 'OIL', 'WATER')


def evaluate(feed, separator, recoveries, cal):
    flow = feed['component_mass_flow_kg_h']
    if not flow or set(flow)!=set(recoveries) or set(flow)!=set(cal['cp_J_kg_K']):
        raise ValueError('Component keys must agree across feed, recoveries and Cp')
    def numeric(v,positive=False):
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or (positive and v==0):
            raise ValueError('Invalid model input number')
    for state in [feed,separator]:
        numeric(state['temperature_K'],True);numeric(state['pressure_Pa_abs'],True)
    numeric(cal['reference_temperature_K'],True)
    for name,value in flow.items():
        numeric(value);numeric(cal['cp_J_kg_K'][name],True)
        row=recoveries[name]
        if set(row)!={'gas','oil','water'}:raise ValueError('Invalid recovery ports')
        for v in row.values():
            numeric(v)
            if v>1:raise ValueError('Recovery exceeds one')
        if abs(sum(row.values())-1)>=1e-12:raise ValueError('Recoveries must sum to one')
    if sum(flow.values())<=0:raise ValueError('Positive feed required')
    def state(fl, t, p):
        total = sum(fl.values())
        return dict(component_mass_flow_kg_h=fl, mass_flow_kg_h=total,
                    component_mass_fractions={n: v/total for n, v in fl.items()} if total else None,
                    temperature_K=t, pressure_Pa_abs=p,
                    enthalpy_flow_W=sum(fl[n]*cal['cp_J_kg_K'][n]*(t-cal['reference_temperature_K'])/3600 for n in fl))
    streams = {'FEED': state(flow, feed['temperature_K'], feed['pressure_Pa_abs'])}
    for sid in IDS[1:]:
        streams[sid] = state({n: v*recoveries[n][sid.lower()] for n, v in flow.items()},
                             separator['temperature_K'], separator['pressure_Pa_abs'])
    outlet_h = sum(streams[s]['enthalpy_flow_W'] for s in IDS[1:])
    duty = outlet_h-streams['FEED']['enthalpy_flow_W']
    mass = {n: flow[n]-sum(streams[s]['component_mass_flow_kg_h'][n] for s in IDS[1:]) for n in flow}
    energy = streams['FEED']['enthalpy_flow_W']+duty-outlet_h
    return dict(streams=streams, separator_duty_W=duty, component_mass_residual_kg_h=mass,
                energy_residual_W=energy, checks_passed=all(abs(v)<1e-8 for v in mass.values()) and abs(energy)<1e-6)
