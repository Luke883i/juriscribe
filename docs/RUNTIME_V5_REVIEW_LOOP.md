# Runtime v0.5 — review, regeneration and evidence binding

## Gap osservati in v0.4

L'audit della baseline PR4 ha mostrato che il reticolo e i gate di evidenza erano già forti, ma mancavano quattro proprietà necessarie per il ciclo editoriale richiesto:

1. il completion gate non richiedeva una review scientifico-editoriale post-bozza;
2. simulation receipt e compression receipt non erano legate al digest del candidato effettivamente valutato;
3. bibliografia non era stato di sessione di prima classe;
4. non esisteva una capsula locale `node.h` che evidenziasse stato stale fra ledger/artefatti.

## Pipeline v0.5

```text
PREVIOUS CHAPTERS
→ ATOMIC EPISTEMIC MINING
→ VALIDATED RETICULUM
→ MINIMAL SETUP
→ DoD + GENERATION CONTRACT
→ CLAIM/SOURCE/BIBLIOGRAPHY PLAN
→ SEALED INITIAL DRAFT
→ SCIENTIFIC-EDITORIAL REVIEW
→ REGENERATION
→ SEALED REGENERATED DRAFT
→ REVIEW UNTIL PASS_CANDIDATE
→ P+10.000 REVIEW SATURATION
→ MULTI-CLASS EDGE SIMULATION
→ LOSSLESS COMPRESSION
→ SEALED COMPRESSED FINAL
→ FINAL QUALITY/SOURCE RECHECK
→ MATERIALIZE + READBACK
→ COMPLETE
```

## Evidence binding

Ogni receipt rilevante viene vincolata a digest:

- draft → generation contract + reticulum;
- review → candidate digest + review standard digest;
- regeneration → from/to candidate digests;
- saturation → candidate digest;
- simulation → final candidate + generation contract + scenario digest;
- compression → pre/post candidate + generation contract + inventory;
- quality → final candidate digest.

Cambiare il testo senza rigenerare le evidenze rende il pacchetto stale e fail-closed.

## 400.000 simulazioni v0.5

Il budget è diviso **ex ante** in cinque classi da 80.000 casi:

- `adversarial`: receipt stale/forged/incomplete, degradation escape, source/bibliography gaps;
- `favorable`: controlli puliti, usati per misurare falsi positivi;
- `stress`: reticula, bibliografie, inferenze e review ledger più grandi e variati;
- `editorial_review`: over-sectioning, score insufficienti, finding non localizzati, struttura/stile;
- `logical_semantic_review`: locator mancanti, endpoint errati, inferenze cicliche, generation contract stale, perdita epistemica in rigenerazione.

Criteri e distribuzioni sono materializzati in `validation/simulation-v5.json`. Non sono 400.000 decisioni giuridiche sostanziali.

## Hardening reflection

`scripts/reflect_v5.py` enumera uno spazio di stati osservabili (task, corpus, reticolo, fonti, bibliografia, inferenza, review, rigenerazione, host, scelta utente). Dopo la completa enumerazione `1..M`, il ciclo termina solo dopo ulteriori `M+1000` replay senza nuova firma.
