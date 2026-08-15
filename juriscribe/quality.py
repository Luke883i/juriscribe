from __future__ import annotations

import math,re
from dataclasses import asdict,dataclass
from typing import Any
from .generation import text_digest
from .mining import ARGUMENT_MARKERS,WORD_RE,SENTENCE_RE
from .sources import validate_claim,validate_inference_graph

APPARATUS_MARKERS=("Fonti verificate del capitolo","Bibliografia","Riferimenti bibliografici","References")
HEADING_RE=re.compile(r"^(?:CAPITOLO\s+\d+|\d+(?:\.\d+)+\s+)",re.IGNORECASE)
NOTE_LINE_RE=re.compile(r"^(\d{1,3})\.\s+(.+)$")
TRAILING_NOTE_RE=re.compile(r"(?<=[.!?])\s+(\d{1,3})(?=\s|$)")

def split_document_regions(text):
    best=None
    for marker in APPARATUS_MARKERS:
        idx=text.find(marker)
        if idx>=0 and (best is None or idx<best[0]): best=(idx,marker)
    if best is None:return text,"",None
    idx,marker=best; return text[:idx].rstrip(),text[idx:].lstrip(),marker

def _words(text): return WORD_RE.findall(text or "")
def _sentences(text): return [s.strip() for s in SENTENCE_RE.split((text or "").strip()) if s.strip()]
def _headings(text): return [line.strip() for line in text.splitlines() if HEADING_RE.match(line.strip())]
def _density(n,w): return n*1000/max(w,1)
def _relative_delta(cur,ref,floor=1.0): return abs(cur-ref)/max(abs(ref),floor)
def _connector_set(text):
    lower=text.lower(); out=set()
    for markers in ARGUMENT_MARKERS.values():
        for marker in markers:
            if marker in lower: out.add(marker)
    return out
def _jaccard(a,b): return 0.0 if not a and not b else 1-len(a&b)/max(len(a|b),1)

def style_profile(text):
    body,_,_=split_document_regions(text); words=_words(body); sentences=_sentences(body); lengths=[len(_words(s)) for s in sentences]; ordered=sorted(lengths); p90=float(ordered[min(len(ordered)-1,max(0,math.ceil(.9*len(ordered))-1))]) if ordered else 0.0; headings=_headings(body)
    return {"word_count":len(words),"sentence_count":len(sentences),"heading_count":len(headings),"avg_sentence_words":round(sum(lengths)/len(lengths),2) if lengths else 0.0,"p90_sentence_words":p90,"heading_density_per_1000_words":round(_density(len(headings),len(words)),3),"semicolon_density_per_1000_words":round(_density(body.count(';'),len(words)),3),"colon_density_per_1000_words":round(_density(body.count(':'),len(words)),3),"connectors":sorted(_connector_set(body)),"headings":headings}

def compare_editorial_style(reference_text,candidate_text):
    ref=style_profile(reference_text); cur=style_profile(candidate_text); deltas={"avg_sentence_words":round(_relative_delta(cur["avg_sentence_words"],ref["avg_sentence_words"]),4),"p90_sentence_words":round(_relative_delta(cur["p90_sentence_words"],ref["p90_sentence_words"]),4),"heading_density":round(_relative_delta(cur["heading_density_per_1000_words"],ref["heading_density_per_1000_words"],.25),4),"semicolon_density":round(_relative_delta(cur["semicolon_density_per_1000_words"],ref["semicolon_density_per_1000_words"],.5),4),"colon_density":round(_relative_delta(cur["colon_density_per_1000_words"],ref["colon_density_per_1000_words"],.5),4),"connector_distance":round(_jaccard(set(ref["connectors"]),set(cur["connectors"])),4)}
    checks=[{"id":"STYLE-SENTENCE-MEAN","status":"PASS" if deltas["avg_sentence_words"]<=.25 else "REVIEW","value":deltas["avg_sentence_words"]},{"id":"STYLE-SENTENCE-P90","status":"PASS" if deltas["p90_sentence_words"]<=.30 else "REVIEW","value":deltas["p90_sentence_words"]},{"id":"STYLE-SECTIONING","status":"PASS" if deltas["heading_density"]<=.75 else "REVIEW","value":deltas["heading_density"]},{"id":"STYLE-CONNECTORS","status":"PASS" if deltas["connector_distance"]<=.65 else "REVIEW","value":deltas["connector_distance"]}]
    return {"reference":ref,"candidate":cur,"deltas":deltas,"checks":checks,"status":"PASS" if all(c["status"]=="PASS" for c in checks) else "REVIEW_REQUIRED"}

def analyze_reference_apparatus(text):
    body,apparatus,marker=split_document_regions(text); declared={}
    for line in apparatus.splitlines():
        m=NOTE_LINE_RE.match(line.strip())
        if m: declared[int(m.group(1))]=m.group(2).strip()
    used=[]
    for line in body.splitlines():
        for raw in TRAILING_NOTE_RE.findall(line):
            n=int(raw)
            if n in declared: used.append(n)
    unique=sorted(set(used)); unused=sorted(set(declared)-set(unique)); missing=sorted(set(unique)-set(declared))
    return {"marker":marker,"declared_source_count":len(declared),"used_source_count":len(unique),"callout_count":len(used),"coverage":round(len(unique)/max(len(declared),1),4) if declared else 0.0,"unused_source_numbers":unused,"missing_source_numbers":missing,"status":"PASS" if declared and not unused and not missing else "REVIEW_REQUIRED"}

