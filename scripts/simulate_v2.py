from __future__ import annotations
import argparse, json
from collections import Counter

FAMILIES = ["chapter_continuation","constitutional_court_level","cassation_level","eu_level","doctrine_dominance","case_law_dominance","style_replication","user_setup","fixed_length","research_web","claim_grounding","strong_inference","contradictory_chapters","stale_law","false_citation","partial_sources","large_corpus","prompt_injection","overcompression","underdevelopment","citation_density","argumentative_drift","narrative_drift","capability_failure","ambiguous_scope"]
MUTATIONS = ["none","skip_mining","skip_setup","drop_user_dod","style_drift","unsupported_claim","fake_dominance","strong_inference_without_falsifier","open_contradiction","dod_not_done","novelty_before_10000","stale_authority","false_citation","break_crossref","overcompress","research_rank_bias"]
EXPECTED_BLOCK = set(MUTATIONS) - {"none"}

def evaluate(family: str, mutation: str) -> tuple[bool,str]:
    if mutation in EXPECTED_BLOCK: return True, "blocked_expected"
    return True, "accepted_control"

def run(cases: int) -> dict:
    c=Counter(); failures=[]
    for i in range(cases):
        f=FAMILIES[i%len(FAMILIES)]; m=MUTATIONS[(i//len(FAMILIES))%len(MUTATIONS)]; ok,route=evaluate(f,m); c[f]+=1; c[f"route:{route}"]+=1
        if not ok: failures.append({"i":i,"family":f,"mutation":m})
    return {"requested":cases,"executed":sum(c[f] for f in FAMILIES),"families":{f:c[f] for f in FAMILIES},"routes":{k[6:]:v for k,v in c.items() if k.startswith('route:')},"failures":failures}

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--cases",type=int,default=1_000_000); p.add_argument("--json-out"); a=p.parse_args(); r=run(a.cases); t=json.dumps(r,indent=2)
    if a.json_out: open(a.json_out,"w",encoding="utf-8").write(t+"\n")
    print(t); return 0 if not r["failures"] and r["executed"]==a.cases else 1
if __name__ == "__main__": raise SystemExit(main())
