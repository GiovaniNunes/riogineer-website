"""Read-only check: every historical contract branch and shared definition survives."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def verify():
    baseline=json.loads((ROOT/'benchmarks/m22_separator_pump/baseline.json').read_text())
    rows=[]
    for name in ('requirements','flowsheet','results','validation'):
        path='contracts/v1/'+name+'.schema.json'
        old=json.loads(subprocess.check_output(['git','show',baseline['head']+':'+path],cwd=ROOT))
        new=json.loads((ROOT/path).read_text())
        a=old if name!='validation' else old['properties']['requirements']
        b=new if name!='validation' else new['properties']['requirements']
        assert all(x in b['anyOf'] for x in a['anyOf']),name
        assert len(b['anyOf'])==len(a['anyOf'])+1
        assert old.get('$defs')==new.get('$defs'),name+' definitions'
        if name=='validation':
            old['properties'].pop('requirements');new['properties'].pop('requirements')
            assert old==new
        rows.append(dict(contract=name,historical_branches=len(a['anyOf']),current_branches=len(b['anyOf']),historical_branches_and_definitions_unchanged=True))
    result=dict(baseline_head=baseline['head'],checks=rows,method='literal structural equality of each historical branch and all shared definitions; one additive branch per contract')
    assert result==json.loads((ROOT/'benchmarks/m22_separator_pump/contract_compatibility.json').read_text())
    return result

if __name__=='__main__':
    verify();print('PASS unchanged historical schema branches/shared definitions; one explicit additive branch per contract')
