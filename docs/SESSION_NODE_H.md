# `node.h` — session integrity header v3

Ogni workspace persistente Juriscribe genera `.juriscribe/<session-id>/node.h` a ogni salvataggio.

L'header contiene **solo metadata e digest**, mai il testo del corpus o chain-of-thought. Serve a rilevare stato stale/tampered fra pipeline e artefatti.

v3 include i digest di:

- corpus, fonti e claim ledger;
- reticolo epistemico;
- setup e DoD;
- generation contract;
- **continuation plan + coverage**;
- candidato corrente;
- review/rigenerazioni;
- bibliografia;
- simulazioni e compressione;
- quality/benchmark/artefatti;
- readiness finale.

La macro aggiunta in v3 è `JURISCRIBE_CONTINUATION_SHA256`. Il validator ricalcola i valori dallo `state.json`: un header non coerente non può sostenere `COMPLETE`.
