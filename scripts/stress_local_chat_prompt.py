from __future__ import annotations
import hashlib, json, random, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROMPT=ROOT/'docs/host/LOCAL_HOST_PROMPT.md'
SEED=20260904114235
CASES=100_000

REQUIRED=(
 'STANDALONE','HOST_ORCHESTRATION_AND_PROJECTION_ONLY','resolved_revision','contract_sha256',
 'ASSUME_UNAVAILABLE','DO_NOT_PROBE','DO_NOT_ATTEMPT','PRIMARY_TRANSPORT := connected GitHub',
 'Resolve canonical main ONCE','pre_admission_allowlist','exact `I ACCEPT`','mandatory LOCAL_CHAT execution-profile choice',
 'LEAN = full Juriscribe method + identical epistemic duties','ATTESTED = same method + same epistemic duties',
 'Do not auto-select','METHOD_ACCESS','METHOD_KERNEL.json','Skip runtime bootstrap entirely',
 'METHOD_MODE_INTENT','H0_HANDSHAKE_CLOSURE','Git blob SHA','blob <len>\\0<bytes>',
 'REAL AdmissionReceipt','REAL ProbeReceipt','H1 activation closure','retry once ONLY',
 'do not roam into Git/DNS/install/public-HTTP alternatives','LEAN -> ATTESTED always requires canonical replay/revalidation',
 'Execution-attestation degradation NEVER degrades artifact obligations','MATERIALIZE -> READBACK',
 '`MATERIALIZATION_PENDING`','Chat prose, Markdown/TXT/JSON/PDF','Physical readiness != execution attestation',
 'Human validation and final responsibility remain mandatory'
)
FORBIDDEN=(
 'RUNTIME_LOCAL_HOST.md', 'auto-select ATTESTED', 'auto-select LEAN', 'receipt simulation allowed',
 'git clone is allowed', 'DNS fallback allowed', 'chat text substitutes artifact', 'LEAN may claim COMPLETE'
)

def validate(text:str)->list[str]:
    e=[]
    if len(text)>8000: e.append('OVER_8000')
    for tok in REQUIRED:
        if tok not in text: e.append('MISSING:'+tok)
    for tok in FORBIDDEN:
        if tok in text: e.append('FORBIDDEN:'+tok)
    order=['BOOT(session_start)','ON `I ACCEPT`','ON LEAN','ON ATTESTED','ACTIVE(profile)','ARTIFACT INVARIANT','FAIL-CLOSED']
    pos=[text.find(x) for x in order]
    if any(x<0 for x in pos) or pos!=sorted(pos): e.append('FLOW_ORDER')
    if 'CONTINUATION' in text or 'GREENFIELD' in text or 'COMPRESSION & CONSOLIDATION' in text: e.append('DUPLICATE_MODE_TAXONOMY')
    if not re.search(r'ASSUME_UNAVAILABLE := \{preinstalled Juriscribe runtime, local Git checkout/package\}',text): e.append('COLD_PRIOR')
    if 'same method + same epistemic duties' not in text or 'identical epistemic duties' not in text: e.append('PROFILE_EPISTEMIC_PARITY')
    if 'RULE := canonical runtime state > host memory. Never silently rebind pinned revision to newer main.' not in text: e.append('NO_LIVE_REBIND')
    if 'DO_NOT_PROBE := {RUNTIME_IMPORT, LOCAL_CHECKOUT}.' not in text: e.append('NO_RUNTIME_PROBE')
    if 'acceptance_evidence := exact human message + resolved_revision + contract_sha256' not in text: e.append('ACCEPTANCE_BINDING')
    if 'fetch ADMISSION.json method_access + exact METHOD_KERNEL.json; verify kernel SHA256' not in text: e.append('METHOD_KERNEL_BINDING')
    if 'obtain expected Git blob SHA from pinned tree; fetch bytes; compute Git blob SHA1' not in text: e.append('GIT_BLOB_BINDING')
    if 'Required user-facing artifact set/format is determined by canonical scientific mode, not LEAN/ATTESTED' not in text: e.append('ARTIFACT_PROFILE_ORTHOGONALITY')
    return e

