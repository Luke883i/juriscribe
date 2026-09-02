from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fail(m): raise SystemExit('PROJECT STATUS CHECK FAIL: '+m)
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def main():
    status=json.loads(read('PROJECT_STATUS.json'))
    admission=json.loads(read('ADMISSION.json'))
    manifest=json.loads(read('MANIFEST.json'))
    runtime=json.loads(read('RUNTIME_V1_CONTRACT.json'))
    contract=read('ISENECA_ACCESS_CONTRACT.md')
    packaged=read('juriscribe/resources/ISENECA_ACCESS_CONTRACT.md')
    readme=read('README.md'); agents=read('AGENTS.md'); responsible=read('RESPONSIBLE_USE.md'); project_doc=read('docs/PROJECT_STATUS.md'); license_text=read('LICENSE'); pyproject=read('pyproject.toml')
    required={'license_spdx':'Apache-2.0','experimental':True,'ai_errors_possible':True,'human_validation_required':True,'human_final_responsibility':True,'professional_advice':False,'substantive_truth_claim':False,'pass_implies_truth':False,'responsible_use_is_license_restriction':False,'status_adds_runtime_authority':False,'authority_partition_nodes':6}
    for k,v in required.items():
        if status.get(k)!=v: fail('canonical status mismatch: '+k)
        if k in (admission.get('project_status') or {}) and admission['project_status'].get(k)!=v: fail('admission status drift: '+k)
    if status.get('profile')!='JURISCRIBE_PROJECT_STATUS_V1' or admission.get('project_status',{}).get('profile')!='JURISCRIBE_PROJECT_STATUS_V1': fail('profile drift')
    nodes=['MODE_REGISTRY','EXPLICIT_ROUTER','COMMON_STALENESS','SPECIALIST_PROOF','MATERIALIZATION','PROJECTION']
    if status.get('authority_nodes')!=nodes or runtime.get('authority_nodes')!=nodes: fail('authority topology drift')
    if runtime.get('project_status_is_authority') is not False: fail('project status escalated to authority')
    if manifest.get('contract_version')!='2.2.0' or admission.get('contract_version')!='2.2.0' or runtime.get('contract_version')!='2.2.0': fail('contract version drift')
    if 'contract_version: 2.2.0' not in contract or packaged!=contract: fail('contract/bundle drift')
    digest=hashlib.sha256(contract.replace('\r\n','\n').encode()).hexdigest()
    if admission.get('contract_sha256')!=digest: fail('admission contract hash stale')
    for token in ['Apache License','Version 2.0','Disclaimer of Warranty','Limitation of Liability']:
        if token not in license_text: fail('license text incomplete: '+token)
    if 'license = {file = "LICENSE"}' not in pyproject: fail('package license metadata missing')
    joined='\n'.join([readme,agents,responsible,project_doc,contract]).lower()
    concepts={'experimental':['experimental','sperimentale'],'ai fallibility':['ai-assisted outputs can be wrong','fallibilità','allucinazioni'],'human validation':['human validation','validazione umana','validato da un umano','validated by a competent human'],'human responsibility':['responsibility','responsabilità']}
    for label,alts in concepts.items():
        if not any(a.lower() in joined for a in alts): fail('missing concept: '+label)
    for token in ["## 21. Natura sperimentale e fallibilità dell'AI",'## 22. Validazione umana e responsabilità finale','## 23. Licenza open-source e responsible use']:
        if token not in contract: fail('contract responsible-use section missing: '+token)
    print(json.dumps({'status':'PASS','profile':status['profile'],'contract_version':'2.2.0','authority_nodes':6,'license':'Apache-2.0'},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
