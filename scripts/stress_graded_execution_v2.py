from __future__ import annotations
import argparse, hashlib, importlib.util, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('graded_execution',ROOT/'juriscribe'/'graded_execution.py'); m=importlib.util.module_from_spec(spec); assert spec.loader; sys.modules[spec.name]=m; spec.loader.exec_module(m)
def run(cases:int,seed:int)->dict:
    rng=random.Random(seed); violations=0; outcomes={}; access=m.MethodAccess(True,True,True,True)
    for _ in range(cases):
        preference=rng.choices(['ATTESTED_PREFERRED','ATTESTED_REQUIRED','LEAN'],weights=[0.68,0.17,0.15])[0]; runtime=rng.random()<0.61; discovery=rng.random()<0.97; exhausted=rng.random()<0.72
        p=m.choose_execution_profile(access,runtime_reachable=runtime,infrastructure_search_exhausted=exhausted,capability_discovery_complete=discovery,preference=preference); key=p['state']+':'+str(p.get('profile')); outcomes[key]=outcomes.get(key,0)+1
        if preference=='LEAN' and p.get('profile')!='LEAN': violations+=1
        if p.get('profile')=='LEAN' and p.get('runtime_attestation_allowed'): violations+=1
        if p.get('profile')=='LEAN' and not p.get('promotion_requires_replay'): violations+=1
        if preference!='LEAN' and not runtime and discovery and not exhausted and p['state']!='INFRASTRUCTURE_SEARCH': violations+=1
        if not runtime and discovery and exhausted and preference=='ATTESTED_REQUIRED' and p['state']!='ATTESTED_INFRASTRUCTURE_BLOCKED': violations+=1
        claims=m.runtime_claim_projection(profile=p.get('profile') or 'LEAN',runtime_reachable=runtime,receipts_verified=False,complete_verified=False)
        if claims['runtime_receipts_may_be_claimed'] or claims['runtime_complete_may_be_claimed']: violations+=1
    out={'schema':'juriscribe-graded-execution-v2-stress/v1','cases':cases,'seed':seed,'oracle_mismatches':violations,'outcomes':dict(sorted(outcomes.items())),'claim_scope':'EXECUTED_RUNTIME_POLICY_TRACES_NOT_PHYSICAL_HOSTS_LEGAL_MATTERS_OR_LLM_SESSIONS'}; out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return out
def main():
    a=argparse.ArgumentParser(); a.add_argument('--cases',type=int,default=100000); a.add_argument('--seed',type=int,default=2026090401); args=a.parse_args(); r=run(args.cases,args.seed); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(1 if r['oracle_mismatches'] else 0)
if __name__=='__main__': main()
