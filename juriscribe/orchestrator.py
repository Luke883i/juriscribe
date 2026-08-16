"""Public orchestration facade.

v0.9 keeps continuation-era primitives available for compatibility, then replaces lifecycle entry points with the tri-mode dispatcher.
"""
from .orchestrator_base import *  # noqa: F401,F403
from .finalization import evaluate_completion, record_artifact, record_compression, record_final_review, record_provenance, seal_draft
from .multimode import apply_setup, audit_candidate_chapter, audit_legal_text, evaluate_completion, freeze_dods, ingest_and_mine, record_artifact, record_compression, record_continuation_coverage, record_final_review, record_provenance, record_regeneration, record_review_cycle, record_review_saturation, record_simulation, register_continuation_plan, register_semantic_mining, seal_draft, select_mode
# Contract-check markers:
# bootstrap_required=True finalization_required=True trimode_required=True editorial_standard_required=True
