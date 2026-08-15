from __future__ import annotations
import argparse, hashlib, json, random, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from juriscribe.bibliography import assess_bibliography, bibliography_gate
from juriscribe.generation import REQUIRED_EDGE_FAMILIES, REQUIRED_SIMULATION_CATEGORIES, audit_compression, compression_valid, validate_simulation_receipt
from juriscribe.quality import compare_editorial_style
from juriscribe.reticulum import build_generation_contract, generation_contract_valid, validate_reticulum
from juriscribe.review import REVIEW_CRITERIA, build_review_cycle, regeneration_record, review_gate, validate_findings, validate_scorecard, validate_review_evidence
from juriscribe.sources import ClaimRecord, SourceRecord, validate_claim, validate_inference_graph

CATEGORIES=("adversarial","favorable","stress","editorial_review","logical_semantic_review")
DEFAULT_SEEDS=(11,29,47,83,131,257,509,1021,2027,4093,8191,12289,16381,24593,32771,40961,49157,57347,65537,99991)
CRITERIA={
 "adversarial":{"standard":"fail-closed evidence binding","pass":"every stale, forged, incomplete or degraded receipt is rejected"},
 "favorable":{"standard":"false-positive control","pass":"clean evidence packages are accepted without spurious blockers"},
 "stress":{"standard":"determinism and bounded structural load","pass":"larger valid ledgers/reticula remain deterministic and exception-free; corrupted variants still fail"},
 "editorial_review":{"standard":"publisher-neutral legal monograph review core","pass":"structure/style/bibliography/findings/scorecards produce the expected review disposition"},
 "logical_semantic_review":{"standard":"epistemic graph and strong-inference integrity","pass":"orphaned, cyclic, unsupported, stale or lossful semantic states are rejected"},
}

SCORE_PASS={k:.96 for k in REVIEW_CRITERIA}
REVIEW_EVIDENCE=[{"criterion":k,"evidence_type":"artifact" if k in {"STRUCTURE","EDITORIAL_STYLE","AUDIENCE_FIT"} else "reticulum","status":"VERIFIED","locator":f"evidence:{k}"} for k in REVIEW_CRITERIA]


