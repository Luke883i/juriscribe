from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.consolidation import build_lossless_inventory,text_digest
from juriscribe.semantic_proof import build_structural_semantic_proof,verify_structural_semantic_proof

CANON='Regola canonica.\n\nMetodo canonico.'
SOURCE='Premessa candidata.\n\nConclusione candidata.'
REFINED='Premessa candidata chiarita.\n\nConclusione candidata.'

def fixture():
    canon=build_lossless_inventory(CANON,source_id='canon',role='canonical_material')
    cand=build_lossless_inventory(SOURCE,source_id='cand',role='candidate_material')
    units=[]
    for inv in (canon,cand):
        for obj in inv['objects']:
            units.append({'id':'U-'+obj['id'],'object_id':obj['id'],'source_id':inv['source_id'],'material_role':inv['role'],'kind':'ARGUMENT','text':obj['text'],'material':True})
    c=next(u for u in units if u['source_id']=='canon')
    rels=[{'id':f'R-{i}','source':c['id'],'predicate':'CONDITIONS','target':u['id'],'material':True} for i,u in enumerate([u for u in units if u['source_id']=='cand'],1)]
    state=SimpleNamespace(corpus=[{'source_id':'canon','role':'canonical_material','digest':text_digest(CANON)},{'source_id':'cand','role':'candidate_material','digest':text_digest(SOURCE)}],epistemic_units=units,relations=rels,reticulum={'status':'PASS','digest':'RET'},strategy={'consolidation':{'inventories':{'canon':canon,'cand':cand},'refactoring_contract':{'status':'READY','digest':'PLAN'}}})
    inv=build_lossless_inventory(REFINED,source_id='cand',role='candidate_material')
    before=[u for u in units if u['source_id']=='cand']
    projected=[{**u,'object_id':obj['id'],'text':obj['text']} for u,obj in zip(before,inv['objects'])]
    return state,{'units':projected,'relations':[dict(r) for r in rels]}

def projection_case(base,name):
    p={'units':[dict(x) for x in base['units']],'relations':[dict(x) for x in base['relations']]}
    if name=='valid': return p,True
    if name=='lost_unit': p['units']=p['units'][1:]
    elif name=='new_unit': p['units'][0]['id']='U-NEW'
    elif name=='lost_relation': p['relations']=p['relations'][1:]
    elif name=='changed_relation': p['relations'][0]['predicate']='CONTRADICTS'
    elif name=='unknown_object': p['units'][0]['object_id']='OBJ-MISSING'
    elif name=='false_witness': p['units'][0]['text']='testo non presente nel refined candidate'
    elif name=='source_spoof': p['units'][0]['source_id']='canon'
    elif name=='role_spoof': p['units'][0]['material_role']='canonical_material'
    else: raise ValueError(name)
    return p,False

def run(cases):
    state,base=fixture(); classes=['valid','lost_unit','new_unit','lost_relation','changed_relation','unknown_object','false_witness','source_spoof','role_spoof']
    counts=Counter(); killed=set(); mismatches=0
    for i in range(cases):
        name=classes[i%len(classes)]; projection,expected=projection_case(base,name)
        proof=build_structural_semantic_proof(state,source_id='cand',refined_text=REFINED,projection=projection)
        actual=proof.get('status')=='PASS'; counts[name]+=1
        if not expected and not actual: killed.add(name)
        if actual!=expected: mismatches+=1
    valid=build_structural_semantic_proof(state,source_id='cand',refined_text=REFINED,projection=base)
    tampered=dict(valid); tampered['structural_unit_recall']=0.5
    tamper_ok,_=verify_structural_semantic_proof(state,source_id='cand',refined_text=REFINED,proof=tampered)
    if tamper_ok: mismatches+=1
    status='PASS' if mismatches==0 and killed==set(classes)-{'valid'} else 'FAIL'
    return {'schema':'juriscribe-runtime-semantics-stress/v1','profile':'JURISCRIBE_RUNTIME_SEMANTICS_STRESS_V1','status':status,'instances':cases,'instance_claim_scope':'SOAK_VOLUME_NOT_UNIQUE_SEMANTIC_CASES','equivalence_classes':len(classes)+1,'class_counts':dict(sorted(counts.items())),'killed_projection_mutation_classes':sorted(killed),'proof_tamper_killed':not tamper_ok,'mismatches':mismatches}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cases',type=int,default=100_000); ap.add_argument('--json-out'); a=ap.parse_args()
    if a.cases<=0: raise SystemExit('cases must be positive')
    result=run(a.cases); text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if a.json_out: Path(a.json_out).write_text(text,encoding='utf-8')
    print(text,end=''); return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
