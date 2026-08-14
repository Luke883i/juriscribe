from __future__ import annotations
import argparse,copy,json,random,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.admission import issue_receipt,validate_receipt
from juriscribe.convergence import completion_gate
from juriscribe.generation import REQUIRED_EDGE_FAMILIES,audit_compression
from juriscribe.reticulum import build_generation_contract,validate_reticulum
from juriscribe.sources import ClaimRecord,SourceRecord,validate_claim,validate_inference_graph

FAMILIES=[
'control_completion','admission_missing','admission_stale_hash','admission_ai_actor','reticulum_missing_locator','reticulum_orphan','reticulum_bad_endpoint','generation_stale_reticulum','generation_stale_setup','completion_admission_missing','dod_open','novelty_short','contradiction_open','quality_review','source_pending','artifact_readback_missing','simulation_missing','simulation_family_missing','simulation_failure','compression_missing','compression_loss','compression_added_material','benchmark_missing','benchmark_bad_integrity','strong_inference_no_falsifier','strong_inference_cycle','source_no_pinpoint','source_not_direct','multiple_failures']

def fixture():
    contract=(ROOT/'ISENECA_ACCESS_CONTRACT.md').read_text(encoding='utf-8'); receipt=issue_receipt(contract,phrase='I ACCEPT',actor_type='human',evidence_type='explicit_user_message',user_message='I ACCEPT',accepted_at='2026-01-01T00:00:00+00:00')
    sources=[{'id':'S1'},{'id':'S2'}]
    units=[
      {'id':'U1','kind':'DEFINITION','text':'Definizione base','source_id':'S1','source_locator':'P1','chapter':'1','material':True,'tags':['preserve']},
      {'id':'U2','kind':'RULE','text':'Regola base','source_id':'S1','source_locator':'P2','chapter':'1','material':True,'tags':['preserve']},
      {'id':'U3','kind':'OPEN_ISSUE','text':'Questione da sviluppare','source_id':'S2','source_locator':'P1','chapter':'2','material':False,'tags':['develop']},
      {'id':'U4','kind':'CLAIM','text':'Conclusione intermedia','source_id':'S2','source_locator':'P2','chapter':'2','material':True,'tags':[]},]
    relations=[{'source':'U1','predicate':'DEFINES','target':'U2','rationale':'base concettuale'},{'source':'U2','predicate':'ANTICIPATES','target':'U3','rationale':'sviluppo successivo'},{'source':'U3','predicate':'DEVELOPS','target':'U4','rationale':'risposta alla questione'}]
    ret=validate_reticulum(units,relations,source_ids={'S1','S2'}).record(); setup={'status':'ACCEPTED','accepted':{'chapter_function':'continuazione','length_words':[1000,1500],'research_depth':'verifica mirata','argumentative_posture':'continuità'}}; gen=build_generation_contract(ret,setup,units,relations)
    sim={'cases':1000,'seeds':[11,29],'families':sorted(REQUIRED_EDGE_FAMILIES),'failures':0,'escapes':0,'status':'PASS'}
    comp=audit_compression(before_words=1400,after_words=1250,required_unit_ids=['U1','U2','U4'],preserved_unit_ids=['U1','U2','U4'])
    return {'contract':contract,'receipt':receipt,'units':units,'relations':relations,'ret':ret,'setup':setup,'gen':gen,'dod':[{'id':'D1','status':'DONE','blocking':True}],'metrics':{'dod_no_novelty_streak':10000},'contra':[],'quality':{'status':'PASS'},'source':'PASS','artifacts':[{'required':True,'readback':'PASS'}],'sim':sim,'comp':comp}

def complete(f,**kw):
    x={**f,**kw}; return completion_gate(x['dod'],x['metrics'],x['contra'],quality=x['quality'],source_coverage=x['source'],benchmark=x.get('benchmark'),benchmark_required=x.get('benchmark_required',False),artifacts=x['artifacts'],generation_required=True,reticulum=x['ret'],generation_contract=x['gen'],simulation=x['sim'],compression=x['comp'],setup=x['setup'],admission={'status':'ACCEPTED'})

