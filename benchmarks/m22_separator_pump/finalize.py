"""Record completed M22 gates and exact unstaged inventory; no Git mutations."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/name).read_text())
def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True)
def python_run(log):
    text=(HERE/'logs'/log).read_text()
    count,seconds=re.findall(r'Ran (\d+) tests in ([\d.]+)s',text)[-1]
    assert '\nOK\n' in text and '\nFAILED' not in text,log
    return dict(tests=int(count),seconds=float(seconds),passed=True,log='logs/'+log)

if __name__=='__main__':
    from integrity import preservation,source_verify
    from contracts import verify as contract_verify
    preservation();source_verify();contract_verify()
    full=python_run('python-full.log')
    for name in ('integration.json','historical.json'):
        assert read(name)['failed_checks']==0
    assert '280 passed' in (HERE/'logs/frontend-full.log').read_text()
    assert '42 passed' in (HERE/'logs/browser-full.log').read_text()
    assert 'Passed: 17 pages' in (HERE/'logs/smoke.log').read_text()
    verification=dict(
        baseline=dict(branch=git('branch','--show-current').strip(),head=git('rev-parse','HEAD').strip(),index=git('diff','--cached','--binary'),task_start=read('baseline.json')['task_start_status']),
        independent_integration=dict(preliminary_checks=207,complete_application_checks=221,complete_cases=2,failures=0,counts_overlap=True),
        historical=dict(cases=30,independent_checks=1680,exact_numeric_payloads=30,identity_exclusions=read('historical.json')['identity_exclusions']),
        python_full=full,python_focused=python_run('focused-final.log'),compatibility_focused=python_run('compatibility-focused.log'),
        frontend=dict(focused_tests=7,full_tests=280,full_files=28,full_runs=1),browser=dict(focused_tests=2,full_tests=42,full_runs=1),
        gates=dict(contracts='passed',types='passed in isolated copy',lint='passed',production_build='passed in isolated copy',smoke='passed: 17 pages and 17 PNG cards plus links/404/index/contact checks',format='exit 1: only pre-existing protected tsconfig.json',diff_check='passed'),
        intermediate_results=[
            dict(command='unittest test_m22_separator_pump -v',tests=9,failures=1,reason='Inherited composition mutation set 0.5, unchanged for below source; changed new test to a genuine 0.4 mutation; historical helper unchanged.',log='logs/focused-initial.log'),
            dict(command='vitest run tests/m22-separator-pump.test.tsx',exit_code=1,reason='No tests discovered: repository includes .test.ts only. Renamed test and used createElement.',log='logs/frontend-focused.log'),
        ],
        counting='Focused, full and separate artifact runs overlap; counts are not summed as unique tests. One ordinary full Python run; no exclusions. No repeated full M21 numerical qualification.',
        commands=[
            'PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/verify.py --preliminary --output benchmarks/m22_separator_pump/preliminary.json',
            'PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/verify.py --output benchmarks/m22_separator_pump/integration.json',
            'PYTHONPATH=engine engine/.venv/bin/python -B benchmarks/m22_separator_pump/historical.py --output benchmarks/m22_separator_pump/historical.json',
            'PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_m22_separator_pump -v',
            'PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest test_separator_pump_integration test_variable_pump_evidence test_pt200_profile test_m21_review -v',
            'PYTHONPATH=engine:engine/tests engine/.venv/bin/python -B -m unittest discover -s engine/tests -v',
            'npm run contracts:check','npm test','npm run lint','npm run format:check','git diff --check',
            'isolated copy: npm run typecheck',
            'isolated copy: npx playwright test tests/e2e/m22-separator-pump.spec.ts',
            'isolated copy: npx playwright test',
            'isolated copy: RIOGINEER_E2E_DIST_DIR=.next/m22-build NEXT_TELEMETRY_DISABLED=1 npm run build',
            'isolated copy: SITE_URL=http://127.0.0.1:3123 RIOGINEER_LLM_PROVIDER=\'\' RIOGINEER_E2E_DIST_DIR=.next/m22-build NEXT_TELEMETRY_DISABLED=1 npm run start -- --port 3123',
            'isolated copy: SMOKE_URL=http://127.0.0.1:3123 npm run smoke',
            'engine/.venv/bin/python -B benchmarks/m22_separator_pump/contracts.py',
            'engine/.venv/bin/python -B benchmarks/m22_separator_pump/integrity.py',
        ],
        cli=dict(below_exit=0,above_exit=0,unsupported_efficiency_081_exit=1),
        service_availability=dict(ports=[3122,8122,3123],listeners=subprocess.run(['lsof','-nP','-iTCP:3122','-iTCP:8122','-iTCP:3123','-sTCP:LISTEN'],capture_output=True,text=True).stdout,task_services_stopped=True),
        unchanged_shared_physics=True,automatic_fallback=False,observed_m21_peak_iterations=199,
        configuration_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('next-env.d.ts','tsconfig.json')},
        human_acceptance=False,commit=False,push=False,deployment=False,user_service_shutdown=False,
        limitations=['Finite two-case addition; no continuous envelope/interpolation/flow or efficiency scaling.','No hydraulic/NPSH/cavitation qualification.','Historical missing next-env snapshot remains unavailable; task-start bytes preserved.','Pre-existing tsconfig formatting remains unchanged.'],
    )
    write('verification.json',verification)
    # Reserve final metadata paths before enumerating the exact owned inventory.
    for name in ('inventory.json','manifest.json','final_status.txt'):
        p=HERE/name
        if not p.exists():p.write_text('{}\n' if name.endswith('.json') else '')
    paths=set(git('diff','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    excluded=['next-env.d.ts','tsconfig.json']
    owned=sorted(paths-set(excluded))
    write('inventory.json',dict(task_paths=owned,task_path_count=len(owned),preserved_unrelated_paths=excluded))
    block='\n## Exact M22 file inventory\n\n'+f'{len(owned)} task-owned paths; all unstaged. The two pre-existing configuration edits\nare excluded and byte-preserved.\n\n'+''.join('- `'+n+'`\n' for n in owned)
    for name in ('MILESTONE_22.md','docs/RIOGINEER_MASTER_CONTEXT.md'):
        p=ROOT/name;s=p.read_text();marker='\n## Exact M22 file inventory\n'
        if marker in s:s=s[:s.index(marker)]
        p.write_text(s.rstrip()+'\n'+block)
    status=git('status','--short')
    (HERE/'final_status.txt').write_text(status)
    write('manifest.json',dict(files={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in owned if n!='benchmarks/m22_separator_pump/manifest.json'},excluded_self='benchmarks/m22_separator_pump/manifest.json'))
    print(json.dumps(dict(python_full=full,task_paths=len(owned),index_empty=not git('diff','--cached','--binary')),indent=2))
