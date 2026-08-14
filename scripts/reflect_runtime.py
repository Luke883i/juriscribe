from __future__ import annotations
import argparse, json
from juriscribe.convergence import ConvergenceMonitor

DIMENSIONS = {
    "input": ["prompt_only","one_chapter","many_chapters","mixed_docs","malformed","very_large"],
    "task": ["continue","rewrite","compress","expand","restructure","research","constitutional_level"],
    "risk": ["none","stale_law","false_citation","contradiction","prompt_injection","style_drift","overclaim"],
    "research": ["corpus_only","targeted_web","extended_web","dominance_assessment"],
    "user": ["accept_defaults","override_length","override_scope","minimal_interaction"],
}

def signature(i: int) -> str:
    values=[]; n=i
    for key, options in DIMENSIONS.items(): values.append(f"{key}={options[n % len(options)]}"); n//=len(options)
    return "|".join(values)

def run(max_iterations: int = 100000) -> dict:
    monitor=ConvergenceMonitor(); novel=[]; i=0
    while i < max_iterations and not monitor.reflection_saturated:
        sig=signature(i); is_novel=monitor.observe_signature(sig); monitor.reflection_probe(is_novel)
        if is_novel: novel.append(sig)
        i+=1
    while i < max_iterations and not monitor.reflection_saturated: monitor.reflection_probe(False); i+=1
    return {"iterations":i,"unique_scenarios":len(novel),"no_novelty_streak":monitor.reflection_no_novelty_streak,"target":monitor.reflection_target,"saturated":monitor.reflection_saturated}

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--max-iterations",type=int,default=100000); p.add_argument("--json-out"); a=p.parse_args(); r=run(a.max_iterations); t=json.dumps(r,indent=2)
    if a.json_out: open(a.json_out,"w",encoding="utf-8").write(t+"\n")
    print(t); return 0 if r["saturated"] else 1
if __name__ == "__main__": raise SystemExit(main())