def claim_traceability(claims,sources,artifact_evidence):
    source_ids={s.get("id") for s in sources}; grouped={}
    for e in artifact_evidence:
        if e.get("claim_id"): grouped.setdefault(e.get("claim_id"),[]).append(e)
    material=[c for c in claims if c.get("material",True)]; errors={}; visible=0
    graph_ok,graph_errors=validate_inference_graph(claims)
    if not graph_ok: errors["INFERENCE_GRAPH"]=graph_errors
    for claim in material:
        cid=claim.get("id","UNKNOWN"); _,es=validate_claim(claim,sources,claims,strict=True); records=grouped.get(cid,[])
        if not records: es.append("material claim has no artifact locator")
        else:
            locators=[str(e.get("artifact_locator","")).strip() for e in records if str(e.get("artifact_locator","")).strip()]
            if not locators: es.append("artifact locator is empty")
            ev_sources=set().union(*(set(e.get("source_ids",[])) for e in records)) if records else set()
            if any(sid not in source_ids for sid in ev_sources): es.append("artifact evidence references unknown source")
            missing_support=set(claim.get("support_source_ids",[]))-ev_sources
            if missing_support: es.append("artifact evidence does not expose all supporting sources: "+", ".join(sorted(missing_support)))
            if locators and not es: visible+=1
        if es: errors[cid]=es
    return {"material_claims":len(material),"fully_traceable_claims":visible,"coverage":round(visible/max(len(material),1),4) if material else 1.0,"errors":errors,"status":"PASS" if not errors else "GAPS_OPEN"}

def cross_chapter_duplication(candidate_text:str, prior_texts:list[str]|None)->dict[str,Any]:
    if not prior_texts:return {"status":"NOT_EVALUATED","candidate_paragraphs":0,"near_duplicates":[]}
    paras=[p.strip() for p in re.split(r"\n\s*\n",split_document_regions(candidate_text)[0]) if len(_words(p))>=20]; prior=[p.strip() for t in prior_texts for p in re.split(r"\n\s*\n",split_document_regions(t)[0]) if len(_words(p))>=20]; dup=[]
    for i,p in enumerate(paras,1):
        ps=set(w.lower() for w in _words(p))
        for j,q in enumerate(prior,1):
            qs=set(w.lower() for w in _words(q)); score=len(ps&qs)/max(len(ps|qs),1)
            if score>=.72: dup.append({"candidate_paragraph":i,"prior_paragraph":j,"similarity":round(score,4)}); break
    return {"status":"PASS" if not dup else "REVIEW_REQUIRED","candidate_paragraphs":len(paras),"near_duplicates":dup}

@dataclass(frozen=True)
class ChapterQualityReport:
    status:str; candidate_digest:str; blocking_failures:list[str]; review_items:list[str]; body_word_count:int; apparatus_word_count:int; length_status:str; style:dict[str,Any]; reference_apparatus:dict[str,Any]; claim_traceability:dict[str,Any]; cross_chapter_duplication:dict[str,Any]; notes:list[str]
    def record(self): return asdict(self)

def audit_chapter(text,*,reference_text=None,prior_texts=None,accepted_setup=None,claims=None,sources=None,artifact_evidence=None):
    body,apparatus,_=split_document_regions(text); bw=len(_words(body)); aw=len(_words(apparatus)); setup=(accepted_setup or {}).get("accepted",accepted_setup or {}); expected=setup.get("length_words"); length_status="NOT_CONSTRAINED"; blocking=[]; review=[]; notes=[]
    if isinstance(expected,(list,tuple)) and len(expected)==2:
        lo,hi=map(int,expected); length_status="PASS" if lo<=bw<=hi else "FAIL"
        if length_status=="FAIL": blocking.append(f"body length {bw} outside accepted range {lo}-{hi}")
    style=compare_editorial_style(reference_text,body) if reference_text else {"status":"NOT_EVALUATED","checks":[]}
    if style.get("status")=="REVIEW_REQUIRED": review.append("style continuity requires editorial review")
    app=analyze_reference_apparatus(text)
    if app["status"]=="PASS": notes.append("source apparatus is visible and internally referenced")
    elif app["declared_source_count"]: review.append("source apparatus has unused or unresolved references")
    trace=claim_traceability(claims or [],sources or [],artifact_evidence or []) if claims is not None else {"status":"NOT_EVALUATED","coverage":None,"errors":{}}
    if trace.get("status")=="GAPS_OPEN": blocking.append("material claim-to-source-to-artifact traceability is incomplete")
    duplication=cross_chapter_duplication(text,prior_texts)
    if duplication.get("status")=="REVIEW_REQUIRED": review.append("cross-chapter near-duplication requires review")
    status="FAIL" if blocking else ("REVIEW_REQUIRED" if review else "PASS")
    return ChapterQualityReport(status,text_digest(text),blocking,review,bw,aw,length_status,style,app,trace,duplication,notes)
