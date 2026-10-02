"""Input matrix and immutable artifact I/O; no thermodynamic computation."""
import json
from pathlib import Path
from benchmarks.pump_energy.common import ROOT, encode, digest, TOLS, IDS
from benchmarks.low_pressure_separator_pump.phase_contract.common import source_specs
from benchmarks.low_pressure_separator_pump.common import cases as old_cases
HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/name).read_text())
def save(name,data,write=False):
    p=HERE/name;raw=encode(data)
    if write:
        assert not p.exists(), 'Refuse to overwrite '+str(p)
        p.write_text(raw)
    else:assert p.read_text()==raw, name+' reproduction differs'
    print(name,digest(p),flush=True)

def matrix():
    specs=source_specs(); rows=[]
    accepted=json.loads((ROOT/'benchmarks/low_pressure_separator_pump/production.json').read_text())['cases']
    for c in accepted:
        if c['disposition']=='accepted_tuple':
            source=c['case_id'] if c['role']=='scaled_flow' else c['source']
            rows.append(dict(case_id=c['case_id'],source=source,role='M20_anchor',P2=c['inputs']['P2'],eta=c['inputs']['eta']))
    for c in old_cases():
        if c['role']=='historical_solver_challenge':rows.append(dict(case_id=c['case_id'],source=c['source'],role='8MPa_challenge',P2=8e6,eta=.8))
    def add(name,source,role='interior',dp=5e5,eta=.8):
        rows.append(dict(case_id=name,source=source,role=role,P2=specs[source]['Pout']+dp,eta=eta))
    for source in ('PT_VL_HEATING','PH_FLASH','PT_BUBBLE_BELOW','PT_BUBBLE_ABOVE','PT_DEW_BELOW'):
        add(source+'_MID',source,dp=5e5,eta=.7)
        add(source+'_HOLDOUT',source,'off_grid_holdout',dp=173456.,eta=.873)
    variations=[('PT_COOL','PT_VL_HEATING',dict(Tout=345.)),('PT_WARM','PT_VL_HEATING',dict(Tout=355.)),
      ('PT_P_HOLDOUT','PT_VL_HEATING',dict(Pout=337000.,Tout=348.3)),
      ('PT_Z','PT_VL_HEATING',dict(z=[.45,.55])),
      ('PH_PIN','PH_FLASH',dict(Pin=28e6)),('PH_TIN','PH_FLASH',dict(Tin=303.7)),
      ('PH_POUT','PH_FLASH',dict(Pout=1.173e6)),('PH_Z','PH_FLASH',dict(z=[.47,.53])),
      ('COLD_COMPRESSED','PT_BUBBLE_BELOW',dict(Tout=specs['PT_BUBBLE_BELOW']['Tout']-.1)),
      ('COLD_SATURATED','PT_BUBBLE_ABOVE',dict(Tout=specs['PT_BUBBLE_ABOVE']['Tout']+.1)),
      ('WARM_HOLDOUT','PT_DEW_BELOW',dict(Tout=specs['PT_DEW_BELOW']['Tout']-.1)),
      ('FLOW_HOLDOUT','PH_FLASH',dict(F=137.))]
    for name,parent,patch in variations:
        specs[name]=specs[parent]|patch
        add(name,name,'source_variation',dp=731000.,eta=.83)
    for dp in (0.,10.,100.,999.,1001.,10000.):add('WORK_'+str(dp),'PH_FLASH','work_boundary',dp=dp)
    add('ETA_LOW','PH_FLASH','negative',eta=.599)
    add('ETA_HIGH','PH_FLASH','negative',eta=1.001)
    add('DECREASE','PH_FLASH','negative',dp=-1.)
    add('ABSENT','PT_VAPOR','negative',dp=1000.)
    return specs,rows

def pump_inputs(source,row):
    r=source['result'];e=r['equipment'][0];s=r['streams'][e['material_streams']['liquid']];p=e['thermodynamics']['phases']['liquid']
    return dict(T1=s['temperature_K'],P1=s['pressure_Pa_abs'],P2=row['P2'],eta=row['eta'],flow=p['molar_flow_mol_s'],z=list(p['composition'].values()) if p['composition'] else None)
