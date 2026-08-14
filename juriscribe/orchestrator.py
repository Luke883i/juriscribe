from __future__ import annotations
from typing import Any
from .convergence import completion_gate
from .mining import deep_mine
from .quality import audit_chapter
from .reticulum import build_generation_contract,validate_reticulum
from .setup import accept_setup,parameter_dods,propose_setup
from .sources import research_plan,validate_claim,validate_inference_graph

def ingest_and_mine(state,text,*,source_id,chapter=None,source_record=None):
    state.mining=deep_mine(text,source_id=source_id,chapter=chapter)
    state.style_profile=dict(state.mining.get('style',{}))
    if source_record:
        state.sources=[s for s in state.sources if s.get('id')!=source_id]+[dict(source_record)]
    elif not any(s.get('id')==source_id for s in state.sources):
        state.sources.append({'id':source_id,'title':chapter or source_id,'source_type':'corpus_chapter','role':'preceding_chapter','direct_read':True,'verified_at':state.updated_at})
    state.corpus=[c for c in state.corpus if c.get('source_id')!=source_id]+[{'source_id':source_id,'chapter':chapter,'role':'preceding_chapter','word_count':state.mining.get('surface',{}).get('word_count',0)}]
    state.phase='SEMANTIC_MINING_REQUIRED'
    return state

def register_semantic_mining(state,units:list[dict[str,Any]],relations:list[dict[str,Any]]):
    source_ids={s.get('id') for s in state.sources if s.get('id')}
    report=validate_reticulum(units,relations,source_ids=source_ids)
    state.epistemic_units=list(units); state.relations=list(relations); state.reticulum=report.record()
    if report.status!='PASS': state.phase='RETICULUM_INVALID'; return state.reticulum
    state.setup=propose_setup(state.mining,state.request,reticulum=state.reticulum); state.phase='USER_SETUP_REQUIRED'; return state.reticulum

def mine_and_prepare(state,text,*,source_id,chapter=None,semantic_annotations=None):
    """Compatibility wrapper: semantic annotations must contain units+relations to reach setup."""
    ingest_and_mine(state,text,source_id=source_id,chapter=chapter)
    if semantic_annotations:
        register_semantic_mining(state,semantic_annotations.get('units',[]),semantic_annotations.get('relations',[]))
    return state

def apply_setup(state,overrides=None):
    if state.setup.get('status')!='USER_SETUP_REQUIRED': raise ValueError('setup proposal is not ready; validated reticulum required first')
    state.setup=accept_setup(state.setup,overrides); existing=[d for d in state.dod if d.get('kind')!='USER_PARAMETER']; state.dod=existing+parameter_dods(state.setup); state.phase='DOD_DEFINITION'; return state

def freeze_dods(state,additional_dods=None):
    if state.setup.get('status')!='ACCEPTED': raise ValueError('user setup must be accepted before DoD freeze')
    for dod in additional_dods or []:
        if not dod.get('id'): raise ValueError('DoD requires id')
        dod.setdefault('status','OPEN'); dod.setdefault('blocking',True); dod.setdefault('evidence',[]); state.dod.append(dod)
    state.generation_contract=build_generation_contract(state.reticulum,state.setup,state.epistemic_units,state.relations)
    state.phase='DOD_FROZEN'; return state

def build_research_plan(state):
    state.source_intelligence['research_plan']=research_plan(state.claim_ledger); state.source_intelligence['coverage_status']='PLANNED' if state.source_intelligence['research_plan'] else 'NOT_REQUIRED'; return state

def validate_claim_ledger(state):
    errors={}
    graph_ok,graph_errors=validate_inference_graph(state.claim_ledger)
    if not graph_ok: errors['INFERENCE_GRAPH']=graph_errors
    for claim in state.claim_ledger:
        ok,es=validate_claim(claim,state.sources,state.claim_ledger,strict=True)
        if not ok: errors[claim.get('id','UNKNOWN')]=es
    state.source_intelligence['coverage_status']='PASS' if not errors else 'GAPS_OPEN'; return errors

def record_simulation(state,receipt):
    state.simulations=dict(receipt); state.metrics['simulations_run']=int(receipt.get('cases',0)); state.metrics['simulation_failures']=int(receipt.get('failures',0)); state.phase='SIMULATED'; return state

def record_compression(state,record): state.compression=dict(record); state.phase='COMPRESSED'; return state

def audit_candidate_chapter(state,text,*,reference_text=None,prior_texts=None,artifact_evidence=None):
    if state.generation_contract.get('status')!='READY': raise ValueError('generation contract not READY')
    if artifact_evidence is not None: state.artifact_evidence=list(artifact_evidence)
    report=audit_chapter(text,reference_text=reference_text,prior_texts=prior_texts,accepted_setup=state.setup,claims=state.claim_ledger,sources=state.sources,artifact_evidence=state.artifact_evidence)
    state.quality=report.record(); state.phase='QUALITY_AUDIT'; return state.quality

def evaluate_completion(state):
    benchmark_required=any(d.get('kind')=='MONOGRAPHIC_EXTRAPOLATION' and d.get('blocking',True) for d in state.dod)
    state.completion=completion_gate(state.dod,state.metrics,state.contradictions,quality=state.quality or None,source_coverage=state.source_intelligence.get('coverage_status'),benchmark=state.benchmark or None,benchmark_required=benchmark_required,artifacts=state.artifacts,generation_required=True,reticulum=state.reticulum,generation_contract=state.generation_contract,simulation=state.simulations,compression=state.compression,setup=state.setup,admission=state.admission)
    state.phase='COMPLETE' if state.completion['eligible'] else 'VALIDATING'; return state
