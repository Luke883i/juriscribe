from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from juriscribe.editorial import resolve_editorial_standard,validate_editorial_standard
from juriscribe.modes import CONTINUATION,GREENFIELD,REVIEW,build_mode_contract,required_artifact_roles
from juriscribe.setup import accept_setup,propose_setup
MODES=[CONTINUATION,GREENFIELD,REVIEW]
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def run(cases=30000):
    if cases<3 or cases%3: raise ValueError("cases must be divisible by 3")
    per_mode=cases//3; ret={"status":"PASS","digest":"r"*64}; mining={"surface":{"word_count":1200},"style":{"register":"formal"}}; killed=accepted=failures=0; signatures=[]
    for mode in MODES:
        for i in range(per_mode):
            request={"raw":f"scenario {mode} {i}"}; proposal=propose_setup(mining,request,reticulum=ret,mode=mode); overrides={"review_output":"REPORT_AND_REVISED_TEXT"} if mode==REVIEW and i%2 else None; setup=accept_setup(proposal,overrides); editorial=resolve_editorial_standard(mode,setup,request=request,mining=mining); role={CONTINUATION:"preceding_chapter",GREENFIELD:"concept_source",REVIEW:"review_target"}[mode]; gc={"status":"READY","contract_digest":"g"*64} if mode!=REVIEW else {"status":"NOT_REQUIRED"}; corpus=[{"role":role,"digest":hashlib.sha256(f"{mode}:{i}".encode()).hexdigest()}]; mutant=i%5
            if mutant==0: corpus=[{"role":"wrong_role","digest":corpus[0]["digest"]}]
            elif mutant==1: editorial=dict(editorial,status="FAIL"); editorial["digest"]=hashlib.sha256(b"tampered").hexdigest()
            contract=build_mode_contract(mode,request=request,corpus=corpus,reticulum=ret,setup=setup,editorial_standard=editorial,generation_contract=gc); is_mutant=mutant in {0,1}; observed_fail=contract["status"]=="FAIL" or not validate_editorial_standard(editorial,mode=mode)[0]
            if is_mutant and observed_fail: killed+=1
            elif not is_mutant and not observed_fail: accepted+=1
            else: failures+=1
            signatures.append((mode,i,mutant,contract["status"],tuple(sorted(required_artifact_roles(mode,setup)))))
    return {"schema":"juriscribe-trimode-validation/v1","cases":cases,"per_mode":per_mode,"modes":MODES,"killed_mutants":killed,"accepted_controls":accepted,"failures":failures,"status":"PASS" if failures==0 else "FAIL","scenario_digest":digest(signatures),"notes":"Property/mutation tests of mode routing and editorial contracts; not legal judgments or LLM calls."}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--cases",type=int,default=30000); p.add_argument("--json-out"); a=p.parse_args(); result=run(a.cases)
    if a.json_out: Path(a.json_out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0 if result["status"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
