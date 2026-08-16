"""Public orchestration facade.

v0.9 keeps continuation-era primitives available for compatibility and routes the
lifecycle through the tri-mode dispatcher. v0.9.1 applies the final-delivery
boundary last; v0.9.2 hardens that boundary with real materialization and
state-bound dashboard verification. v0.9.4 adds a legal-humanistic semantic
projection boundary after delivery so dossier freshness cannot be bypassed.
v0.9.6 extends that boundary with lossless artifact-evidence traceability. v0.9.7
adds a user-bound generation configuration, deterministic anti-plagiarism proof,
and cyclic predelivery saturation as the final runtime governance boundary.
"""
from .orchestrator_base import *  # noqa: F401,F403
from .finalization import evaluate_completion, record_artifact, record_compression, record_final_review, record_provenance, seal_draft
from .multimode import apply_setup, audit_candidate_chapter, audit_legal_text, evaluate_completion, freeze_dods, ingest_and_mine, record_artifact, record_compression, record_continuation_coverage, record_final_review, record_provenance, record_regeneration, record_review_cycle, record_review_saturation, record_simulation, register_continuation_plan, register_semantic_mining, seal_draft, select_mode
from .delivery import evaluate_completion, record_artifact
from .semantic_delivery import evaluate_completion, record_artifact
from .generation_governance import (
    apply_setup,
    audit_candidate_chapter,
    audit_legal_text,
    evaluate_completion,
    freeze_dods,
    ingest_and_mine,
    record_artifact,
    record_final_review,
    record_provenance,
    register_plagiarism_reference,
    register_semantic_mining,
    seal_draft,
)
# Contract-check markers:
# bootstrap_required=True finalization_required=True trimode_required=True editorial_standard_required=True
# delivery_boundary_required=True docx_final_documents_required=True dashboard_attachment_required=True
# materialized_delivery_required=True dashboard_state_binding_required=True artifact_first_surface_required=True
# legal_humanistic_projection_required=True semantic_dossier_freshness_required=True dashboard_inference_only=True
# evidence_traceability_required=True dashboard_artifact_recall_required=True dashboard_compressed_outcome_required=True
# generation_configuration_required=True anti_plagiarism_required=True predelivery_saturation_required=True
