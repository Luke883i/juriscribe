from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import argparse,json
from collections import Counter
from juriscribe.convergence import completion_gate

MUTATIONS=[
    'control','reopen_dod','short_novelty','open_contradiction','quality_review','source_pending','readback_missing','benchmark_missing','benchmark_bad_integrity','multiple_failures'
]

def good_benchmark():
    return {'score':{'blind_integrity':'PASS','heading_recall_soft':0.75}}

def evaluate(mutation:str)->tuple[bool,str,bool]:
    dod=[{'id':'D1','status':'DONE','blocking':True}]
    metrics={'dod_no_novelty_streak':10000}
    contradictions=[]
    quality={'status':'PASS'}
    source='PASS'
    artifacts=[{'id':'chapter','required':True,'readback':'PASS'}]
    benchmark=good_benchmark(); benchmark_required=False
    if mutation=='reopen_dod': dod[0]['status']='OPEN'
    elif mutation=='short_novelty': metrics['dod_no_novelty_streak']=9999
    elif mutation=='open_contradiction': contradictions=[{'id':'C1','status':'OPEN','blocking':True}]
    elif mutation=='quality_review': quality={'status':'REVIEW_REQUIRED'}
    elif mutation=='source_pending': source='PLANNED'
    elif mutation=='readback_missing': artifacts[0]['readback']=None
    elif mutation=='benchmark_missing': benchmark_required=True; benchmark={}
    elif mutation=='benchmark_bad_integrity': benchmark_required=True; benchmark={'score':{'blind_integrity':'FAIL','heading_recall_soft':0.9}}
    elif mutation=='multiple_failures': dod[0]['status']='OPEN'; quality={'status':'FAIL'}; source='GAPS_OPEN'; metrics['dod_no_novelty_streak']=0
    result=completion_gate(dod,metrics,contradictions,quality=quality,source_coverage=source,benchmark=benchmark,benchmark_required=benchmark_required,artifacts=artifacts)
    expected = mutation=='control'
    return result['eligible']==expected,result['reason'],result['eligible']

def run(cases:int)->dict:
    failures=[]; counts=Counter(); routes=Counter()
    for i in range(cases):
        m=MUTATIONS[i%len(MUTATIONS)]; ok,reason,eligible=evaluate(m); counts[m]+=1; routes['accepted_control' if eligible else reason]+=1
        if not ok and len(failures)<100: failures.append({'i':i,'mutation':m,'reason':reason,'eligible':eligible})
    return {'requested':cases,'executed':cases,'mutations':dict(counts),'routes':dict(routes),'failures':failures,'passed':not failures}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--cases',type=int,default=100000); p.add_argument('--json-out'); a=p.parse_args(); r=run(a.cases); t=json.dumps(r,ensure_ascii=False,indent=2)
    if a.json_out: open(a.json_out,'w',encoding='utf-8').write(t+'\n')
    print(t); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
