"""Public orchestration facade with explicit runtime composition.

Historical specialist engines remain authoritative for their proof semantics. v1
adds recovery export only as an explicit MATERIALIZATION route; recovery resume
continues to reuse bootstrap/session persistence rather than becoming proof authority.
"""
from .orchestrator_base import *  # noqa: F401,F403
from .runtime_router import resolve_operation, routing_manifest

apply_setup = resolve_operation("apply_setup")
audit_candidate_chapter = resolve_operation("audit_candidate_chapter")
audit_legal_text = resolve_operation("audit_legal_text")
create_recovery_bundle = resolve_operation("create_recovery_bundle")
evaluate_completion = resolve_operation("evaluate_completion")
freeze_dods = resolve_operation("freeze_dods")
ingest_and_mine = resolve_operation("ingest_and_mine")
record_artifact = resolve_operation("record_artifact")
record_compression = resolve_operation("record_compression")
record_continuation_coverage = resolve_operation("record_continuation_coverage")
record_final_review = resolve_operation("record_final_review")
record_natural_language_interpretation = resolve_operation("record_natural_language_interpretation")
record_provenance = resolve_operation("record_provenance")
record_regeneration = resolve_operation("record_regeneration")
record_review_cycle = resolve_operation("record_review_cycle")
record_review_saturation = resolve_operation("record_review_saturation")
record_simulation = resolve_operation("record_simulation")
register_continuation_plan = resolve_operation("register_continuation_plan")
register_plagiarism_reference = resolve_operation("register_plagiarism_reference")
register_semantic_mining = resolve_operation("register_semantic_mining")
resolve_natural_language_interpretation = resolve_operation("resolve_natural_language_interpretation")
seal_draft = resolve_operation("seal_draft")
select_mode = resolve_operation("select_mode")

calibrate_refactoring = resolve_operation("calibrate_refactoring")
consolidation_gate = resolve_operation("consolidation_gate")
record_consolidation_saturation = resolve_operation("record_consolidation_saturation")
register_refactoring_plan = resolve_operation("register_refactoring_plan")
seal_refined_candidate = resolve_operation("seal_refined_candidate")

RUNTIME_ROUTING_MANIFEST = routing_manifest()

# Contract-check markers retained from all historical runtime layers:
# bootstrap_required=True finalization_required=True trimode_required=True editorial_standard_required=True
# delivery_boundary_required=True docx_final_documents_required=True dashboard_attachment_required=False
# dashboard_summary_surface_only=True chat_tail_docx_attachments_required=True
# materialized_delivery_required=True dashboard_state_binding_required=True artifact_first_surface_required=True
# legal_humanistic_projection_required=True semantic_dossier_freshness_required=True dashboard_inference_only=True
# evidence_traceability_required=True dashboard_artifact_recall_required=False dashboard_compressed_outcome_required=True
# generation_configuration_required=True anti_plagiarism_required=True predelivery_saturation_required=True
# artifact_atlas_required=True dashboard_complete_artifact_description_required=True
# materialized_narrative_antiplagiarism_required=True sealed_candidate_artifact_binding_required=True
# natural_language_pipeline_lock_required=True implicit_mode_change_forbidden=True
# standard_artifact_autopilot_required=True final_chapter_inference_trace_required=True
# mechanical_delivery_compliance_required=True atomic_attachment_release_required=True
# compression_consolidation_mode_required=True lossless_inventory_required=True joint_reticulum_required=True
# ten_million_mutations_required=True dual_saturation_required=True user_calibration_required=True
# minimal_surgical_refactoring_required=True canonical_immutability_required=True refined_candidate_cardinality_required=True
# peer_review_readiness_required=True consolidation_provenance_required=True consolidation_final_review_required=True
# atomic_consolidation_delivery_required=True dynamic_mode_discovery_required=True
# proof_carrying_semantics_required=True structural_substantive_claim_separation_required=True
# executable_editorial_reticulum_required=True seeded_editorial_mutation_stress_required=True
# authorized_merge_split_reorder_required=True a_level_editorial_readiness_not_journal_acceptance=True
# explicit_runtime_routing_required=True common_mode_registry_required=True
# scientific_checkpoint_required=True portable_recovery_bundle_required=True
# recovery_fresh_probe_required=True iteration_where_done_next_how_do_required=True
