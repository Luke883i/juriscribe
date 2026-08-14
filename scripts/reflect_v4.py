from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
DIMS={
 'task':['continue','synthesize','reframe','comparative'],
 'corpus':['single_chapter','multi_chapter','with_bibliography','mixed_age'],
 'reticulum':['dense','sparse','cross_chapter','contradictory'],
 'sources':['primary_complete','mixed','stale_risk','unavailable'],
 'inference':['direct','strong','countered','cyclic'],
 'style':['aligned','oversectioned','compressed'],
 'host':['full','no_web','no_docx'],
 'user':['accepted','modified'],
}
def run(target):
    keys=list(DIMS); seen=set(); sample=[]; q=0
    for values in itertools.product(*(DIMS[k] for k in keys)):
        sig=tuple(values)
        if sig not in seen:
            seen.add(sig); q+=1
            if len(sample)<12: sample.append({'q':q,'signature':dict(zip(keys,values))})
    known=next(iter(seen)); streak=0; iterations=q
    while streak<target:
        iterations+=1
        if known in seen: streak+=1
        else: seen.add(known); streak=0
    return {'Q':q,'iterations':iterations,'no_novelty_streak':streak,'target':target,'saturated':streak>=target,'dimensions':{k:len(v) for k,v in DIMS.items()},'sample_discoveries':sample}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--target',type=int,default=1000); p.add_argument('--json-out'); a=p.parse_args(); r=run(a.target); text=json.dumps(r,ensure_ascii=False,indent=2)
    if a.json_out: Path(a.json_out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if r['saturated'] else 1
if __name__=='__main__': raise SystemExit(main())
