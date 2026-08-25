"""C&C artifact-atlas extension without duplicating the atlas renderer."""
from . import artifact_atlas_core as _atlas

_atlas.ROLE_META.update({
    "refactoring_report": ("Relazione di rifattorizzazione", "Analisi olistica della traiettoria minimale di Compression & Consolidation, con gap, mutazioni, saturazione, calibrazione e readiness."),
    "refined_candidate": ("Candidato raffinato", "Materiale candidato rifattorizzato chirurgicamente e preservato rispetto al reticolo semantico, pronto per peer review."),
})
_atlas.ROLE_ANCHORS.update({
    "refactoring_report": "#artifact-atlas",
    "refined_candidate": "#artifact-atlas",
})
