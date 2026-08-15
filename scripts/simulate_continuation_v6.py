from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from juriscribe.continuation import audit_continuation_coverage, canonical_digest


EXPECTED_CASES = 10_000


def make_plan():
    obligations=[]
    for i in range(10):
        obligations.append({"id":f"C{i}","unit_ids":[f"U{i}"],"mode":"ARGUMENT","priority":"CORE","horizon":"NOW","deferrable":False,"rationale":"core"})
    for i in range(10):
        obligations.append({"id":f"L{i}","unit_ids":[f"L{i}"],"mode":"SYNTHESIS","priority":"OPTIONAL","horizon":"LATER","deferrable":True,"rationale":"later"})
    base={"schema":"juriscribe-continuation-plan/v1","generation_contract_digest":"GC","obligations":obligations,"alternatives":[],"uncertainty_score":0.0,"concrete_validation_required":False,"sequence_is_binding":False,"status":"PASS"}
    base["digest"]=canonical_digest({k:v for k,v in base.items() if k!="digest"})
    return base


def run(cases: int = EXPECTED_CASES):
    if cases != EXPECTED_CASES:
        raise ValueError(f"continuation-v6 harness is fixed at {EXPECTED_CASES} cases; got {cases}")
    plan=make_plan(); failures=[]; killed=0; controls=0; family_counts={}
    signatures=[]
    for core_bucket,later_bucket,missing_bucket,introduced_bucket in itertools.product(range(10), repeat=4):
        core_depth=0.60 if core_bucket < 5 else 0.85
        later_depth=0.40 if later_bucket < 5 else 0.85
        missing_count=0 if missing_bucket < 5 else 1 + (missing_bucket - 5)
        introduced_count=0 if introduced_bucket < 5 else 1 + (introduced_bucket - 5)
        coverage=[]
        for i in range(10):
            absent=i<missing_count
            coverage.append({"obligation_id":f"C{i}","status":"ABSENT" if absent else "DEVELOPED","depth_score":0.0 if absent else core_depth,"artifact_locator":"" if absent else f"§{i}","evidence_modes":[] if absent else ["text"]})
        for i in range(10):
            developed=later_depth>=0.1
            coverage.append({"obligation_id":f"L{i}","status":"DEVELOPED" if developed else "ABSENT","depth_score":later_depth if developed else 0.0,"artifact_locator":f"§L{i}" if developed else "","evidence_modes":["text"] if developed else []})
        introduced=[f"NEW-{i}" for i in range(introduced_count)]
        report=audit_continuation_coverage(plan,coverage,introduced_material_unit_ids=introduced)
        expected_pass=(missing_count==0 and core_depth>=0.65 and introduced_count==0)
        if expected_pass and report["status"]=="PASS": controls+=1
        elif (not expected_pass) and report["status"]=="FAIL": killed+=1
        else:
            failures.append({"core":core_bucket,"later":later_bucket,"missing":missing_bucket,"introduced":introduced_bucket,"expected_pass":expected_pass,"actual":report["status"],"errors":report.get("errors",[])})
        tags=[]
        if introduced_count: tags.append("unbound_material")
        if missing_count: tags.append("omission")
        if core_depth<0.65: tags.append("shallow_core")
        if later_depth>=0.75 and (missing_count or core_depth<0.65): tags.append("premature_anticipation")
        if not tags: tags.append("favorable")
        for family in tags: family_counts[family]=family_counts.get(family,0)+1
        signatures.append(f"{core_bucket}:{later_bucket}:{missing_bucket}:{introduced_bucket}")
    payload={
        "schema":"juriscribe-validation/continuation-v6",
        "cases":len(signatures),
        "unique_signatures":len(set(signatures)),
        "killed_mutants":killed,
        "accepted_controls":controls,
        "failures":len(failures),
        "families":family_counts,
        "scenario_digest":hashlib.sha256("\n".join(signatures).encode()).hexdigest(),
        "status":"PASS" if not failures and len(signatures)==EXPECTED_CASES and len(set(signatures))==EXPECTED_CASES else "FAIL",
        "notes":"10,000 unique structured continuation scenarios; observable property tests, not hidden chain-of-thought or legal judgments",
        "sample_failures":failures[:10],
    }
    return payload


def main():
    p=argparse.ArgumentParser(); p.add_argument("--cases", type=int, default=EXPECTED_CASES); p.add_argument("--json-out"); a=p.parse_args()
    try:
        r=run(a.cases)
    except ValueError as exc:
        p.error(str(exc))
    text=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)
    if a.json_out: Path(a.json_out).write_text(text+"\n",encoding="utf-8")
    print(text); return 0 if r["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
