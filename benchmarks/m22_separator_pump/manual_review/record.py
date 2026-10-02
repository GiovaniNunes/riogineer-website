"""Additive manual-review inventory and preservation; no historical artifact rewrite."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
EDITED={'src/app/digital-engineer/workspace.tsx','src/app/digital-engineer/separator-pump-results.tsx','tests/m22-separator-pump.test.ts','tests/e2e/m22-separator-pump.spec.ts','MILESTONE_22.md','docs/RIOGINEER_MASTER_CONTEXT.md'}
NEW={'src/lib/digital-engineer/number-format.ts','tests/m22-manual-review.test.ts'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True)
if __name__=='__main__':
    base=json.loads((HERE/'baseline.json').read_text())
    assert git('rev-parse','HEAD').strip()==base['head']
    assert git('branch','--show-current').strip()=='main'
    assert git('diff','--cached','--binary')==''
    for name,expected in base['files'].items():
        raw=(ROOT/name).read_bytes()
        if name in ('MILESTONE_22.md','docs/RIOGINEER_MASTER_CONTEXT.md'):
            raw=raw.split(b'\n## M22 manual review and targeted presentation corrections')[0]
        elif name in EDITED:continue
        assert sha(raw)==expected,name+' changed outside targeted corrections'
    for name in ('next-env.d.ts','tsconfig.json'):
        assert (ROOT/name).read_bytes()==(HERE/('preserved-'+name+'.txt')).read_bytes()
    source_manifest=json.loads((HERE.parent/'source_manifest.json').read_text())
    for name,h in source_manifest['files'].items():assert sha((ROOT/name).read_bytes())==h,name
    assert '13 passed' in (HERE/'frontend-final.log').read_text()
    assert '2 passed' in (HERE/'browser.log').read_text()
    assert not (HERE/'types.log').read_text().strip()
    assert not (HERE/'lint.log').read_text().strip()
    assert not (HERE/'diff-check.log').read_text().strip()
    assert 'All matched files' in (HERE/'format.log').read_text()
    comparison=json.loads((HERE/'numerical-comparison.json').read_text());assert comparison['result_payload_equality']
    synced=sorted((EDITED|NEW)-{'MILESTONE_22.md','docs/RIOGINEER_MASTER_CONTEXT.md'})
    for name in synced:assert (ROOT/name).read_bytes()==(ROOT/'.local/m22-validation'/name).read_bytes(),name+' validation copy differs'
    save('verification.json',dict(date='2026-10-02',timezone='America/Sao_Paulo',head=base['head'],branch='main',index_empty=True,
        fresh_case_reproduction=comparison,frontend=dict(final=13,files=3,initial_passed=11,initial_failed=2,correction='Scope limitation-text assertion to visible section; raw JSON is intentionally unchanged.'),browser=dict(passed=2,services='Existing ports 3122/8122; webServer disabled; no starts/stops'),
        gates=dict(types='passed: tsc --noEmit',lint='passed: affected paths',format='passed: affected paths',diff='passed'),
        prior_full_suites_not_rerun=dict(python=693,frontend=280,browser=42),
        preserved=dict(all_prior_evidence=True,all_backend_and_schema_source=True,docs_prefixes=True,configuration_bytes=True,configuration_sha256={n:base['files'][n] for n in ['next-env.d.ts','tsconfig.json']}),
        validation_copy_synced=synced,backend_restart_required=False,refresh_sufficient=True,
        acceptance='correction review pending',commit=False,push=False,deploy=False,service_shutdown=False))
    for name in ('inventory.json','manifest.json','final_status.txt'):
        if not (HERE/name).exists():(HERE/name).write_text('{}\n' if name.endswith('.json') else '')
    previous=json.loads((HERE.parent/'inventory.json').read_text())['task_paths']
    review_files=sorted(str(p.relative_to(ROOT)) for p in HERE.rglob('*') if p.is_file())
    delta=sorted(EDITED|NEW|set(review_files));combined=sorted(set(previous)|set(delta))
    save('inventory.json',dict(correction_paths=delta,correction_path_count=len(delta),application_test_document_delta=sorted(EDITED|NEW),combined_m22_paths=combined,combined_count=len(combined),preserved_unrelated=['next-env.d.ts','tsconfig.json'],prior_inventory_preserved='benchmarks/m22_separator_pump/inventory.json'))
    (HERE/'final_status.txt').write_text(git('status','--short'))
    save('manifest.json',dict(files={n:sha((ROOT/n).read_bytes()) for n in combined if n!='benchmarks/m22_separator_pump/manual_review/manifest.json'},excluded_self='benchmarks/m22_separator_pump/manual_review/manifest.json',prior_manifest_preserved='benchmarks/m22_separator_pump/manifest.json'))
    print(json.dumps(dict(correction_paths=len(delta),combined_m22_paths=len(combined),preservation='passed',synced=synced),indent=2))
