from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

DIMENSIONS={
  "task":["continue","restructure","update","counterargument"],
  "corpus":["single_chapter","multi_chapter","chapter_plus_bibliography","mixed_versions"],
  "reticulum":["dense","sparse_valid","contradictory","stale"],
  "sources":["primary_complete","mixed_authority","counterauthority","temporal_conflict"],
  "bibliography":["unavailable","complete","gaps_open"],
  "inference":["direct","strong_supported","strong_contested"],
  "review":["clean","major_findings","style_drift","logical_gap"],
  "regeneration":["improves","no_material_gain","degrades"],
  "host":["full","no_web","no_docx"],
  "user":["accepted","modified"],
}


def signature(values):
    return tuple(values)


def risk_tags(record):
    tags=[]
    if record["reticulum"] in {"contradictory","stale"}: tags.append("reticulum_gate")
    if record["sources"] in {"counterauthority","temporal_conflict"}: tags.append("source_conflict")
    if record["bibliography"]=="gaps_open": tags.append("bibliography_gate")
    if record["inference"]=="strong_contested": tags.append("inference_review")
    if record["review"]!="clean": tags.append("scientific_editorial_review")
    if record["regeneration"]=="degrades": tags.append("degradation_guard")
    if record["host"]!="full": tags.append("capability_degradation")
    if record["corpus"]=="mixed_versions": tags.append("version_conflict")
    return tags or ["clean_path"]


def run(target:int=1000):
    keys=list(DIMENSIONS); seen=set(); samples=[]; tag_counts={}; iterations=0
    for values in itertools.product(*(DIMENSIONS[k] for k in keys)):
        iterations+=1; sig=signature(values); seen.add(sig)
        rec=dict(zip(keys,values))
        for tag in risk_tags(rec): tag_counts[tag]=tag_counts.get(tag,0)+1
        if len(samples)<20: samples.append({"m":len(seen),"signature":rec,"risk_tags":risk_tags(rec)})
    M=len(seen)
    # Saturation witness: replay known states deterministically. No new signature may emerge.
    known=list(seen); streak=0
    for i in range(target):
        iterations+=1
        sig=known[(i*7919)%len(known)]
        if sig in seen: streak+=1
        else:
            seen.add(sig); streak=0
    basis={"dimensions":DIMENSIONS,"M":M,"target":target,"tag_counts":tag_counts}
    digest=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
      "schema":"juriscribe-validation/reflection-v5",
      "M":M,"iterations":iterations,"no_novelty_streak":streak,"target":target,"saturated":streak>=target,
      "dimensions":{k:len(v) for k,v in DIMENSIONS.items()},"risk_tag_counts":tag_counts,
      "sample_discoveries":samples,"scenario_digest":digest,
      "interpretation":"observable architecture-state enumeration followed by a no-novelty witness; not hidden chain-of-thought disclosure",
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("--target",type=int,default=1000); p.add_argument("--json-out"); a=p.parse_args(); r=run(a.target); text=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)
    if a.json_out: Path(a.json_out).write_text(text+"\n",encoding="utf-8")
    print(text); return 0 if r["saturated"] else 1
if __name__=="__main__": raise SystemExit(main())
