"""Audit every original assertion, including comparisons masked by failures."""
import json, hashlib, sys, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'engine')]
from benchmarks.m21_pt200.review.archive import pins
from riogineer_engine.core import semantic_hash,build_flowsheet
from riogineer_engine.milestone20 import requirements
from riogineer_engine.separator_pump_scope import CASES

def build():
    read=lambda p:json.loads((ROOT/p).read_text())
    before=read('benchmarks/m21_pt200/baseline.json')['files']
    start=read('benchmarks/m21_pt200/review/baseline.json')['files']
    rows=[]
    def add(test,identity,expected,observed,classification,coverage,masked=False):
        rows.append(dict(test=test,assertion=identity,expected=expected,observed=observed,mismatch=expected!=observed,mismatch_at_review_start=expected!=observed,classification=classification,authorized_M21_edit=classification=='authorized M21 source change',evidence='Original frozen manifest; M21 baseline.json; review/baseline.json; historical_manifest.json',ongoing_coverage=coverage,masked_in_original_log=masked))
    for group,entries in pins().items():
        failed=False
        for path,expected in entries.items():
            observed=start[path]
            classification='unchanged' if expected==observed else ('authorized M21 source change' if before[path]!=observed else 'predates M21')
            coverage='historical_integrity('+group+'); source_verify; current independent numerical regression' if path.startswith('engine/') else ('review preservation; archive --require-complete reports unavailable old next-env' if path=='next-env.d.ts' else 'historical_integrity('+group+'); review preservation')
            add('M19.test_equipment_comparison_and_source_capture' if group=='M19' else 'M20.test_preservation',path,expected,observed,classification,coverage,group=='M19' and failed)
            failed |= expected!=observed
    e=read('benchmarks/m20_separator_pump/implementation.json')
    add('M20.test_all30_fresh_evidence','failed_checks',0,e['failed_checks'],'unchanged','retained')
    add('M20.test_all30_fresh_evidence','case set',sorted(c['qualification_id'] for c in CASES),sorted(c['case_id'] for c in e['cases']),'unchanged','retained')
    for n,c in enumerate(e['cases']):
        add('M20.test_all30_fresh_evidence',c['case_id']+' all frozen checks passed',True,all(q['passed'] for q in c['checks']),'unchanged','retained',n>0)
        add('M20.test_all30_fresh_evidence',c['case_id']+' input_sha256',c['result']['input_sha256'],semantic_hash(build_flowsheet(requirements(c['case_id']))),'authorized M21 source change','archived_m20_semantics reproduces historical identities; current_m20 compares all30 to frozen independent references and current hashes',n>0)
    b=read('benchmarks/m20_separator_pump/baseline.json')
    add('M20.test_preservation','master prefix',b['sha256']['docs/RIOGINEER_MASTER_CONTEXT.md'],hashlib.sha256((ROOT/'docs/RIOGINEER_MASTER_CONTEXT.md').read_bytes()[:b['master_prefix_bytes']]).hexdigest(),'unchanged','retained')
    e=read('benchmarks/variable_composition_pump/equipment_comparison.json')
    for key,expected in [('passed',True),('case_count',64)]:add('M19.test_equipment_comparison_and_source_capture',key,expected,e[key],'unchanged','retained')
    original=[]
    raw=(ROOT/'benchmarks/m21_pt200/logs/full-python.log').read_text()
    for section in raw.split('FAIL: ')[1:]:
        label=section.splitlines()[0]
        pair=re.search(r"AssertionError: '([0-9a-f]{64})' != '([0-9a-f]{64})'",section)
        if pair:
            a,b=pair.groups()
            original.append(dict(test=label,expected=a if 'test_all30' in label else b,observed=b if 'test_all30' in label else a))
    assert len(original)==7
    return dict(original_log_observations=original,original_log='benchmarks/m21_pt200/logs/full-python.log',assertions=rows,assertion_count=len(rows),mismatches=sum(r['mismatch'] for r in rows),masked_mismatches=sum(r['mismatch'] and r['masked_in_original_log'] for r in rows),note='Observed values are final review-start bytes, not intermediate values in the original failed log. Historical reproduction is pinned-byte integrity plus semantic construction, not a historical numerical solver rerun.')
if __name__=='__main__':
    r=build();(HERE/'assertion_ledger.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    lines=['# Complete historical assertion ledger','',r['note'],'',f"{r['assertion_count']} assertions; {r['mismatches']} mismatches, {r['masked_mismatches']} masked mismatches. Every mismatch existed at review start.",'','| Test / assertion | Expected | Observed | Classification / retained coverage |','|---|---|---|---|']
    for row in r['assertions']:
        lines.append('| '+row['test']+' / '+row['assertion']+' | `'+json.dumps(row['expected'])+'` | `'+json.dumps(row['observed'])+'` | '+row['classification']+'; '+row['ongoing_coverage']+(' (masked)' if row['masked_in_original_log'] else '')+' |')
    lines += ['', '## Original logged failures', '', 'These intermediate observations are preserved separately from the final review-start values above.', '', '| Original failure | Expected | Observed in original log |', '|---|---|---|']
    for row in r['original_log_observations']:
        lines.append('| '+row['test']+' | `'+row['expected']+'` | `'+row['observed']+'` |')
    (HERE/'ASSERTION_LEDGER.md').write_text('\n'.join(lines)+'\n');print(r['assertion_count'],r['mismatches'],r['masked_mismatches'])
