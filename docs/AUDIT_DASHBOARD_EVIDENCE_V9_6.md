# Audit severo — copertura evidenziale della dashboard v0.9.6

## Mandato

Verificare se la dashboard Juriscribe sia realmente alimentata da **ogni evidenza materializzata** e non soltanto dai quattro dossier semantici; rendere visibile l'esito complessivo in forma insieme completa e compressa; consentire il richiamo dei singoli artefatti finali; mantenere invariati mining, reticolo, claim/source/inference discipline, provenance, review, delivery fail-closed e fixed-point storici.

## Metodo di audit

L'audit separa quattro livelli che nelle versioni precedenti potevano essere confusi:

1. **stato epistemico sorgente** — claim ledger, fonti, unita epistemiche, provenance, review, transformation records e `artifact_evidence`;
2. **proiezioni canoniche** — Evidence dossier, Source register, Inference register e Transformation ledger;
3. **evidenza di collocazione nel prodotto** — collegamento fra claim, fonti/pinpoint e posizione dichiarata nell'artefatto finale;
4. **superficie dashboard** — esito compresso, dossier completi, tracciabilita delle evidenze e richiamo agli artefatti.

La proprieta richiesta non e soltanto la parita dei dossier. E la catena causale:

`evidenza registrata -> riferimento epistemico -> fonte/pinpoint -> collocazione nel prodotto -> proiezione dashboard -> artefatto richiamabile`.

## Pattern consolidati da preservare

- singolo stato canonico della sessione;
- quattro dossier derivati dalla stessa proiezione giuridico-umanistico-editoriale;
- semantic seal dei dossier;
- dashboard senza telemetria tecnica nel body;
- delivery confinato nel workspace, readback reale e fail-closed;
- distinzione fra contenuto attestato, inferenza e trasformazione editoriale;
- browser come renderer e strumento di lettura, non come motore inferenziale;
- compatibilita Python 3.10/3.12 e baseline/fixed-point storici.

## Anti-pattern rilevati

### A1 — P0: `artifact_evidence` non proiettato lossless

La v0.9.5 usava `artifact_evidence` soprattutto per recuperare `artifact_locator` nell'Evidence dossier. `source_ids`, `pinpoints`, `status` e futuri campi estesi non avevano una garanzia di presenza nella dashboard. Ne derivava una falsa equivalenza fra **parita dei quattro dossier** e **completezza dell'evidenza**.

**Correzione:** `JURISCRIBE_EVIDENCE_TRACEABILITY_V1` proietta 1:1 ogni record `artifact_evidence`, preserva i campi non ancora canonizzati sotto `attributi_ulteriori` e arricchisce il record soltanto con contesto gia presente nello stato.

### A2 — P1: riferimenti evidenziali non verificati come grafo

Un `claim_id`, `source_id` o artefatto esplicitamente dichiarato poteva diventare orfano senza un gate dedicato alla superficie evidenziale.

**Correzione:** `evidence_traceability_gate` fallisce su claim/fonti/artefatti espliciti non risolti, locator assente, identita duplicate o proiezione non lossless. Il record problematico resta visibile: il gate non nasconde l'errore.

### A3 — P1: assenza di indice umano degli artefatti finali

`state.artifacts` partecipava ai gate tecnici e al digest di freshness, ma non esisteva una proiezione umana completa degli artefatti richiesti dalla modalita.

**Correzione:** `build_user_artifact_index` deriva i ruoli dal medesimo `required_artifact_roles` del delivery. I quattro dossier sono indicati come contenuto integrale della dashboard; final chapter/legal text/review report/findings/revised text sono richiamati mediante link relativo quando materializzati. Gli artefatti INTERNAL restano esclusi.

### A4 — P1: esito complessivo privo di compressione controllata

La dashboard esponeva i registri completi ma non sintetizzava in modo canonico la quantita di evidenza, fonti, inferenze, trasformazioni, copertura `artifact_evidence` e disponibilita degli artefatti.

**Correzione:** `build_dashboard_evidence_coverage` genera un **Esito complessivo — quadro compresso e completo**. La sintesi usa esclusivamente conteggi e stati derivati; non introduce una nuova conclusione giuridica.

### A5 — P2: nessuna simulazione dedicata artefatto-evidenza -> dashboard

