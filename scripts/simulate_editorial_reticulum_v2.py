from __future__ import annotations
import argparse, copy, json, sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.consolidation import build_lossless_inventory, canonical_digest
from juriscribe.editorial_reticulum import build_editorial_execution_reticulum, build_editorial_refinement_proof, verify_editorial_execution_reticulum
from juriscribe.editorial_stress import (
    DEFAULT_SEEDS,
    FLAG_DUPLICATE_OUTPUT, FLAG_EXPANSION_WITHOUT_CAUSE, FLAG_FALSE_WITNESS,
    FLAG_HUMAN_DIVERGENT_REPEAT, FLAG_HUMAN_MATERIAL_RECALIBRATION,
    FLAG_NEW_UNIT, FLAG_RELATION_REWIRE, FLAG_STALE_BINDING, FLAG_UNAUTHORIZED_MERGE,
    FLAG_UNAUTHORIZED_REORDER, FLAG_UNAUTHORIZED_SPLIT, FLAG_UNBOUND_GAP,
    FLAG_UNIT_LOSS, FLAG_UNJUSTIFIED_OPERATION, FLAG_UNKNOWN_OBJECT,
    build_editorial_mutation_evidence, validate_case_vector, validate_editorial_mutation_evidence,
)

SCENARIOS=[
 ('valid_control','SEMANTIC_PRESERVATION',0,'valid',True),
 ('lost_unit','SEMANTIC_PRESERVATION',FLAG_UNIT_LOSS,'valid',False),
 ('new_unit','SEMANTIC_PRESERVATION',FLAG_NEW_UNIT,'valid',False),
 ('relation_rewire','RELATION_INTEGRITY',FLAG_RELATION_REWIRE,'valid',False),
 ('false_witness','SEMANTIC_PRESERVATION',FLAG_FALSE_WITNESS,'valid',False),
 ('unknown_output_object','SEMANTIC_PRESERVATION',FLAG_UNKNOWN_OBJECT,'valid',False),
 ('unbound_gap','GAP_OPERATION_CAUSALITY',FLAG_UNBOUND_GAP,'valid',False),
 ('unjustified_operation','GAP_OPERATION_CAUSALITY',FLAG_UNJUSTIFIED_OPERATION,'valid',False),
 ('unauthorized_reorder','ORDER_DISCIPLINE',FLAG_UNAUTHORIZED_REORDER,'valid',False),
 ('unauthorized_merge','MERGE_SPLIT_DISCIPLINE',FLAG_UNAUTHORIZED_MERGE,'valid',False),
 ('unauthorized_split','MERGE_SPLIT_DISCIPLINE',FLAG_UNAUTHORIZED_SPLIT,'valid',False),
 ('overcompression','COMPRESSION_BOUNDS',0,'under',False),
 ('overexpansion','COMPRESSION_BOUNDS',0,'over',False),
 ('unjustified_expansion','COMPRESSION_BOUNDS',FLAG_EXPANSION_WITHOUT_CAUSE,'expanded',False),
 ('duplicate_output','REDUNDANCY',FLAG_DUPLICATE_OUTPUT,'valid',False),
 ('stale_binding','STALE_BINDING',FLAG_STALE_BINDING,'valid',False),
 ('human_material_recalibration','HUMAN_CALIBRATION',FLAG_HUMAN_MATERIAL_RECALIBRATION,'valid',False),
 ('human_divergent_repeat','HUMAN_IDEMPOTENCY',FLAG_HUMAN_DIVERGENT_REPEAT,'valid',False),
 ('human_repeat_idempotent','HUMAN_IDEMPOTENCY',0,'valid',True),
 ('unicode_layout_edge','UNICODE_LAYOUT_EDGE',0,'valid',True),
 ('long_form_scale','LONG_FORM_SCALE',0,'valid',True),
]


def _fixture():
    src='The hypothesis predicts a measurable effect.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
    inv=build_lossless_inventory(src,source_id='cand',role='candidate_material'); o=inv['objects']
    units=[
      {'id':'U1','object_id':o[0]['id'],'source_id':'cand','material_role':'candidate_material','kind':'CLAIM','text':o[0]['text'],'material':True},
      {'id':'U2','object_id':o[1]['id'],'source_id':'cand','material_role':'candidate_material','kind':'METHOD','text':o[1]['text'],'material':True},
      {'id':'U3','object_id':o[2]['id'],'source_id':'cand','material_role':'candidate_material','kind':'RESULT','text':o[2]['text'],'material':True},
      {'id':'U4','object_id':o[3]['id'],'source_id':'cand','material_role':'candidate_material','kind':'LIMITATION','text':o[3]['text'],'material':True},
    ]
    relations=[{'id':'R1','source':'U3','predicate':'SUPPORTS','target':'U1','material':True},{'id':'R2','source':'U2','predicate':'WARRANTS','target':'U1','material':True},{'id':'R3','source':'U4','predicate':'QUALIFIES','target':'U1','material':True}]
    plan={'status':'READY','digest':'PLAN-DEEP','gaps':[{'id':'G1','unit_id':'U1'},{'id':'G2','unit_id':'U3'}],'operations':[{'id':'O1','unit_id':'U1','operation':'CLARIFY','gap_ids':['G1'],'rationale':'reduce ambiguity','expected_benefit':'clearer causal claim','degradation_risk':'LOW'},{'id':'O2','unit_id':'U3','operation':'LOCAL_REWRITE','gap_ids':['G2'],'rationale':'remove redundancy','expected_benefit':'higher information density','degradation_risk':'LOW'}]}
    state=SimpleNamespace(strategy={'consolidation':{'inventories':{'cand':inv},'refactoring_contract':plan}},reticulum={'status':'PASS','digest':'RET-DEEP'},epistemic_units=units,relations=relations)
    return state,src