def evaluate(family):
    f=fixture()
    if family=='control_completion': return complete(f)['eligible'] is True,'control'
    if family=='admission_missing': return validate_receipt(None,f['contract'])[0] is False,'admission'
    if family=='admission_stale_hash':
        r=dict(f['receipt']); r['contract_sha256']='0'*64; return validate_receipt(r,f['contract'])[0] is False,'admission'
    if family=='admission_ai_actor':
        try: issue_receipt(f['contract'],phrase='I ACCEPT',actor_type='ai',evidence_type='explicit_user_message',user_message='I ACCEPT'); return False,'admission'
        except PermissionError: return True,'admission'
    if family.startswith('reticulum_'):
        units=copy.deepcopy(f['units']); rel=copy.deepcopy(f['relations'])
        if family=='reticulum_missing_locator': units[0]['source_locator']=''
        elif family=='reticulum_orphan': rel=rel[:1]
        else: rel.append({'source':'U1','predicate':'SUPPORTS','target':'MISSING'})
        return validate_reticulum(units,rel,source_ids={'S1','S2'}).status=='FAIL','reticulum'
    if family=='generation_stale_reticulum':
        ret=dict(f['ret']); ret['digest']='x'; return complete(f,ret=ret)['eligible'] is False,'generation'
    if family=='generation_stale_setup':
        setup=copy.deepcopy(f['setup']); setup['accepted']['length_words']=[2000,2500]; return complete(f,setup=setup)['eligible'] is False,'generation'
    if family=='completion_admission_missing': return completion_gate(f['dod'],f['metrics'],f['contra'],quality=f['quality'],source_coverage=f['source'],artifacts=f['artifacts'],generation_required=True,reticulum=f['ret'],generation_contract=f['gen'],simulation=f['sim'],compression=f['comp'],setup=f['setup'],admission={})['eligible'] is False,'admission'
    if family=='dod_open': d=copy.deepcopy(f['dod']); d[0]['status']='OPEN'; return complete(f,dod=d)['eligible'] is False,'completion'
    if family=='novelty_short': return complete(f,metrics={'dod_no_novelty_streak':9999})['eligible'] is False,'completion'
    if family=='contradiction_open': return complete(f,contra=[{'status':'OPEN','blocking':True}])['eligible'] is False,'completion'
    if family=='quality_review': return complete(f,quality={'status':'REVIEW_REQUIRED'})['eligible'] is False,'quality'
    if family=='source_pending': return complete(f,source='PLANNED')['eligible'] is False,'sources'
    if family=='artifact_readback_missing': return complete(f,artifacts=[{'required':True,'readback':None}])['eligible'] is False,'artifact'
    if family=='simulation_missing': return complete(f,sim={})['eligible'] is False,'simulation'
    if family=='simulation_family_missing':
        sim=copy.deepcopy(f['sim']); sim['families']=sim['families'][:-1]; return complete(f,sim=sim)['eligible'] is False,'simulation'
    if family=='simulation_failure':
        sim=copy.deepcopy(f['sim']); sim['failures']=1; return complete(f,sim=sim)['eligible'] is False,'simulation'
    if family=='compression_missing': return complete(f,comp={})['eligible'] is False,'compression'
    if family=='compression_loss':
        comp=audit_compression(before_words=1400,after_words=1200,required_unit_ids=['U1','U2'],preserved_unit_ids=['U1']); return complete(f,comp=comp)['eligible'] is False,'compression'
    if family=='compression_added_material':
        comp=audit_compression(before_words=1400,after_words=1200,required_unit_ids=['U1'],preserved_unit_ids=['U1'],added_material_unit_ids=['NEW']); return complete(f,comp=comp)['eligible'] is False,'compression'
    if family=='benchmark_missing': return complete(f,benchmark_required=True,benchmark={})['eligible'] is False,'benchmark'
    if family=='benchmark_bad_integrity': return complete(f,benchmark_required=True,benchmark={'score':{'blind_integrity':'FAIL','heading_recall_soft':.9}})['eligible'] is False,'benchmark'
    if family=='strong_inference_no_falsifier':
        s=SourceRecord('S','Norma','u','primary_law',direct_read=True).record(); p=ClaimRecord('P','Premessa','direct','scope',support_source_ids=('S',),status='SUPPORTED',source_evidence=({'source_id':'S','pinpoint':'art. 1','proposition':'premessa'},)).record(); c=ClaimRecord('I','Inferenza','strong_inference','scope',premise_claim_ids=('P',),inference_bridge='ponte',falsifier='',status='INFERRED').record(); return validate_claim(c,[s],[p,c],strict=True)[0] is False,'inference'
    if family=='strong_inference_cycle':
        a={'id':'A','claim_type':'strong_inference','premise_claim_ids':['B']}; b={'id':'B','claim_type':'strong_inference','premise_claim_ids':['A']}; return validate_inference_graph([a,b])[0] is False,'inference'
    if family in {'source_no_pinpoint','source_not_direct'}:
        s=SourceRecord('S','Norma','u','primary_law',direct_read=(family!='source_not_direct')).record(); ev=({'source_id':'S','pinpoint':'' if family=='source_no_pinpoint' else 'art. 1','proposition':'regola'},); c=ClaimRecord('C','Regola','direct','scope',support_source_ids=('S',),status='SUPPORTED',source_evidence=ev).record(); return validate_claim(c,[s],[c],strict=True)[0] is False,'sources'
    if family=='multiple_failures':
        d=copy.deepcopy(f['dod']); d[0]['status']='OPEN'; sim=copy.deepcopy(f['sim']); sim['escapes']=1; return complete(f,dod=d,quality={'status':'FAIL'},source='GAPS_OPEN',sim=sim,comp={})['eligible'] is False,'multiple'
    return False,'unknown'

def run(cases,seeds):
    failures=[]; family_counts=Counter(); category_counts=Counter(); seed_counts=defaultdict(Counter); per_seed=cases//len(seeds); remainder=cases%len(seeds); index=0
    for si,seed in enumerate(seeds):
        rng=random.Random(seed); n=per_seed+(1 if si<remainder else 0)
        for j in range(n):
            family=FAMILIES[j%len(FAMILIES)] if j<len(FAMILIES) else rng.choice(FAMILIES); ok,cat=evaluate(family); family_counts[family]+=1; category_counts[cat]+=1; seed_counts[str(seed)][family]+=1
            if not ok and len(failures)<100: failures.append({'index':index,'seed':seed,'family':family,'category':cat})
            index+=1
    return {'requested':cases,'executed':index,'seeds':seeds,'families':dict(family_counts),'categories':dict(category_counts),'seed_case_counts':{s:sum(c.values()) for s,c in seed_counts.items()},'failures':failures,'passed':not failures}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--cases',type=int,default=100000); p.add_argument('--seeds',default='11,29,47,83,131,257,509,1021,2027,4093'); p.add_argument('--json-out'); a=p.parse_args(); seeds=[int(x) for x in a.seeds.split(',') if x.strip()]; r=run(a.cases,seeds); text=json.dumps(r,ensure_ascii=False,indent=2)
    if a.json_out: Path(a.json_out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
