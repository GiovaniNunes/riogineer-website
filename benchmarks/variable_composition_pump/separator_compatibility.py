"""Actual M17 liquid outlets; no stream T/P/rate edits, no production integration."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'engine'))
from riogineer_engine.milestone17 import requirements as separator
from riogineer_engine.milestone19 import requirements as pump_requirements
from riogineer_engine.core import build_flowsheet,calculate
from riogineer_engine.thermodynamics import MolecularCompositionProvider
from riogineer_engine.variable_pump_energy import inlet_specification,pump,PumpFailure
HERE=Path(__file__).resolve().parent

def run():
 path=ROOT/'benchmarks/two_phase_separator_energy/methane_nhexane_separator_energy_reference.json'
 cases=json.loads(path.read_text())['cases']
 cases=cases+[dict(case_id='ADDITIONAL_HIGH_PRESSURE_LIQUID',inputs=dict(mode='specified_temperature',Pin=30e6,Tin=300.,Pout=20e6,Tout=300.,F=100.,z=[.25,.75]))]
 rows=[]
 for c in cases:
  r=calculate(build_flowsheet(separator(**c['inputs'])))
  # M17 material-port mapping owns stream identity.
  e=r['equipment'][0]; sid=e['material_streams']['liquid'];s=r['streams'][sid]
  row=dict(case_id=c['case_id'],actual_liquid=s,separator_thermodynamics=e['thermodynamics'])
  if s['mass_flow_kg_h']==0:row.update(direct=False,reasons=['absent_liquid'])
  else:
   m=MolecularCompositionProvider().enrich(s);z=m.composition.molar_fractions['methane'];F=m.composition.molar_flow_kmol_h/3.6
   T=s['temperature_K'];P=s['pressure_Pa_abs'];reasons=[]
   if not .01<=z<=.55:reasons.append('composition_scope')
   if not 300<=T<=350:reasons.append('temperature_scope')
   if not 20e6<=P<=25e6:reasons.append('pressure_scope')
   if not 5<=F<=200:reasons.append('flow_scope')
   row.update(z_methane=z,F_mol_s=F,pressure_shortfall_Pa=max(0,20e6-P),pressure_excess_Pa=max(0,P-25e6),temperature_shortfall_K=max(0,300-T),temperature_excess_K=max(0,T-350),reasons=reasons,direct=False)
   if not reasons:
    u=pump_requirements()['equipment'][0]
    # PT-based model has no independent enthalpy input. Retain actual H above,
    # recompute from unchanged PT/rates, and REQUIRE identical H before direct claim.
    feed=dict(s,enthalpy_flow_W=None)
    v=pump(dict(u,operating_parameters=u['parameters']),{'inlet':feed});d=v.details['thermodynamics']
    residual=d['F_mol_s']*d['inlet']['H_eq_J_mol']-s['enthalpy_flow_W']
    assert abs(residual)<=F*1e-6
    row.update(direct=True,enthalpy_convention_residual_W=residual,pump_thermodynamics=d)
  rows.append(row);print(c['case_id'],row['direct'],row['reasons'],flush=True)
 out=dict(separator_reference_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cases=rows,direct_count=sum(r['direct'] for r in rows),production_network_integration=False)
 (HERE/'separator_compatibility.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':run()