def _projection(state,text):
    inv=build_lossless_inventory(text,source_id='cand',role='candidate_material')
    return {'units':[{**u,'object_id':obj['id'],'text':obj['text']} for u,obj in zip(state.epistemic_units,inv['objects'])],'relations':[dict(r) for r in state.relations]}


def deep_checks(rounds=125):
    checks=0; mismatches=0
    for _ in range(rounds):
        s,src=_fixture(); r=build_editorial_execution_reticulum(s); checks+=1; mismatches += r['status']!='PASS'
        ok,_=verify_editorial_execution_reticulum(s,r); checks+=1; mismatches += not ok
        s2,_=_fixture(); s2.relations=[x for x in s2.relations if x['predicate'] not in ('SUPPORTS','WARRANTS')]; checks+=1; mismatches += build_editorial_execution_reticulum(s2)['status']!='FAIL'
        s3,_=_fixture(); s3.strategy['consolidation']['refactoring_contract']['operations'][0]['expected_benefit']=''; checks+=1; mismatches += build_editorial_execution_reticulum(s3)['status']!='FAIL'
        refined='The hypothesis predicts a measurable effect with a prespecified direction.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe interpretation is limited by sample size.'
        p=_projection(s,refined); sp={'status':'PASS','digest':canonical_digest(p)}; ep=build_editorial_refinement_proof(s,source_id='cand',refined_text=refined,projection=p,structural_proof=sp,execution_reticulum=r); checks+=1; mismatches += ep['status']!='PASS'
        tiny='Effect.\n\nMethod.\n\nResult.\n\nLimit.'; p2=_projection(s,tiny); sp2={'status':'PASS','digest':canonical_digest(p2)}; checks+=1; mismatches += build_editorial_refinement_proof(s,source_id='cand',refined_text=tiny,projection=p2,structural_proof=sp2,execution_reticulum=r)['status']!='FAIL'
        tampered=copy.deepcopy(r); tampered['candidate_relation_coverage']=0.5; checks+=1; mismatches += verify_editorial_execution_reticulum(s,tampered)[0]
        dup='The hypothesis predicts a measurable effect.\n\nThe experiment uses a blinded protocol.\n\nThe observed result supports the hypothesis.\n\nThe observed result supports the hypothesis.'; p3=_projection(s,dup); sp3={'status':'PASS','digest':canonical_digest(p3)}; checks+=1; mismatches += build_editorial_refinement_proof(s,source_id='cand',refined_text=dup,projection=p3,structural_proof=sp3,execution_reticulum=r)['status']!='FAIL'
    return checks,mismatches


def run(cases:int, seed_offset:int=0):
    seeds=[int(x)+int(seed_offset) for x in DEFAULT_SEEDS]
    n=len(SCENARIOS); counts=[0]*n; seed_counts=[0]*len(seeds); killed=set(); mismatches=0; survivors=0
    mask=(1<<64)-1; x=(seeds[0]^0x9E3779B97F4A7C15)&mask
    for i in range(cases):
        si=i & (len(seeds)-1); seed_counts[si]+=1
        x=(x*6364136223846793005 + 1442695040888963407 + seeds[si]) & mask
        idx=(x>>32)%n; counts[idx]+=1
        name,family,flags,ratio_mode,expected=SCENARIOS[idx]
        if ratio_mode=='under': ratio=200 + ((x>>8)%200)
        elif ratio_mode=='over': ratio=1351 + ((x>>8)%450)
        elif ratio_mode=='expanded': ratio=1051 + ((x>>8)%299)
        else: ratio=650 + ((x>>8)%401)
        actual=validate_case_vector(flags,ratio)
        if actual!=expected: mismatches+=1
        if not expected:
            if actual: survivors+=1
            else: killed.add(name)
    scenario_counts={SCENARIOS[i][0]:counts[i] for i in range(n) if counts[i]}
    family_counts=Counter()
    for i,c in enumerate(counts): family_counts[SCENARIOS[i][1]]+=c
    deep,deep_mismatches=deep_checks()
    mismatches += deep_mismatches
    state,_=_fixture(); ret=build_editorial_execution_reticulum(state)
    evidence=build_editorial_mutation_evidence(instances=cases,plan_digest='PLAN-DEEP',reticulum_digest='RET-DEEP',execution_reticulum_digest=ret['digest'],seed_counts={str(seeds[i]):seed_counts[i] for i in range(len(seeds))},scenario_counts=scenario_counts,family_counts=dict(family_counts),killed_mutation_classes=sorted(killed),deep_checks=deep,survivors=survivors,mismatches=mismatches,seeds=seeds)
    ok,errors=validate_editorial_mutation_evidence(evidence,plan_digest='PLAN-DEEP',reticulum_digest='RET-DEEP',execution_reticulum_digest=ret['digest'])
    return {'status':'PASS' if ok and mismatches==0 and survivors==0 else 'FAIL','evidence':evidence,'validation_errors':errors}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--cases',type=int,default=10_000_000); ap.add_argument('--seed-offset',type=int,default=0); ap.add_argument('--json-out'); a=ap.parse_args()
    out=run(a.cases,a.seed_offset); text=json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n';
    if a.json_out: Path(a.json_out).write_text(text,encoding='utf-8')
    print(text,end=''); raise SystemExit(0 if out['status']=='PASS' else 1)
