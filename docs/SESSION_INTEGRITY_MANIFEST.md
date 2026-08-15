# `session.integrity.json` — manifest canonico di integrità

Da runtime v0.8 ogni workspace persistente materializza:

```text
.juriscribe/<session-id>/session.integrity.json
```

Il file è il record canonico machine-readable dell'integrità della sessione. È JSON deterministico, privo di timestamp volatili e privo di testo del corpus.

## Struttura

```json
{
  "schema": "juriscribe-session-integrity/v1",
  "kind": "session_integrity_manifest",
  "bindings": {
    "session_id": "…",
    "phase": "…",
    "ready": false,
    "corpus_sha256": "…"
  },
  "paths": {
    "state": "state.json",
    "ledger": "ledger",
    "artifacts": "artifacts"
  },
  "legacy_projection": {
    "path": "node.h",
    "format": "c-preprocessor-header",
    "status": "DEPRECATED_COMPATIBILITY"
  }
}
```

I `bindings` coprono lo stesso stato materiale protetto storicamente dal legacy header: corpus, fonti, claim, source intelligence, reticolo, setup, DoD, generation contract, continuation, candidato, review, final review, provenance, interaction, bootstrap, bibliografia, simulazioni, compressione, qualità, benchmark e artefatti.

## Proprietà

- **deterministico**: a parità di stato materiale produce lo stesso record;
- **fail-closed**: field missing, field extra o digest diverso rendono il manifest invalido;
- **corpus-free**: registra digest, non testo giuridico;
- **human-inspectable**: JSON esplicito anziché macro C;
- **migration-aware**: `node.h` resta proiezione legacy finché il contratto 1.5.0 la nomina.

Il completion gate v0.8 verifica sia il manifest canonico sia il legacy `node.h`, così un tampering su uno dei due non passa silenziosamente.
