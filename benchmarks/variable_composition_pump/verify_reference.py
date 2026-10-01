"""Verify frozen provenance against this independent environment, then evidence."""
import inspect,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from benchmarks.pump_energy.common import digest
from benchmarks.peng_robinson_caloric import reference as caloric
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
r=json.loads((HERE/'reference.json').read_text())
for p,h in r['source_sha256'].items():assert digest(ROOT/p)==h,p
assert r['cp_source_sha256']==digest(Path(caloric.hc.__file__).parent/'Heat Capacity/PolingDatabank.tsv')
actual={Path(inspect.getfile(o)).name:digest(inspect.getfile(o)) for o in (caloric.PR,caloric.PRMIX,caloric.CEOSGas,caloric.FlashVL,caloric.HeatCapacityGas)}
assert actual==r['library_source_sha256']
assert r['boundary_summary']['accepted']==r['boundary_summary']['count']==824
assert r['boundary_summary']['engineering_reserve_Pa']>0
assert sum(c['accepted'] for c in r['cases'])==53
assert not any(n.startswith('riogineer_engine') for n in sys.modules)
print('Frozen source, installed library and Cp hashes verified; 824 boundary points, 53 supported pump cases.')
