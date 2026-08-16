from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe import __version__
from juriscribe.admission import CONTRACT_VERSION,contract_digest
def fail(msg): raise SystemExit("CONTRACT CHECK FAIL: "+msg)
def main():
    contract=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8'); admission=json.loads((ROOT/'ADMISSION.json').read_text(encoding='utf-8')); manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8')); agents=(ROOT/'AGENTS.md').read_text(encoding='utf-8'); pipeline=(ROOT/'juriscribe/pipeline_v9.py').read_text(encoding='utf-8'); pipeline_facade=(ROOT/'juriscribe/pipeline.py').read_text(encoding='utf-8'); orchestrator=(ROOT/'juriscribe/orchestrator.py').read_text(encoding='utf-8'); multimode=(ROOT/'juriscribe/multimode.py').read_text(encoding='utf-8'); delivery=(ROOT/'juriscribe/delivery.py').read_text(encoding='utf-8'); session=(ROOT/'juriscribe/session.py').read_text(encoding='utf-8'); workflow=(ROOT/'.github/workflows/runtime-regression.yml').read_text(encoding='utf-8'); readme=(ROOT/'README.md').read_text(encoding='utf-8'); agent_rules=(ROOT/'docs/AGENT_RUNTIME_RULES.md').read_text(encoding='utf-8')
    if admission['contract_sha256']!=contract_digest(contract): fail('ADMISSION contract hash is stale')
    if admission['contract_version']!=CONTRACT_VERSION or manifest['contract_version']!=CONTRACT_VERSION: fail('contract version mismatch')
    if manifest['runtime_version']!=__version__: fail('runtime version mismatch')
    if manifest.get('schema')!='juriscribe-manifest/v9': fail('manifest schema is not v9')
    if not agents.startswith('# JURISCRIBE AI ADMISSION SENTINEL'): fail('AGENTS sentinel must be first')
    for path in admission['pre_admission_allowlist']:
        if path not in agents: fail(f'pre-admission allowlist missing from sentinel: {path}')
    for token in ['PROBE JURISCRIBE','INITIALIZE JURISCRIBE','CONTINUATION','GREENFIELD','REVIEW']:
        if token not in contract: fail(f'contract missing v0.9 token: {token}')
    if admission.get('mode_selection_required_for_substantive_work') is not True: fail('mode selection not mandatory')
    init_block=pipeline.split('def initialize',1)[1].split('def _ws',1)[0]
    if 'require_probe_receipt' not in init_block: fail('initialize does not require sealed probe receipt')
    if 'probe_capabilities(' in init_block or 'perform_probe(' in init_block: fail('initialize must not silently run probe')
    for token in ['select-mode','audit-text','integrity','MODE_SELECTION_REQUIRED']:
        if token not in pipeline: fail(f'pipeline missing v0.9 command/state {token}')
    for token in ['select_mode','audit_legal_text','trimode_required=True','editorial_standard_required=True','delivery_boundary_required=True']:
        if token not in orchestrator: fail(f'orchestrator missing runtime marker {token}')
    for token in ['build_mode_contract','resolve_editorial_standard','REPORT_ONLY','REPORT_AND_REVISED_TEXT']:
        if token not in multimode: fail(f'multimode runtime missing {token}')
    for token in ['DOCX_WRITE','DOCX_READBACK','session_dashboard','delivery_class','BRIEF_ARTIFACT_FIRST','build_delivery_manifest']:
        if token not in delivery: fail(f'delivery boundary missing {token}')
    if 'JURISCRIBE_VERBOSE_JSON' not in pipeline_facade: fail('pipeline facade must default to brief output with explicit machine-json opt in')
    if 'write_node_header' in session: fail('v0.9 must not generate node.h')
    for path in ['juriscribe/modes.py','juriscribe/editorial.py','juriscribe/multimode.py','juriscribe/delivery.py','juriscribe/dashboard_v9.py','schemas/mode-contract.schema.json','schemas/editorial-standard.schema.json','schemas/delivery-manifest.schema.json','docs/MODES_V9.md','docs/EDITORIAL_STANDARD_V9.md','docs/RUNTIME_V9_TRI_MODE.md','docs/FINAL_DELIVERY_V9_1.md','validation/modes-v9.json']:
        if not (ROOT/path).exists(): fail(f'missing runtime file {path}')
    delivery_manifest=manifest.get('delivery') or {}
    if delivery_manifest.get('documents_format')!='DOCX': fail('manifest must require DOCX final documents')
    if delivery_manifest.get('dashboard_required') is not True or delivery_manifest.get('dashboard_format')!='HTML': fail('manifest must require HTML dashboard')
    if delivery_manifest.get('internal_records_attached') is not False: fail('internal records must be excluded from final delivery')
    if int(delivery_manifest.get('max_final_chat_lines',99))>3: fail('final chat must remain brief')
    for required in ['python -m unittest discover -s tests -v','python scripts/check_contract.py','python scripts/simulate_v5_ci.py --cases 400000','python scripts/reflect_v5.py --target 1000','python scripts/simulate_continuation_v6.py --json-out /tmp/continuation-v6.json','python scripts/simulate_v7.py --cases 10000','python scripts/reflect_v8.py --target 100','python scripts/simulate_modes_v9.py --cases 30000']:
        if required not in workflow: fail(f'CI missing required gate: {required}')
    for required in ['CONTINUATION','GREENFIELD','REVIEW','JURISCRIBE_LEGAL_EDITORIAL_CORE_V2','REPORT_ONLY','session.integrity.json','DOCX','session-dashboard.html','FINAL_DELIVERY_V9_1']:
        if required not in readme: fail(f'README missing onboarding/delivery detail: {required}')
    for required in ['1–3 righe','DOCX','session-dashboard.html','non allegare']:
        if required not in agent_rules: fail(f'agent delivery rule missing: {required}')
    print(json.dumps({'status':'PASS','runtime_version':__version__,'contract_version':CONTRACT_VERSION,'contract_sha256':admission['contract_sha256'],'modes':manifest['modes']['canonical'],'editorial_standard':manifest['editorial']['standard_id'],'trimode_validation_cases':30000,'delivery':'DOCX+HTML dashboard, internal logs excluded'},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
