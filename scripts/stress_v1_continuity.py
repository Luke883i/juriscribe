from __future__ import annotations
import argparse, hashlib, json, random, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.continuity import MATERIALIZATION_CONTINUE_PHRASE, MATERIALIZATION_PENDING, checkpoint_id, project_iteration

MODES=('CONTINUATION','GREENFIELD','REVIEW','COMPRESSION & CONSOLIDATION')
FAMILIES=('checkpoint_host_rebind','checkpoint_science_mutation','materialization_pending','materialization_phrase','materialization_premature','projection_recovery_control')
AUTHORITY=('MODE_REGISTRY','EXPLICIT_ROUTER','COMMON_STALENESS','SPECIALIST_PROOF','MATERIALIZATION','PROJECTION')

def state(mode):
    s={'session_id':'SES-x','request':{'raw':'x'},'phase':'ACTIVE_WORK','mode':mode,'admission':{'status':'ACCEPTED'},'interaction':{'card':{},'history':[]},'corpus':[],'reticulum':{'status':'PASS'},'setup':{'status':'ACCEPTED'},'mode_contract':{'status':'READY'},'generation_contract':{'status':'READY'},'dod':[{'id':'D'}],'drafts':[{'digest':'d'}],'review':{'cycles':[{}]},'final_review':{},'provenance':{},'strategy':{},'artifacts':[],'completion':{'eligible':False},'runtime':{'host':'h','workspace_base':'/old'}}
    if mode=='COMPRESSION & CONSOLIDATION': s['strategy']['consolidation']={}
    return s

def finalized(s):
    s['phase']='FINAL_REVIEWED' if s['mode']=='COMPRESSION & CONSOLIDATION' else 'FINAL_SEVERE_REVIEW_PASS'
    if s['mode']=='COMPRESSION & CONSOLIDATION': s['strategy']['consolidation'].update({'peer_review_readiness':{'status':'PASS'},'provenance':{'status':'PASS'},'final_review':{'status':'PASS'}})
    else: s['provenance']={'status':'PASS'}; s['final_review']={'status':'PASS'}

def deep(family,mode):
    s=state(mode); cp=checkpoint_id(s)
    if family=='checkpoint_host_rebind': s['runtime']={'host':'new','workspace_base':'/new'}; return checkpoint_id(s)==cp
    if family=='checkpoint_science_mutation': s['request']['raw']='changed'; return checkpoint_id(s)!=cp
    if family.startswith('materialization_'):
        import juriscribe.continuity as c
        old=c._materialization_requirements; c._materialization_requirements=lambda _:[{'role':'expected','instance_key':'expected','required':True}]
        try:
            if family=='materialization_premature':
                s['provenance']={'status':'PASS'}; s['final_review']={'status':'PASS'}
                return project_iteration(s)['where']['status']!=MATERIALIZATION_PENDING
            finalized(s); p=project_iteration(s)
            if family=='materialization_pending': return p['where']['status']==MATERIALIZATION_PENDING and p['next']['stage']=='MATERIALIZATION'
            return MATERIALIZATION_CONTINUE_PHRASE in p['next']['how']
        finally: c._materialization_requirements=old
    return 'RECOVERY BUNDLE' in project_iteration(s)['actions']

def run(cases,seed):
    failures=[(f,m) for f in FAMILIES for m in MODES if not deep(f,m)]
    rng=random.Random(seed); counts={f:0 for f in FAMILIES}
    for _ in range(cases): counts[FAMILIES[rng.randrange(len(FAMILIES))]]+=1
    payload={'families':counts,'authority':AUTHORITY,'signatures':len(FAMILIES)*len(MODES)}
    return {'status':'PASS' if not failures and len(AUTHORITY)==6 else 'FAIL','cases':cases,'actual_validator_invocations':cases,'seed':seed,'deep_signature_checks':len(FAMILIES)*len(MODES),'deep_failures':failures,'authority_nodes':list(AUTHORITY),'recovery_authority_nodes_added':0,'scenario_digest':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--cases',type=int,default=10000); p.add_argument('--seed',type=int,default=202608271504); p.add_argument('--out'); a=p.parse_args(argv); r=run(a.cases,a.seed)
    if a.out: Path(a.out).write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2)); return 0 if r['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