MUTATIONS=(
 ('drop_accept', lambda s:s.replace('exact `I ACCEPT`','`I ACCEPT`',1)),
 ('auto_attested', lambda s:s.replace('Do not auto-select.','auto-select ATTESTED.',1)),
 ('drop_profile_choice', lambda s:s.replace('mandatory LOCAL_CHAT execution-profile choice','LOCAL_CHAT execution-profile choice',1)),
 ('lean_weaken_method', lambda s:s.replace('LEAN = full Juriscribe method + identical epistemic duties','LEAN = reduced method',1)),
 ('attested_extra_epistemic', lambda s:s.replace('ATTESTED = same method + same epistemic duties','ATTESTED = stronger epistemic truth',1)),
 ('drop_pin_once', lambda s:s.replace('Resolve canonical main ONCE','Resolve canonical main',1)),
 ('allow_rebind', lambda s:s.replace('Never silently rebind pinned revision to newer main.','Silently rebind to newer main when convenient.',1)),
 ('allow_git', lambda s:s+'\ngit clone is allowed\n'),
 ('allow_dns', lambda s:s+'\nDNS fallback allowed\n'),
 ('drop_primary_transport', lambda s:s.replace('PRIMARY_TRANSPORT := connected GitHub','PRIMARY_TRANSPORT := generic network',1)),
 ('probe_runtime', lambda s:s.replace('DO_NOT_PROBE := {RUNTIME_IMPORT, LOCAL_CHECKOUT}.','DO_NOT_PROBE := {}.',1)),
 ('drop_method_kernel', lambda s:s.replace('METHOD_KERNEL.json','METHOD.json',1)),
 ('lean_bootstrap', lambda s:s.replace('Skip runtime bootstrap entirely','Search runtime before LEAN',1)),
 ('lean_fake_mode', lambda s:s.replace('METHOD_MODE_INTENT','MODE_SELECTED',1)),
 ('drop_h0', lambda s:s.replace('H0_HANDSHAKE_CLOSURE','HANDSHAKE',1)),
 ('drop_blob_sha', lambda s:s.replace('Git blob SHA','source checksum',1)),
 ('drop_git_object_formula', lambda s:s.replace('blob <len>\\0<bytes>','bytes',1)),
 ('fake_admission', lambda s:s.replace('REAL AdmissionReceipt','synthetic AdmissionReceipt',1)),
 ('fake_probe', lambda s:s.replace('REAL ProbeReceipt','synthetic ProbeReceipt',1)),
 ('drop_h1', lambda s:s.replace('H1 activation closure','activation files',1)),
 ('unbounded_retry', lambda s:s.replace('retry once ONLY','retry until success',1)),
 ('roam_fallbacks', lambda s:s.replace('do not roam into Git/DNS/install/public-HTTP alternatives','try Git/DNS/install/public-HTTP alternatives',1)),
 ('retro_promote', lambda s:s.replace('LEAN -> ATTESTED always requires canonical replay/revalidation','LEAN -> ATTESTED may relabel prior work',1)),
 ('degrade_artifacts', lambda s:s.replace('Execution-attestation degradation NEVER degrades artifact obligations','Execution-attestation degradation may degrade artifact obligations',1)),
 ('drop_readback', lambda s:s.replace('MATERIALIZE -> READBACK','MATERIALIZE',1)),
 ('drop_pending', lambda s:s.replace('`MATERIALIZATION_PENDING`','`PENDING`',1)),
 ('chat_substitute', lambda s:s+'\nchat text substitutes artifact\n'),
 ('drop_physical_split', lambda s:s.replace('Physical readiness != execution attestation','Physical readiness = execution attestation',1)),
 ('lean_complete', lambda s:s+'\nLEAN may claim COMPLETE\n'),
 ('drop_human_validation', lambda s:s.replace('Human validation and final responsibility remain mandatory','Human validation is optional',1)),
 ('add_companion_dependency', lambda s:s+'\nLoad RUNTIME_LOCAL_HOST.md before work.\n'),
 ('swap_profile_sections', lambda s:s.replace('ON LEAN','__TMP__',1).replace('ON ATTESTED','ON LEAN',1).replace('__TMP__','ON ATTESTED',1)),
 ('drop_pre_allowlist', lambda s:s.replace('pre_admission_allowlist','allowlist',1)),
 ('drop_accept_binding', lambda s:s.replace('acceptance_evidence := exact human message + resolved_revision + contract_sha256','acceptance_evidence := human message',1)),
 ('drop_no_simulation', lambda s:s.replace('Never simulate receipt/nonces/digests.','receipt simulation allowed.',1)),
)

def main()->int:
    base=PROMPT.read_text(encoding='utf-8')
    base_errors=validate(base)
    if base_errors:
        print(json.dumps({'status':'BASE_FAIL','errors':base_errors},ensure_ascii=False,indent=2)); return 1
    rng=random.Random(SEED)
    killed=0; families={name:0 for name,_ in MUTATIONS}
    h=hashlib.sha256()
    for i in range(CASES):
        name,op=rng.choice(MUTATIONS); families[name]+=1
        mutant=op(base)
        if rng.randrange(3)==0:
            mutant=mutant.replace('\n\n','\n',rng.randrange(1,4))
        errors=validate(mutant)
        h.update(f'{i}|{name}|{len(mutant)}|{";".join(errors)}\n'.encode())
        if errors: killed+=1
    result={'status':'PASS' if killed==CASES else 'FAIL','seed':SEED,'cases':CASES,'killed':killed,'survivors':CASES-killed,'prompt_chars':len(base),'limit':8000,'headroom':8000-len(base),'families':families,'digest':h.hexdigest(),'scope':'synthetic prompt/process mutation; not empirical host latency or independent legal validation'}
    out=ROOT/'docs/evidence/local-chat-prompt-mutation-20260904.json'; out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
