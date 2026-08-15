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
    continuation=(ROOT/'juriscribe/continuation.py').read_text(encoding='utf-8')
    node=(ROOT/'juriscribe/node_header.py').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/runtime-regression.yml').read_text(encoding='utf-8')
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    stable_sim=(ROOT/'scripts/simulate_v5_ci.py').read_text(encoding='utf-8')
    if admission['contract_sha256']!=contract_digest(contract): fail('ADMISSION contract hash is stale')
    if admission['contract_version']!=CONTRACT_VERSION or manifest['contract_version']!=CONTRACT_VERSION: fail('contract version mismatch')
    if manifest['runtime_version']!=__version__: fail('runtime version mismatch')
    if manifest['schema']!='juriscribe-manifest/v6': fail('manifest schema is not v6')
    if not agents.startswith('# JURISCRIBE AI ADMISSION SENTINEL'): fail('AGENTS sentinel must be first')
    for path in admission['pre_admission_allowlist']:
        if path not in agents: fail(f'pre-admission allowlist missing from sentinel: {path}')
    if 'issue_receipt(' not in pipeline or 'args.command == "accept"' not in pipeline: fail('explicit accept command missing')
    init_block=pipeline.split('def initialize',1)[1].split('def _ws',1)[0]
    if 'require_receipt' not in init_block: fail('initialize does not require admission receipt')
    if 'issue_receipt' in init_block: fail('initialize must never auto-issue acceptance')
    for token in ['review-cycle','record-regeneration','review-saturation','record-simulation','record-compression','node-header','continuation-plan','continuation-coverage']:
        if token not in pipeline: fail(f'pipeline missing runtime command {token}')
    for token in ['derive_continuation_plan','record_continuation_coverage','continuation_required=True']:
        if token not in orchestrator: fail(f'orchestrator missing v0.6 enforcement: {token}')
    for token in ['sequence_is_binding','minimum_coverage_score','introduced_material_bindings','sequence_scoring']:
        if token not in continuation: fail(f'continuation hardening invariant missing: {token}')
    if 'NODE_H_VERSION = "3"' not in node or 'JURISCRIBE_CONTINUATION_SHA256' not in node:
        fail('node.h v3 continuation binding missing')
    if 'SELECTOR_VERSION = "sha256-stable-roundrobin-v2"' not in stable_sim or 'hashlib.sha256' not in stable_sim:
        fail('stable cross-version simulation selector missing')
    for required in [
        'python -m unittest discover -s tests -v',
        'python scripts/check_contract.py',
        'python scripts/simulate_v5_ci.py --cases 400000',
        'python scripts/reflect_v5.py --target 1000',
        'python scripts/simulate_continuation_v6.py --json-out /tmp/continuation-v6.json',
        'validation/continuation-v6.json /tmp/continuation-v6.json',
    ]:
        if required not in workflow: fail(f'CI missing required gate: {required}')
    for required in ['https://chatgpt.com/','Inizializza Juriscribe','400.000','10.000 scenari unici','P+10.000','node.h','development frontier']:
        if required not in readme: fail(f'README onboarding/contract detail missing: {required}')
    print(json.dumps({
        'status':'PASS',
        'runtime_version':__version__,
        'contract_version':CONTRACT_VERSION,
        'contract_sha256':admission['contract_sha256'],
        'pre_admission_allowlist':admission['pre_admission_allowlist'],
        'simulation_selector':'sha256-stable-roundrobin-v2',
        'continuation_unique_scenarios':10000,
        'node_h_version':3,
    },indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
