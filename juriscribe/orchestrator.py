"""Public orchestration facade.

v0.11 adds Compression & Consolidation as an isolated overlay while preserving the
historical continuation/greenfield/review paths. C&C overlays are imported last.
"""
from .orchestrator_base import *  # noqa: F401,F403
from .finalization import evaluate_completion, record_artifact, record_compression, record_final_review, record_provenance, seal_draft
from .multimode import apply_setup, audit_candidate_chapter, audit_legal_text, evaluate_completion, freeze_dods, ingest_and_mine, record_artifact, record_compression, record_continuation_coverage, record_final_review, record_provenance, record_regeneration, record_review_cycle, record_review_saturation, record_simulation, register_continuation_plan, register_semantic_mining, seal_draft, select_mode
from .delivery import evaluate_completion, record_artifact
from .semantic_delivery import evaluate_completion, record_artifact
from .generation_governance import audit_candidate_chapter, audit_legal_text, ingest_and_mine, record_final_review, record_provenance, register_plagiarism_reference, register_semantic_mining
from .artifact_governance import apply_setup, freeze_dods, record_artifact, seal_draft
from .governance_delivery import evaluate_completion
from .runtime_autopilot import apply_setup, freeze_dods, record_artifact, record_natural_language_interpretation, resolve_natural_language_interpretation, seal_draft, select_mode
from .runtime_v11 import apply_setup, calibrate_refactoring, consolidation_gate, freeze_dods, ingest_and_mine, record_consolidation_saturation, record_simulation, register_refactoring_plan, register_semantic_mining, seal_refined_candidate, select_mode
from .runtime_v11_review import record_final_review, record_provenance, record_review_cycle
from .consolidation_completion import evaluate_completion
# Contract-check markers:
# bootstrap_required=True finalization_required=True trimode_required=True editorial_standard_required=True
# compression_consolidation_mode_required=True lossless_inventory_required=True joint_reticulum_required=True
# ten_million_mutations_required=True dual_saturation_required=True user_calibration_required=True
# minimal_surgical_refactoring_required=True canonical_immutability_required=True refined_candidate_cardinality_required=True
# peer_review_readiness_required=True consolidation_provenance_required=True consolidation_final_review_required=True
# atomic_consolidation_delivery_required=True
# delivery_boundary_required=True docx_final_documents_required=True dashboard_attachment_required=False
# natural_language_pipeline_lock_required=True standard_artifact_autopilot_required=True
