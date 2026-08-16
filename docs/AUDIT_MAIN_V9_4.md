# Audit integrale di `main` — v0.9.4

Base auditata: merge di PR #13 (`5fe4d419e177cb703751dfcb9c9e707684c7d701`).

## Scopo e misura

L'audit copre l'intero ciclo di vita del prodotto e tutte le superfici che possono modificare il significato o la consegna di un lavoro Juriscribe: admission/bootstrap, session state, tri-mode, mining, reticolo, fonti e claim, inferenze, continuation, review, rigenerazione, simulazione, compressione, provenance, final severe review, artefatti, dashboard, delivery, documentazione, contract checker e CI/fixed-point storici.

La misura adottata non e "piu dati in UI", ma **piu intelligibilita giuridica a parita di invarianti**. Nessun record scientifico storico viene riscritto e nessun fixed-point viene ridefinito per far passare la release.

## Pattern consolidati da preservare

1. **Single source of truth di sessione.** `SessionState` conserva oggetti epistemici espliciti; dashboard e artefatti devono essere proiezioni, non archivi paralleli.
2. **Fail-closed.** Bootstrap, integrity, source validation, final review, DOCX materialization e delivery falliscono quando manca una prova richiesta.
3. **Reticolo tipizzato.** Claim, regole, eccezioni, qualificazioni, inferenze e relazioni sono distinguibili e collegabili.
4. **Disciplina fonte/claim.** Le fonti materiali richiedono lettura, verifica, pinpoint e proposizione circostanziata; una inferenza forte richiede premesse, ponte e falsificatore.
5. **Review causale.** Finding, rigenerazione, preservazione epistemica e riesame sono collegati, anziche essere una mera scorecard.
6. **Provenance lossless.** Claim, inferenze, decisioni e trasformazioni materiali ricevono una disposizione finale verificabile senza esporre chain-of-thought latente.
7. **Tri-mode senza duplicazione di runtime.** CONTINUATION, GREENFIELD e REVIEW condividono il core e differenziano soltanto requisiti realmente diversi.
8. **Artifact-first.** La conversazione resta breve; il contenuto sostanziale appartiene agli artefatti.

## Anti-pattern identificati

### A1 — Dashboard come telemetria
La dashboard v0.9.3 mostrava digest, integrity, path, readback e conteggi interni. Questi dati sono utili al gate ma non aiutano un giurista a ricostruire l'argomento.

**Correzione:** il corpo HTML v0.9.4 contiene esclusivamente mandato, cornice editoriale e il contenuto inferenziale dei quattro dossier. Il digest di freshness resta solo nel `<head>` come metadata invisibile necessario al controllo consolidato.

### A2 — Duplicazione semantica fra artefatti
Evidence dossier, Source register, Inference register e Transformation ledger avevano ruoli nominativi ma non un'unica funzione canonica che ne determinasse il contenuto.

**Correzione:** `juriscribe.editorial_artifacts` costruisce quattro viste deterministiche a partire dallo stesso stato. La dashboard aggrega esattamente quelle viste.

### A3 — Perdita di significato nella presentazione
Il runtime gia registrava autorita, scope, controautorita, premise, bridge, falsifier, review findings, preservation e consequence probes, ma gran parte di questa informazione non arrivava alla superficie umana.

**Correzione:** ogni dossier espone la funzione giuridica del dato, non soltanto il suo stato macchina.

### A4 — Freshness soltanto materiale
La dashboard era stale-sensitive, mentre un dossier DOCX poteva restare formalmente valido anche dopo una modifica semantica dello stato, se i byte non cambiavano.

**Correzione:** i dossier registrati da v0.9.4 vengono sigillati con il digest della propria proiezione giuridico-editoriale. Un cambiamento successivo rende il dossier stale al completion gate. I record storici privi del seal restano migrabili.

### A5 — Drift documentale di versione
Il runtime era 0.9.3 mentre il README riportava ancora 0.9.2.

**Correzione:** la versione e la documentazione corrente sono riallineate a 0.9.4; il contratto di accesso resta 1.7.0 perche non cambia l'admission policy.

## Modello semantico v0.9.4

- **Evidence dossier:** proposizione -> funzione giuridica -> fonte/premessa -> pinpoint -> qualificazioni/contrasti -> disposizione -> collocazione nel testo.
- **Source register:** fonte -> carattere dell'autorita -> organo/autore -> tempo/giurisdizione -> uso effettivo -> evidenza circostanziata -> riserve/controautorita -> bibliografia.
- **Inference register:** conclusione -> premesse testuali -> ponte -> falsificatore -> autorita/evidenze -> qualificazioni/obiezioni/contrasti -> disposizione.
- **Transformation ledger:** finding -> ragione -> intervento -> preservazione/perdita/novita -> compressione -> final review -> conseguenze riesaminate.
- **Dashboard:** riproduzione integrale e leggibile delle quattro viste, senza telemetria tecnica nel corpo.

## DoD v0.9.4

La release e completata soltanto se:

1. i quattro dossier sono derivati da una proiezione canonica condivisa;
2. la dashboard rende ogni contenuto delle quattro proiezioni senza ridurlo a metriche;
3. nel `<body>` della dashboard non compaiono integrity manifest, digest, path di filesystem, capability, readback o log;
4. il metadata invisibile di freshness resta operativo e una dashboard stale continua a fallire;
5. i dossier v0.9.4 registrati portano un semantic seal e il drift inferenziale viene rilevato;
6. nessuna nuova struttura espone chain-of-thought latente: soltanto oggetti epistemici gia materializzati;
7. DOCX, readback, confinement, no-symlink e bounded OOXML restano invariati;
8. tri-mode, bootstrap, provenance, final review, M+10.000 e tutti i gate consolidati restano invariati;
9. unit/lifecycle/review/continuation/multimode/finalization e contract checker passano su Python 3.10 e 3.12;
10. 400k five-class, M+1000, 10k continuation, 10k v7 mutations, reflection v8, 30k tri-mode e tutti i fixed-point storici restano verdi senza aggiornare le receipt di baseline.

## Criterio di non-regressione

La release aggiunge un livello di **proiezione** sopra lo stato; non sostituisce lo stato. Raw provenance, review receipts, reticolo, claim ledger, source records e simulation/fixed-point formats restano invariati. In questo modo il prodotto diventa piu significativo per il lettore giuridico senza spostare o indebolire la frontiera di validazione scientifica.
