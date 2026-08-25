from __future__ import annotations
from . import multimode as _legacy
from .consolidation_review import record_peer_review_readiness, record_consolidation_provenance, record_consolidation_final_review
from .modes import COMPRESSION_CONSOLIDATION, normalize_mode

def record_review_cycle(state, record):
    if normalize_mode(state.mode)==COMPRESSION_CONSOLIDATION: return record_peer_review_readiness(state,record)
    return _legacy.record_review_cycle(state,record)

def record_provenance(state, payload):
    if normalize_mode(state.mode)==COMPRESSION_CONSOLIDATION: return record_consolidation_provenance(state,payload)
    return _legacy.record_provenance(state,payload)

def record_final_review(state, payload):
    if normalize_mode(state.mode)==COMPRESSION_CONSOLIDATION: return record_consolidation_final_review(state,payload)
    return _legacy.record_final_review(state,payload)