Le suite v0.9.4/v0.9.5 dimostravano la parita dei dossier e le proprieta della workbench, ma non falsificavano la perdita di campi di `artifact_evidence`, i riferimenti orfani o la completezza dell'indice artefatti.

**Correzione:** simulazione dedicata di **10.000 scenari unici**, con seed variabile e derivato univocamente, distribuzione CONTINUATION/GREENFIELD/REVIEW e casi negativi intenzionali.

## Architettura v0.9.6

La dashboard mantiene integralmente la workbench v0.9.5 e aggiunge tre livelli:

### Esito complessivo

Mostra in forma compressa:

- numero di elementi probatori;
- numero di fonti;
- numero di inferenze;
- numero di trasformazioni;
- rapporto evidenze registrate/proiettate;
- artefatti attesi/richiamabili;
- presenza di riferimenti evidenziali da completare.

Questa e una compressione **descrittiva**, non una nuova inferenza.

### Indice degli artefatti

Mostra tutti e soli gli artefatti finali richiesti dalla modalita, esclusa la dashboard stessa:

- titolo umano;
- funzione editoriale/scientifica;
- stato umano (`ATTESO`, `REGISTRATO`, `DISPONIBILE`);
- ancora al dossier quando il contenuto e integralmente presente nella dashboard;
- link relativo al file finale quando disponibile.

Non mostra path assoluti, digest, media type, capability, readback o altri dettagli tecnici.

### Registro di tracciabilita delle evidenze

Per ogni `artifact_evidence` mostra:

- identita dell'evidenza;
- tipo/funzione dichiarata;
- claim e proposizione risolta;
- collocazione nell'artefatto;
- fonti richiamate e loro contesto umano;
- pinpoint registrati;
- stato epistemico;
- artefatto dichiarato e relativo richiamo, se presente;
- ogni campo esteso non noto al runtime, preservato lossless.

## Simulazione 10.000 multi-seed

La simulazione `scripts/simulate_dashboard_evidence_v96.py` genera 10.000 scenari con seed di scenario univoco derivato da 20 seed base. Varia:

- modalita operativa;
- output REVIEW;
- numero di fonti;
- numero e tipo di claim;
- numero di evidenze di artefatto;
- disponibilita dell'esito;
- casi negativi con claim, fonte, artefatto o locator non risolto.

Per **ogni scenario** verifica:

1. numero evidenze registrate = numero evidenze proiettate;
2. ogni leaf del record `artifact_evidence` sopravvive nella proiezione;
3. l'indice artefatti coincide con i ruoli finali richiesti dalla modalita;
4. il numero di artefatti richiamabili e coerente;
5. i riferimenti validi passano il gate e quelli intenzionalmente rotti falliscono;
6. i seed di scenario sono tutti distinti.

Ogni centesimo scenario materializza anche la dashboard HTML e verifica presenza delle sezioni di copertura, presenza di ogni evidence ID proiettato e assenza di path/telemetria tecnica nel body.

## Definition of Done

La release v0.9.6 e completa solo se:

1. `artifact_evidence` e proiettato 1:1 senza perdita di campi;
2. claim, fonti e artefatti esplicitamente referenziati sono risolti o bloccano il completion gate;
3. i quattro dossier v0.9.4 restano integralmente presenti e semanticamente sigillati;
4. la dashboard contiene un esito complessivo compresso ma derivato soltanto da dati materializzati;
5. tutti gli artefatti finali richiesti dalla modalita compaiono nell'indice umano;
6. gli artefatti materializzati possono essere richiamati con link relativo confinato agli artifacts della sessione;
7. nessun artefatto INTERNAL compare nell'indice umano;
8. nessun path assoluto, digest, readback, capability o telemetria tecnica entra nel body;
9. il browser non genera nuove inferenze;
10. la simulazione dedicata esegue **10.000** casi con **10.000 seed di scenario unici** e stato PASS;
11. unit test e contract checker passano su Python 3.10 e 3.12;
12. 400k, M+1000, continuation, v7 mutations, reflection v8, 30k tri-mode e tutti i fixed-point storici restano verdi senza aggiornamento delle baseline.

## Criterio di regressione

Qualsiasi modifica futura che elimini una evidenza registrata dalla proiezione, rompa un riferimento senza segnalarlo, tolga un artefatto finale dall'indice o renda la sintesi incoerente deve rendere rossa la CI. Il miglioramento della leggibilita non puo essere ottenuto comprimendo via informazione epistemicamente rilevante.