def base_reticulum(n=6):
    units=[]
    for i in range(n):
        units.append({"id":f"U{i}","kind":"RULE" if i%3==0 else ("QUALIFICATION" if i%3==1 else "CLAIM"),"text":f"Proposizione {i}","source_id":"S1" if i<n//2 else "S2","source_locator":f"§{1+i//3} ¶{i+1}","chapter":"1" if i<n//2 else "2","material":True})
    relations=[]
    for i in range(n-1):
        relations.append({"source":f"U{i}","predicate":"QUALIFIES" if i%2 else "SUPPORTS","target":f"U{i+1}"})
    relations.append({"source":"U0","predicate":"ANTICIPATES","target":f"U{n-1}"})
    return units,relations


def clean_generation():
    units,rels=base_reticulum()
    ret=validate_reticulum(units,rels,source_ids={"S1","S2"}).record()
    setup={"status":"ACCEPTED","accepted":{"length_words":[1500,2200],"chapter_function":"sviluppo sistematico"}}
    gen=build_generation_contract(ret,setup,units,rels)
    return units,rels,ret,setup,gen

UNITS,RELS,RET,SETUP,GEN=clean_generation()
CAND="a"*64; FINAL="b"*64; CONTRACT=GEN["contract_digest"]
CYCLE=build_review_cycle(cycle=1,candidate_digest=CAND,findings=[],scorecard=SCORE_PASS,evidence=REVIEW_EVIDENCE)
SAT={"candidate_digest":CAND,"P":13,"probes":10013,"no_novelty_streak":10000,"no_improvement_without_degradation_streak":10000,"target":10000,"open_blockers":0,"open_majors":0,"degradation_escapes":0,"status":"PASS"}
SIM={"cases":400000,"seeds":list(DEFAULT_SEEDS),"families":sorted(REQUIRED_EDGE_FAMILIES),"categories":{k:80000 for k in REQUIRED_SIMULATION_CATEGORIES},"failures":0,"escapes":0,"false_positives":0,"status":"PASS","candidate_digest":FINAL,"generation_contract_digest":CONTRACT,"scenario_digest":"c"*64}
COMP=audit_compression(before_words=2100,after_words=1950,required_unit_ids=["U0","U1"],preserved_unit_ids=["U0","U1"],before_digest=CAND,after_digest=FINAL,generation_contract_digest=CONTRACT,post_compression_recheck="PASS")
SOURCE=SourceRecord("SRC","Norma","https://example.invalid/source","primary_law",direct_read=True).record()
CLAIM=ClaimRecord("C","Regola circostanziata","direct","scope",support_source_ids=("SRC",),status="SUPPORTED",source_evidence=({"source_id":"SRC","pinpoint":"art. 1","proposition":"regola nel perimetro"},)).record()
BIB=[{"id":"B1","source_id":"SRC","citation":"Fonte normativa, art. 1"}]


def editorial_text(section_count:int, repeats:int=10)->str:
    pieces=["CAPITOLO X"]
    for i in range(section_count):
        pieces.append(f"{i+1}.1 Sezione {i+1}\n"+("Anzitutto la regola va ricostruita nel suo perimetro; tuttavia ogni eccezione deve restare visibile. "*repeats))
    return "\n".join(pieces)
REF_TEXT=editorial_text(5,20)
STYLE_STABLE_STATUS=compare_editorial_style(REF_TEXT,REF_TEXT)["status"]
STYLE_OVER_STATUS=compare_editorial_style(REF_TEXT,editorial_text(18,6))["status"]


def adversarial(family):
    if family=="stale_sim_candidate": return not validate_simulation_receipt({**SIM,"candidate_digest":"x"*64},candidate_digest=FINAL,generation_contract_digest=CONTRACT,require_categories=True)[0]
    if family=="stale_sim_contract": return not validate_simulation_receipt({**SIM,"generation_contract_digest":"x"*64},candidate_digest=FINAL,generation_contract_digest=CONTRACT,require_categories=True)[0]
    if family=="missing_sim_category":
        bad={**SIM,"categories":dict(SIM["categories"])}; bad["categories"]["editorial_review"]=0
        return not validate_simulation_receipt(bad,candidate_digest=FINAL,generation_contract_digest=CONTRACT,require_categories=True)[0]
    if family=="sim_escape": return not validate_simulation_receipt({**SIM,"escapes":1},candidate_digest=FINAL,generation_contract_digest=CONTRACT,require_categories=True)[0]
    if family=="stale_compression_before": return not compression_valid(COMP,expected_before_digest="x"*64,expected_after_digest=FINAL,generation_contract_digest=CONTRACT,strict=True)[0]
    if family=="compression_no_recheck": return not compression_valid({**COMP,"post_compression_recheck":"NOT_RUN"},expected_before_digest=CAND,expected_after_digest=FINAL,generation_contract_digest=CONTRACT,strict=True)[0]
    if family=="bibliography_missing_mapping": return not bibliography_gate(assess_bibliography([{"id":"B2","source_id":"OTHER","citation":"Other"}],[SOURCE],[CLAIM]))[0]
    if family=="review_stale_candidate": return not review_gate({"cycles":[CYCLE],"saturation":SAT},expected_candidate_digest="x"*64)[0]
    if family=="review_short_saturation": return not review_gate({"cycles":[CYCLE],"saturation":{**SAT,"no_novelty_streak":9999}},expected_candidate_digest=CAND)[0]
    if family=="review_degradation_escape": return not review_gate({"cycles":[CYCLE],"saturation":{**SAT,"degradation_escapes":1,"status":"INCOMPLETE"}},expected_candidate_digest=CAND)[0]
    return False


def favorable(family):
    if family=="valid_sim": return validate_simulation_receipt(SIM,candidate_digest=FINAL,generation_contract_digest=CONTRACT,require_categories=True)[0]
    if family=="valid_compression": return compression_valid(COMP,expected_before_digest=CAND,expected_after_digest=FINAL,generation_contract_digest=CONTRACT,strict=True)[0]
    if family=="bibliography_unavailable": return bibliography_gate(assess_bibliography([],[],[]))[0]
    if family=="valid_bibliography": return bibliography_gate(assess_bibliography(BIB,[SOURCE],[CLAIM]))[0]
    if family=="valid_review": return review_gate({"cycles":[CYCLE],"saturation":SAT},expected_candidate_digest=CAND)[0]
    if family=="valid_reticulum": return validate_reticulum(UNITS,RELS,source_ids={"S1","S2"}).status=="PASS"
    if family=="valid_generation": return generation_contract_valid(GEN,RET,SETUP)[0]
    if family=="valid_claim": return validate_claim(CLAIM,[SOURCE],[CLAIM],strict=True)[0]
    if family=="valid_inference_graph": return validate_inference_graph([{"id":"P","claim_type":"direct"},{"id":"I","claim_type":"strong_inference","premise_claim_ids":["P"]}])[0]
    if family=="valid_editorial_style": return STYLE_STABLE_STATUS=="PASS"
    return False


def stress(family, rng):
    size=(16,24,32,48)[rng.randrange(4)]
    if family=="reticulum_scale":
        u,r=base_reticulum(size); a=validate_reticulum(u,r,source_ids={"S1","S2"}); b=validate_reticulum(u,r,source_ids={"S1","S2"}); return a.status=="PASS" and a.digest==b.digest
    if family=="reticulum_corruption_scale":
        u,r=base_reticulum(size); u[-1]=dict(u[-1]); u[-1]["source_locator"]=""; return validate_reticulum(u,r,source_ids={"S1","S2"}).status=="FAIL"
    if family=="bibliography_scale":
        n=size; sources=[{"id":f"S{i}","direct_read":True,"verified_at":"2026-01-01"} for i in range(n)]; claims=[{"id":f"C{i}","material":True,"support_source_ids":[f"S{i}"]} for i in range(n)]; entries=[{"id":f"B{i}","source_id":f"S{i}","citation":f"Autore {i}, Titolo {i}"} for i in range(n)]; return assess_bibliography(entries,sources,claims)["status"]=="PASS"
    if family=="bibliography_duplicate_scale":
        entries=[{"id":f"B{i}","citation":"same citation" if i<2 else f"C{i}"} for i in range(size)]; return assess_bibliography(entries,[],[])["status"]=="GAPS_OPEN"
    if family=="inference_chain_scale":
        claims=[{"id":"C0","claim_type":"direct"}]+[{"id":f"C{i}","claim_type":"strong_inference","premise_claim_ids":[f"C{i-1}"]} for i in range(1,size)]; return validate_inference_graph(claims)[0]
    if family=="inference_cycle_scale":
        claims=[{"id":f"C{i}","claim_type":"strong_inference","premise_claim_ids":[f"C{(i+1)%size}"]} for i in range(size)]; return not validate_inference_graph(claims)[0]
    if family=="review_finding_scale":
        findings=[{"id":f"F{i}","criterion":"STRUCTURE","severity":"MINOR","kind":"density","artifact_locator":f"§{i}","status":"ADDRESSED","proposed_action":"compress"} for i in range(size)]; return build_review_cycle(cycle=1,candidate_digest=CAND,findings=findings,scorecard=SCORE_PASS,evidence=REVIEW_EVIDENCE)["status"]=="PASS_CANDIDATE"
    if family=="review_duplicate_id_scale":
        findings=[{"id":"F","criterion":"STRUCTURE","severity":"MINOR","kind":"density","status":"ADDRESSED"} for _ in range(size)]; return not validate_findings(findings)[0]
    return False


def editorial(family):
    if family=="oversectioning": return STYLE_OVER_STATUS=="REVIEW_REQUIRED"
    if family=="stable_style": return STYLE_STABLE_STATUS=="PASS"
    if family=="missing_review_evidence": return not validate_review_evidence([])[0]
    if family=="missing_score_criterion":
        s=dict(SCORE_PASS); s.pop("LEGAL_AUTHORITY"); return not validate_scorecard(s)[0]
    if family=="major_without_locator":
        f=[{"id":"F1","criterion":"LEGAL_AUTHORITY","severity":"MAJOR","kind":"source","status":"OPEN","proposed_action":"add source"}]; return not validate_findings(f)[0]
    if family=="low_blocking_score":
        s=dict(SCORE_PASS); s["LEGAL_AUTHORITY"]=.70; return build_review_cycle(cycle=1,candidate_digest=CAND,findings=[],scorecard=s,evidence=REVIEW_EVIDENCE)["status"]=="REGENERATE_REQUIRED"
    if family=="low_style_score":
        s=dict(SCORE_PASS); s["EDITORIAL_STYLE"]=.70; return build_review_cycle(cycle=1,candidate_digest=CAND,findings=[],scorecard=s,evidence=REVIEW_EVIDENCE)["status"]=="REVIEW_REQUIRED"
    if family=="open_major":
        f=[{"id":"F1","criterion":"INTERCHAPTER_COHERENCE","severity":"MAJOR","kind":"drift","artifact_locator":"§2","status":"OPEN","proposed_action":"rewrite"}]; return build_review_cycle(cycle=1,candidate_digest=CAND,findings=f,scorecard=SCORE_PASS,evidence=REVIEW_EVIDENCE)["status"]=="REGENERATE_REQUIRED"
    if family=="resolved_minor":
        f=[{"id":"F1","criterion":"STRUCTURE","severity":"MINOR","kind":"density","artifact_locator":"§2","status":"ADDRESSED","proposed_action":"compress"}]; return build_review_cycle(cycle=1,candidate_digest=CAND,findings=f,scorecard=SCORE_PASS,evidence=REVIEW_EVIDENCE)["status"]=="PASS_CANDIDATE"
    return False


def logical(family):
    if family=="missing_locator":
        u=[dict(x) for x in UNITS]; u[0]["source_locator"]=""; return validate_reticulum(u,RELS,source_ids={"S1","S2"}).status=="FAIL"
    if family=="bad_endpoint":
        r=list(RELS)+[{"source":"U0","predicate":"SUPPORTS","target":"MISSING"}]; return validate_reticulum(UNITS,r,source_ids={"S1","S2"}).status=="FAIL"
    if family=="orphan_material":
        u=[dict(x) for x in UNITS]+[{"id":"UX","kind":"RULE","text":"orphan","source_id":"S1","source_locator":"§9","chapter":"1","material":True}]; return validate_reticulum(u,[{"source":"U0","predicate":"SUPPORTS","target":"U1"}],source_ids={"S1","S2"}).status=="FAIL"
    if family=="generation_stale_reticulum": return not generation_contract_valid(GEN,{**RET,"digest":"x"*64},SETUP)[0]
    if family=="generation_stale_setup": return not generation_contract_valid(GEN,RET,{"status":"ACCEPTED","accepted":{"length_words":[1,2]}})[0]
    if family=="strong_inference_no_falsifier":
        p={"id":"P","status":"SUPPORTED","claim_type":"direct"}; i={"id":"I","text":"inf","claim_type":"strong_inference","scope":"s","material":True,"premise_claim_ids":["P"],"inference_bridge":"bridge","falsifier":""}; return not validate_claim(i,[],[p,i],strict=True)[0]
    if family=="inference_cycle": return not validate_inference_graph([{"id":"A","claim_type":"strong_inference","premise_claim_ids":["B"]},{"id":"B","claim_type":"strong_inference","premise_claim_ids":["A"]}])[0]
    if family=="regeneration_loss": return regeneration_record(cycle=1,from_digest="a",to_digest="b",addressed_finding_ids=["F"],preserved_required_unit_ids=["U0"],required_unit_ids=["U0","U1"])["status"]=="REAUDIT_REQUIRED"
    if family=="regeneration_new_material": return regeneration_record(cycle=1,from_digest="a",to_digest="b",addressed_finding_ids=["F"],preserved_required_unit_ids=["U0"],required_unit_ids=["U0"],introduced_material_unit_ids=["NEW"])["status"]=="REAUDIT_REQUIRED"
    if family=="contradiction_visible":
        r=list(RELS)+[{"source":"U0","predicate":"CONTRADICTS","target":"U1"}]; return validate_reticulum(UNITS,r,source_ids={"S1","S2"}).contradiction_relations==1
    return False

FAMILIES={
 "adversarial":["stale_sim_candidate","stale_sim_contract","missing_sim_category","sim_escape","stale_compression_before","compression_no_recheck","bibliography_missing_mapping","review_stale_candidate","review_short_saturation","review_degradation_escape"],
 "favorable":["valid_sim","valid_compression","bibliography_unavailable","valid_bibliography","valid_review","valid_reticulum","valid_generation","valid_claim","valid_inference_graph","valid_editorial_style"],
 "stress":["reticulum_scale","reticulum_corruption_scale","bibliography_scale","bibliography_duplicate_scale","inference_chain_scale","inference_cycle_scale","review_finding_scale","review_duplicate_id_scale"],
 "editorial_review":["oversectioning","stable_style","missing_review_evidence","missing_score_criterion","major_without_locator","low_blocking_score","low_style_score","open_major","resolved_minor"],
 "logical_semantic_review":["missing_locator","bad_endpoint","orphan_material","generation_stale_reticulum","generation_stale_setup","strong_inference_no_falsifier","inference_cycle","regeneration_loss","regeneration_new_material","contradiction_visible"],
}


def evaluate(category,family,rng):
    if category=="adversarial": return adversarial(family)
    if category=="favorable": return favorable(family)
    if category=="stress": return stress(family,rng)
    if category=="editorial_review": return editorial(family)
    return logical(family)


def run(cases:int,seeds:tuple[int,...])->dict:
    if cases%len(CATEGORIES): raise ValueError("case count must be divisible by five categories")
    per=cases//len(CATEGORIES)
    failures=[]; category_counts=Counter(); family_counts=Counter(); seed_counts=Counter(); accepted_controls=0; killed_mutants=0
    for cidx,category in enumerate(CATEGORIES):
        families=FAMILIES[category]
        rngs={seed: random.Random((seed<<20) ^ (cidx*2654435761)) for seed in seeds}
        for j in range(per):
            seed=seeds[(j+cidx)%len(seeds)]; seed_counts[str(seed)]+=1
            rng=rngs[seed]
            family=families[rng.randrange(len(families))]
            ok=False
            try: ok=bool(evaluate(category,family,rng))
            except Exception as exc:
                if len(failures)<100: failures.append({"category":category,"family":family,"index":j,"seed":seed,"error":type(exc).__name__+": "+str(exc)})
            category_counts[category]+=1; family_counts[f"{category}:{family}"]+=1
            if ok:
                if category=="favorable": accepted_controls+=1
                else: killed_mutants+=1
            elif len(failures)<100:
                failures.append({"category":category,"family":family,"index":j,"seed":seed,"error":"unexpected outcome"})
    scenario_basis={"cases":cases,"seeds":list(seeds),"criteria":CRITERIA,"families":FAMILIES,"category_counts":dict(category_counts),"family_counts":dict(sorted(family_counts.items()))}
    scenario_digest=hashlib.sha256(json.dumps(scenario_basis,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    result={
      "schema":"juriscribe-validation/simulation-v5","requested":cases,"executed":cases,
      "categories":dict(category_counts),"criteria":CRITERIA,"families":FAMILIES,
      "family_counts":dict(sorted(family_counts.items())),"seeds":list(seeds),"seed_case_counts":dict(seed_counts),
      "killed_mutants":killed_mutants,"accepted_controls":accepted_controls,
      "failures":failures,"escapes":len(failures),"false_positives":0 if not failures else sum(1 for f in failures if f["category"]=="favorable"),
      "scenario_digest":scenario_digest,"passed":not failures,
      "interpretation":"property/mutation/stress evidence over runtime gates; not 400,000 substantive legal judgments or LLM calls",
    }
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument("--cases",type=int,default=400000); p.add_argument("--seeds",default=",".join(map(str,DEFAULT_SEEDS))); p.add_argument("--json-out")
    a=p.parse_args(); seeds=tuple(int(x) for x in a.seeds.split(",") if x.strip()); r=run(a.cases,seeds); text=json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)
    if a.json_out: Path(a.json_out).write_text(text+"\n",encoding="utf-8")
    print(text); return 0 if r["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
