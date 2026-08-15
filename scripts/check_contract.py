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
    workflow=(ROOT/'.github/workflows/runtime-regression.yml').read_text(encoding='utf-8')
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    stable_sim=(ROOT/'scripts/simulate_v5_ci.py').read_text(encoding='utf-8')
    if admission['contract_sha256']!=contract_digest(contract): fail('ADMISSION contract hash is stale')
    if admission['contract_version']!=CONTRACT_VERSION or manifest['contract_version']!=CONTRACT_VERSION: fail('contract version mismatch')
    if manifest['runtime_version']!=__version__: fail('runtime version mismatch')
    if not agents.startswith('# JURISCRIBE AI ADMISSION SENTINEL'): fail('AGENTS sentinel must be first')
    for path in admission['pre_admission_allowlist']:
        if path not in agents: fail(f'pre-admission allowlist missing from sentinel: {path}')
    if 'issue_receipt(' not in pipeline or 'args.command == "accept"' not in pipeline: fail('explicit accept command missing')
    init_block=pipeline.split('def initialize',1)[1].split('def _ws',1)[0]
    if 'require_receipt' not in init_block: fail('initialize does not require admission receipt')
    if 'issue_receipt' in init_block: fail('initialize must never auto-issue acceptance')
    for token in ['review-cycle','record-regeneration','review-saturation','record-simulation','record-compression','node-header']:
        if token not in pipeline: fail(f'pipeline missing v0.5 command {token}')
    if 'SELECTOR_VERSION = "sha256-stable-random-v1"' not in stable_sim or 'hashlib.sha256' not in stable_sim:
        fail('stable cross-version simulation selector missing')
    for required in ['python -m unittest discover -s tests -v','python scripts/check_contract.py','python scripts/simulate_v5_ci.py --cases 400000','python scripts/reflect_v5.py --target 1000']:
        if required not in workflow: fail(f'CI missing required gate: {required}')
    for required in ['https://chatgpt.com/','Inizializza Juriscribe','400.000','P+10.000','node.h']:
        if required not in readme: fail(f'README onboarding/contract detail missing: {required}')
    print(json.dumps({'status':'PASS','runtime_version':__version__,'contract_version':CONTRACT_VERSION,'contract_sha256':admission['contract_sha256'],'pre_admission_allowlist':admission['pre_admission_allowlist'],'simulation_selector':'sha256-stable-random-v1'},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
