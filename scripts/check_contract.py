from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe import __version__
from juriscribe.admission import CONTRACT_VERSION,contract_digest


def fail(msg): raise SystemExit("CONTRACT CHECK FAIL: "+msg)
def main():
    contract=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8')
    admission=json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    agents=(ROOT/'AGENTS.md').read_text(encoding='utf-8')
    pipeline=(ROOT/'juriscribe/pipeline.py').read_text(encoding='utf-8')
    orchestrator=(ROOT/'juriscribe/orchestrator.py').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/runtime-regression.yml').read_text(encoding='utf-8')
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    if admission['contract_sha256']!=contract_digest(contract): fail('ADMISSION contract hash is stale')
    if admission['contract_version']!=CONTRACT_VERSION or manifest['contract_version']!=CONTRACT_VERSION: fail('contract version mismatch')
    if manifest['runtime_version']!=__version__: fail('runtime version mismatch')
    if not agents.startswith('# JURISCRIBE AI ADMISSION SENTINEL'): fail('AGENTS sentinel must be first')
    for path in admission['pre_admission_allowlist']:
        if path not in agents: fail(f'pre-admission allowlist missing from sentinel: {path}')
    for token in ['web browsing','PROBE JURISCRIBE','INITIALIZE JURISCRIBE']:
        if token not in agents and token not in contract: fail(f'bootstrap visibility token missing: {token}')
    if admission.get('user_visible_bootstrap') is not True: fail('user-visible bootstrap not mandatory')
    if admission.get('probe_receipt_required_for_initialize') is not True: fail('probe receipt not mandatory for initialize')
    init_block=pipeline.split('def initialize',1)[1].split('def _ws',1)[0]
    if 'require_probe_receipt' not in init_block: fail('initialize does not require sealed probe receipt')
    if 'probe_capabilities(' in init_block or 'perform_probe(' in init_block: fail('initialize must not silently run probe')
    if '--probe-receipt' not in pipeline: fail('initialize CLI does not expose probe receipt')
    for token in ['record-provenance','final-review','interaction-card','continuation-coverage']:
        if token not in pipeline: fail(f'pipeline missing v0.7 command {token}')
    for token in ['record_provenance','record_final_review','finalization_required=True','bootstrap_required=True']:
        if token not in orchestrator: fail(f'orchestrator missing v0.7 gate {token}')
    for path in ['juriscribe/bootstrap.py','juriscribe/interaction.py','juriscribe/provenance.py','juriscribe/final_review.py','validation/mutation-v7.json']:
        if not (ROOT/path).exists(): fail(f'missing v0.7 file {path}')
    for required in ['python -m unittest discover -s tests -v','python scripts/check_contract.py','python scripts/simulate_v5_ci.py --cases 400000','python scripts/reflect_v5.py --target 1000','python scripts/simulate_continuation_v6.py --cases 10000','python scripts/simulate_v7.py --cases 10000']:
        if required not in workflow: fail(f'CI missing required gate: {required}')
    for required in ['https://chatgpt.com/','I ACCEPT','PROBE JURISCRIBE','INITIALIZE JURISCRIBE','ALTRO','Provenance','review']:
        if required not in readme: fail(f'README onboarding/finalization detail missing: {required}')
    print(json.dumps({'status':'PASS','runtime_version':__version__,'contract_version':CONTRACT_VERSION,'contract_sha256':admission['contract_sha256'],'bootstrap_order':admission['bootstrap_order'],'mutation_v7':'10000'},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
