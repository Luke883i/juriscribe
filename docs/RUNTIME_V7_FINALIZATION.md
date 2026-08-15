# Juriscribe runtime v0.7 — bootstrap, provenance e finalizzazione

## Novità ad alta leva

### Bootstrap fail-closed visibile

Il bootstrap è una state machine osservabile: T&C → acceptance → probe → probe receipt → initialize → ACTIVE. `initialize()` non esegue più il probe implicitamente. Web browsing o discovery del repository non autorizzano la lettura sostanziale.

### Interaction cards

Ogni fase espone scelte standard stabili ma conserva sempre `ALTRO` e input libero. Le card sono auditabili e digestate, non un sostituto della conversazione.

### Provenance lossless

Prima della final review il runtime materializza un provenance bundle candidato/corpus-bound. Tutte le inferenze materiali registrate, i claim materiali, le decisioni utente e le trasformazioni richieste devono avere una disposizione finale. `IN_FINAL` richiede locator nell'artefatto; inferenze e claim richiedono evidenze.

### Review finale severa

Dopo compressione + final recheck + continuation coverage, e prima degli artefatti, un secondo gate controlla nove assi: quadro normativo globale, seed, autorità, conseguenze, controautorità, integrità editoriale, provenance, tempo/giurisdizione e losslessness. Almeno un consequence probe è obbligatorio.

### Set artefatti finale

Il completion gate richiede i ruoli: final chapter, evidence dossier, source register, inference register, transformation ledger e dashboard. Tutti devono avere readback PASS.

### Dashboard

La dashboard usa progressiva disclosure: prossimo passo e blocker prima; poi controlli; poi evidenze granulari; infine storia delle revisioni e integrità tecnica.
