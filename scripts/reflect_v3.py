from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import argparse,itertools,json

DIMENSIONS={
    'task':['continue','rewrite','reorganize','compress','expand','ex_novo'],
    'evidence':['primary_complete','mixed','secondary_only','gap'],
    'style':['aligned','oversectioned','rhythm_drift','unknown'],
    'benchmark':['not_required','committed_pass','integrity_fail','missing'],
    'host':['full','no_web','read_only'],
    'setup':['accepted','modified','human_decision'],
}

def semantic_signature(values):
    d=dict(zip(DIMENSIONS,values))
    risks=[]
    if d['evidence'] in {'secondary_only','gap'}: risks.append('source')
    if d['style'] in {'oversectioned','rhythm_drift','unknown'}: risks.append('style')
    if d['benchmark'] in {'integrity_fail','missing'}: risks.append('benchmark')
    if d['host']!='full': risks.append('capability')
    if d['setup']=='human_decision': risks.append('human')
    # Preserve task and setup because the same failure has different legal/editorial
    # significance across transformations.
    return (d['task'],d['setup'],tuple(sorted(risks)),d['evidence'],d['style'],d['benchmark'],d['host'])

def run(no_novelty_target=1000):
    values=list(itertools.product(*DIMENSIONS.values()))
    seen=set(); iterations=0; no_novelty=0; discoveries=[]
    for combo in itertools.chain(values,itertools.cycle(values)):
        sig=semantic_signature(combo); novelty=sig not in seen
        if novelty:
            seen.add(sig); no_novelty=0
            if len(discoveries)<20: discoveries.append({'q':len(seen),'signature':repr(sig)})
        else: no_novelty+=1
        iterations+=1
        if no_novelty>=no_novelty_target: break
    return {'Q':len(seen),'iterations':iterations,'no_novelty_streak':no_novelty,'target':no_novelty_target,'saturated':True,'dimensions':{k:len(v) for k,v in DIMENSIONS.items()},'sample_discoveries':discoveries}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--target',type=int,default=1000); p.add_argument('--json-out'); a=p.parse_args(); r=run(a.target); t=json.dumps(r,ensure_ascii=False,indent=2)
    if a.json_out: open(a.json_out,'w',encoding='utf-8').write(t+'\n')
    print(t); return 0
if __name__=='__main__': raise SystemExit(main())
