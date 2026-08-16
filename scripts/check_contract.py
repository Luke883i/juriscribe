from __future__ import annotations
import json, re, sys
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
    pipeline=(ROOT/'juriscribe/pipeline_v9.py').read_text(encoding='utf-8')
    pipeline_facade=(ROOT/'juriscribe/pipeline.py').read_text(encoding='utf-8')
    bootstrap=(ROOT/'juriscribe/bootstrap.py').read_text(encoding='utf-8')
    admission_runtime=(ROOT/'juriscribe/admission.py').read_text(encoding='utf-8')
    orchestrator=(ROOT/'juriscribe/orchestrator.py').read_text(encoding='utf-8')
    multimode=(ROOT/'juriscribe/multimode.py').read_text(encoding='utf-8')
    delivery=(ROOT/'juriscribe/delivery.py').read_text(encoding='utf-8')
    dashboard=(ROOT/'juriscribe/dashboard_v9.py').read_text(encoding='utf-8')
    session=(ROOT/'juriscribe/session.py').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/runtime-regression.yml').read_text(encoding='utf-8')
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    agent_rules=(ROOT/'docs/AGENT_RUNTIME_RULES.md').read_text(encoding='utf-8')
    hardening=(ROOT/'docs/RUNTIME_HARDENING_V9_3.md').read_text(encoding='utf-8')

    if admission['contract_sha256']!=contract_digest(contract): fail('ADMISSION contract hash is stale')
    if admission['contract_version']!=CONTRACT_VERSION or manifest['contract_version']!=CONTRACT_VERSION: fail('contract version mismatch')
    if manifest['runtime_version']!=__version__: fail('runtime version mismatch')
    if manifest.get('schema')!='juriscribe-manifest/v9': fail('manifest schema is not v9')
    if not agents.startswith('# JURISCRIBE AI ADMISSION SENTINEL'): fail('AGENTS sentinel must be first')
    for path in admission['pre_admission_allowlist']:
        if path not in agents: fail(f'pre-admission allowlist missing from sentinel: {path}')

    governance_tokens=['PROBE JURISCRIBE','INITIALIZE JURISCRIBE','CONTINUATION','GREENFIELD','REVIEW','DOCX_WRITE','DOCX_READBACK','1–3 righe','stack trace','decisione umana','session-dashboard.html']
    for token in governance_tokens:
        if token not in contract: fail(f'contract missing v0.9 governance token: {token}')
    historical_detail_tokens=[
        'CONTINUATION FRONTIER','ATOMIC CONCEPT DECOMPOSITION + RETICULUM','DIAGNOSTIC SATURATION',
        'SCIENTIFIC / CONTENT / SOURCE / LOGICAL / EDITORIAL REVIEW','contributo/obiettivo del documento',
        'preservazione epistemica/voce autoriale','I criteri non applicabili devono essere marcati e motivati',
        'simulazioni multi-classe','compressione lossless','assenza di nuovi finding materiali',
        "La sequenza futura dell'autore non è un completion target",
    ]
    for token in historical_detail_tokens:
        if token not in contract: fail(f'contract lost historical scientific/editorial detail: {token}')
    for section in range(1,20):
        if f'## {section}.' not in contract: fail(f'contract historical section {section} missing')

    for flag in ['artifact_first_surface_required','autonomous_until_blocking_human_decision','materialized_delivery_required','dashboard_state_binding_required','probe_receipt_single_use','receipt_nonces_required','sealed_capabilities_immutable','workspace_overwrite_forbidden','non_deterministic_session_ids','atomic_session_persistence','artifact_workspace_confinement','technical_output_dual_opt_in']:
        if admission.get(flag) is not True: fail(f'admission missing hardening flag: {flag}')
    if int(admission.get('post_bootstrap_chat_max_lines',99))>3: fail('post-bootstrap chat surface is too verbose')
    if admission.get('mode_selection_required_for_substantive_work') is not True: fail('mode selection not mandatory')
    if admission.get('bootstrap_order')[-2:] != ['MODE_SELECTION_REQUIRED','ACTIVE_WORK']: fail('bootstrap order split-brain detected')

    for token in ['new_session_id','uuid.uuid4','assert_initializable','_atomic_text_write','os.replace','session integrity validation failed']:
        if token not in session: fail(f'session hardening missing {token}')
    for token in ['receipt_nonce','_receipt_id','receipt id/digest mismatch']:
        if token not in admission_runtime: fail(f'admission receipt hardening missing {token}')
    for token in ['juriscribe-bootstrap/v2','juriscribe-probe-receipt/v2','probe_nonce','claim_probe_receipt','os.O_EXCL','MODE_SELECTION_REQUIRED','ACTIVE_WORK']:
        if token not in bootstrap: fail(f'bootstrap hardening missing {token}')

    init_block=pipeline.split('def initialize',1)[1].split('def bootstrap_after_acceptance',1)[0]
    if 'require_probe_receipt' not in init_block: fail('initialize does not require sealed probe receipt')
    if 'probe_capabilities(' in init_block or 'perform_probe(' in init_block: fail('initialize must not silently run probe')
    for token in ['new_session_id','claim_probe_receipt','was not present in sealed probe receipt','workspace_base','persist=False','persist_session','bootstrap_after_acceptance','MODE_SELECTION_REQUIRED','activate_work']:
        if token not in pipeline: fail(f'pipeline bootstrap/persistence hardening missing {token}')
    for token in ['select-mode','audit-text','integrity']:
        if token not in pipeline: fail(f'pipeline missing v0.9 command/state {token}')
    for token in ['select_mode','audit_legal_text','trimode_required=True','editorial_standard_required=True','delivery_boundary_required=True','materialized_delivery_required=True','dashboard_state_binding_required=True']:
        if token not in orchestrator: fail(f'orchestrator missing runtime marker {token}')
    for token in ['build_mode_contract','resolve_editorial_standard','REPORT_ONLY','REPORT_AND_REVISED_TEXT']:
        if token not in multimode: fail(f'multimode runtime missing {token}')

    for token in ['DOCX_WRITE','DOCX_READBACK','session_dashboard','delivery_class','build_delivery_manifest','verify_materialized_artifact','zipfile.is_zipfile','word/document.xml','dashboard_state_digest','sha256','juriscribe-final-delivery/v3','workspace_base','artifact path escapes','symlink','MAX_DOCX_UNCOMPRESSED_BYTES','MAX_COMPRESSION_RATIO','word/vbaProject.bin']:
        if token not in delivery: fail(f'delivery boundary missing {token}')
    for token in ['juriscribe-state-digest','dashboard_state_digest','visible_artifacts']:
        if token not in dashboard: fail(f'dashboard freshness/user-facing filter missing {token}')
    for token in ['phase','interaction','completion','node_integrity','runtime']:
        if token not in delivery: fail(f'dashboard control binding missing {token}')
    for token in ['JURISCRIBE_VERBOSE_JSON','--technical-output','redirect_stderr','_record_hidden_failure','MAX_PUBLIC_SUMMARY_CHARS','Operazione non completata. Consulta la dashboard.','Errore tecnico interno']:
        if token not in pipeline_facade: fail(f'artifact-first pipeline facade missing {token}')
    if 'and TECHNICAL_FLAG in _argv(argv)' not in pipeline_facade: fail('machine JSON is not dual opt-in')
    if 'write_node_header' in session: fail('v0.9 must not generate node.h')

    for path in ['juriscribe/modes.py','juriscribe/editorial.py','juriscribe/multimode.py','juriscribe/delivery.py','juriscribe/dashboard_v9.py','schemas/mode-contract.schema.json','schemas/editorial-standard.schema.json','schemas/delivery-manifest.schema.json','schemas/admission-receipt.schema.json','schemas/bootstrap.schema.json','schemas/probe-receipt.schema.json','docs/MODES_V9.md','docs/EDITORIAL_STANDARD_V9.md','docs/RUNTIME_V9_TRI_MODE.md','docs/FINAL_DELIVERY_V9_2.md','docs/HISTORIOGRAPHIC_AUDIT_V9_2.md','docs/RUNTIME_HARDENING_V9_3.md','tests/test_runtime_hardening_v9_3.py','validation/modes-v9.json']:
        if not (ROOT/path).exists(): fail(f'missing runtime file {path}')

    delivery_manifest=manifest.get('delivery') or {}
    if delivery_manifest.get('documents_format')!='DOCX': fail('manifest must require DOCX final documents')
    if delivery_manifest.get('dashboard_required') is not True or delivery_manifest.get('dashboard_format')!='HTML': fail('manifest must require HTML dashboard')
    if delivery_manifest.get('dashboard_state_binding') is not True: fail('manifest must require dashboard state binding')
    if delivery_manifest.get('artifact_workspace_confinement') is not True: fail('manifest must confine final artifacts to workspace')
    if delivery_manifest.get('docx_resource_limits') is not True: fail('manifest must require bounded DOCX readback')
    if delivery_manifest.get('internal_records_attached') is not False: fail('internal records must be excluded from final delivery')
    if delivery_manifest.get('surface_scope')!='all-post-bootstrap': fail('artifact-first policy must cover all post-bootstrap interaction')
    if delivery_manifest.get('autonomous_default') is not True: fail('post-bootstrap agent must default to autonomous execution')
    if delivery_manifest.get('human_interruptions')!='blocking-noninferable-only': fail('human interruptions must be blocker/non-inferable only')
    if delivery_manifest.get('exception_output')!='redacted-to-dashboard': fail('exception details must remain internal/dashboard-bound')
    if delivery_manifest.get('materialization_validation')!='filesystem+workspace-confinement+OOXML+bounded-readback+sha256': fail('delivery materialization verification is incomplete')
    if int(delivery_manifest.get('max_post_bootstrap_chat_lines',99))>3: fail('post-bootstrap chat must remain brief')
    bootstrap_manifest=manifest.get('bootstrap_hardening') or {}
    for key in ['fast_path_preserves_distinct_probe_and_initialize_receipts','mode_selection_stays_explicit','receipt_nonces','probe_receipt_single_use','sealed_capabilities_immutable','workspace_overwrite']:
        if key not in bootstrap_manifest: fail(f'manifest bootstrap hardening missing {key}')

    checkout_sha='11d5960a326750d5838078e36cf38b85af677262'
    setup_sha='a26af69be951a213d495a4c3e4e4022e16d87065'
    if f'actions/checkout@{checkout_sha}' not in workflow or f'actions/setup-python@{setup_sha}' not in workflow: fail('GitHub Actions are not pinned to audited commit SHAs')
    if re.search(r'uses:\s+actions/(checkout|setup-python)@v\d', workflow): fail('movable GitHub Actions major tag remains')
    if 'governance-main-provenance' not in workflow or '/commits/{os.environ[\'SHA\']}/pulls' not in workflow: fail('main direct-push provenance guard missing')

    for required in ['python -m unittest discover -s tests -v','python scripts/check_contract.py','python scripts/simulate_v5_ci.py --cases 400000','python scripts/reflect_v5.py --target 1000','python scripts/simulate_continuation_v6.py --json-out /tmp/continuation-v6.json','python scripts/simulate_v7.py --cases 10000','python scripts/reflect_v8.py --target 100','python scripts/simulate_modes_v9.py --cases 30000']:
        if required not in workflow: fail(f'CI missing required gate: {required}')
    for required in ['CONTINUATION','GREENFIELD','REVIEW','JURISCRIBE_LEGAL_EDITORIAL_CORE_V2','REPORT_ONLY','session.integrity.json','DOCX','session-dashboard.html','FINAL_DELIVERY_V9_2','attendi gli artefatti finali','NON narrare']:
        if required not in readme: fail(f'README missing onboarding/delivery detail: {required}')
    for required in ['1–3 righe','DOCX','session-dashboard.html','non allegare','non narrare','decisione umana','stack trace','dashboard stale','bootstrap-after-acceptance','single-use','--technical-output']:
        if required not in agent_rules: fail(f'agent surface/hardening rule missing: {required}')
    for required in ['P0','P1','P2','fast bootstrap','branch protection','non può']:
        if required.lower() not in hardening.lower(): fail(f'hardening dossier missing {required}')

    print(json.dumps({'status':'PASS','runtime_version':__version__,'contract_version':CONTRACT_VERSION,'contract_sha256':admission['contract_sha256'],'modes':manifest['modes']['canonical'],'editorial_standard':manifest['editorial']['standard_id'],'trimode_validation_cases':30000,'delivery':'workspace-confined bounded DOCX + control-bound HTML dashboard','bootstrap':'nonce + single-use probe + no-overwrite + safe fast path','historical_contract_sections_preserved':19,'actions_pinned':True},indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
