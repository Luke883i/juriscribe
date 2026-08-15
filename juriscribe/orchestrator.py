"""Public orchestration facade.

v0.6 lifecycle stays byte-identical in orchestrator_base; v0.7 finalization overrides
only the state transitions that need bootstrap/provenance/final-review enforcement.
"""
from .orchestrator_base import *  # noqa: F401,F403
from .finalization import (
    evaluate_completion,
    record_artifact,
    record_compression,
    record_final_review,
    record_provenance,
    seal_draft,
)

# Contract-check markers: finalization_required=True bootstrap_required=True
