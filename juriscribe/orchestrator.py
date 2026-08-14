from __future__ import annotations
from typing import Any
from .convergence import completion_gate
from .mining import deep_mine
from .quality import audit_chapter
from .setup import propose_setup,accept_setup,parameter_dods
from .sources import validate_claim,research_plan

def mine_and_prepare(state,text,*,source_id,chapter=None,semantic_annotations=None):
    state.mining=deep_mine(text,source_id=source_id,chapter=chapter,semantic_annotations=semantic_annotations); state.style_profile=dict(state.mining.get('style',{})); state.setup=propose_setup(state.mining,state.request); state.phase='USER_SETUP_REQUIRED'; return state

def apply_setup(state,overrides=None):
    if state.setup.get('status')!='USER_SETUP_REQUIRED': raise ValueError('setup proposal is not ready')
    state.setup=accept_setup(state.setup,overrides); existing=[d for d in state.dod if d.get('kind')!='USER_PARAMETER']; state.dod=existing+parameter_dods(state.setup); state.phase='DOD_DEFINITION'; return state

def freeze_dods(state,additional_dods=None):
    if state.setup.get('status')!='ACCEPTED': raise ValueError('user setup must be accepted before DoD freeze')
    for dod in additional_dods or []:
        if not dod.get('id'): raise ValueError('DoD requires id')
        dod.setdefault('status','OPEN'); dod.setdefault('blocking',True); dod.setdefault('evidence',[]); state.dod.append(dod)
    state.phase='DOD_FROZEN'; return state

def build_research_plan(state):
    state.source_intelligence['research_plan']=research_plan(state.claim_ledger); state.source_intelligence['coverage_status']='PLANNED' if state.source_intelligence['research_plan'] else 'NOT_REQUIRED'; return state

def validate_claim_ledger(state):
    errors={}
    for claim in state.claim_ledger:
        ok,es=validate_claim(claim,state.sources,state.claim_ledger)
        if not ok: errors[claim.get('id','UNKNOWN')]=es
    state.source_intelligence['coverage_status']='PASS' if not errors else 'GAPS_OPEN'; return errors

def audit_candidate_chapter(state,text,*,reference_text=None,artifact_evidence=None):
    if artifact_evidence is not None: state.artifact_evidence=list(artifact_evidence)
    report=audit_chapter(text,reference_text=reference_text,accepted_setup=state.setup,claims=state.claim_ledger,sources=state.sources,artifact_evidence=state.artifact_evidence)
    state.quality=report.record(); state.phase='QUALITY_AUDIT'; return state.quality

def evaluate_completion(state):
    benchmark_required=any(d.get('kind')=='MONOGRAPHIC_EXTRAPOLATION' and d.get('blocking',True) for d in state.dod)
    state.completion=completion_gate(state.dod,state.metrics,state.contradictions,quality=state.quality or None,source_coverage=state.source_intelligence.get('coverage_status'),benchmark=state.benchmark or None,benchmark_required=benchmark_required,artifacts=state.artifacts)
    state.phase='COMPLETE' if state.completion['eligible'] else 'VALIDATING'; return state
