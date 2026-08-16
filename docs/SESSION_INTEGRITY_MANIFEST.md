# `session.integrity.json` — canonical session integrity v2

Dalla v0.9 è l'unico record di integrità richiesto. Contiene metadata e digest, non corpus text né chain-of-thought.

La v2 lega anche `mode`, `mode_selection`, `mode_contract` e `editorial_standard`, oltre a corpus, fonti, claim, reticolo, setup, DoD, contratti, candidato/target, review, provenance, final review, simulazioni/compressione quando applicabili e artifact registry.

Il validator ricalcola deterministicamente i binding contro `state.json` e rileva missing field, stale state, tampering e campi inattesi.

`node.h` non viene più generato. Un vecchio `node.h` può essere letto una sola volta per migrare un workspace storico privo di `session.integrity.json`.
