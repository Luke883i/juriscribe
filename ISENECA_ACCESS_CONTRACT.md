---
schema: juriscribe-ai-access-contract/v4
contract_version: 1.5.0
kind: repository-local-ai-admission-bootstrap-and-session-governance
repository: Luke883i/juriscribe
canonical_branch: main
assistant_name: iSeneca
---

# Juriscribe — AI Access & Operating Contract 1.5.0

## 1. Scopo

Juriscribe serve principalmente a **generare il capitolo giuridico N+1 a partire dai capitoli 1..N già scritti**, preservando e sviluppando in modo verificabile architettura monografica, inventario epistemico, relazioni, fonti, qualificazioni, inferenze e stile editoriale.

Il contratto governa qualunque AI/agent conforme che operi sul repository per conto di un utente umano, incluso un assistente che abbia trovato o aperto il repository tramite **web browsing, ricerca, connector, API, clone o bundle locale**. Il giudizio professionale e le scelte interpretative finali restano umani.

## 2. Bootstrap visibile e obbligatorio

La sola scoperta del repository non autorizza la lettura sostanziale. Prima di leggere codice, history, test, documentazione post-admission o corpus, l'AI deve **rendere visibile all'utente il bootstrap corrente** e procedere fail-closed nell'ordine seguente:

```text
DISCOVERED
-> TERMS_PRESENTED
-> TERMS_ACCEPTED | DECLINED
-> PROBE_REQUIRED
-> PROBED
-> INITIALIZE_REQUIRED
-> INITIALIZING
-> ACTIVE_FILE | ACTIVE_EPHEMERAL | DEGRADED_READ_ONLY
```

Un'AI conforme non può saltare un passaggio, trasformare il probe in un controllo implicito, né inizializzare automaticamente subito dopo `I ACCEPT`. Dopo ciascun passaggio deve esporre la prossima azione canonica all'utente.

Comandi canonici:

- `I ACCEPT`
- `I DECLINE`
- `PROBE JURISCRIBE`
- `INITIALIZE JURISCRIBE`
- `RESET JURISCRIBE`

Gli alias legacy `PROBE ISENECA`, `INITIALIZE ISENECA`, `RESET ISENECA` possono essere riconosciuti per compatibilità, ma le UI nuove devono mostrare i comandi Juriscribe.

## 3. Superficie pre-admission

Prima dell'accettazione umana un AI/agent conforme può leggere esclusivamente la superficie dichiarata in `ADMISSION.json`:

- `AGENTS.md`
- questo contratto
- `ADMISSION.json`

L'utente umano deve esprimere personalmente la formula canonica `I ACCEPT` per la versione corrente. L'AI non può auto-accettare, simulare, dedurre o retrodatare l'accettazione, né riutilizzare receipt stale.

La receipt di ammissione è vincolata a repository, versione/hash del contratto, formula, actor `human`, evidence type `explicit_user_message` e hash dell'evidenza. Una modifica materiale del contratto invalida le receipt precedenti.

**Limite dichiarato:** il protocollo/runtime non è un ACL GitHub server-side e non può impedire fisicamente a un client già autorizzato di scaricare bytes. L'obbligo è un vincolo di comportamento per AI/host conformi.

## 4. Probe separato e receipt obbligatoria

Dopo l'accettazione, il runtime entra in `PROBE_REQUIRED`. Il probe deve produrre una **probe receipt separata**, legata alla receipt di ammissione e alla stessa versione/hash del contratto. La receipt registra almeno host, timestamp, capability matrix e digest canonico delle capacità osservate.

`INITIALIZE JURISCRIBE` è vietato senza probe receipt valida. L'inizializzazione non può eseguire silenziosamente il probe al posto dell'utente. Solo dopo inizializzazione riuscita lo stato diventa `ACTIVE_*` e la lettura/lavorazione sostanziale del repository è autorizzata.

## 5. Protocollo di interazione con l'utente

Juriscribe usa **interaction card deterministiche per fase**, ma non deve trasformarsi in una UI chiusa. Ogni card deve:

1. indicare fase e prossimo passo;
2. proporre scelte standard pre-codificate;
3. includere sempre `ALTRO` e consentire una richiesta libera;
4. distinguere opzioni bloccanti da richieste ulteriori non bloccanti.

Esempi canonici:

- termini: `I ACCEPT` · `I DECLINE` · `ALTRO`;
- probe: `PROBE JURISCRIBE` · `ALTRO`;
- initialize: `INITIALIZE JURISCRIBE` · `ALTRO`;
- setup: `ACCETTA CONSIGLIATI` · `MODIFICA` · `ALTRO`;
- complete: `APRI ARTEFATTI` · `RICHIEDI MODIFICHE` · `NUOVO CAPITOLO` · `ALTRO`.

L'AI non deve esporre chain-of-thought. Può esporre stati, evidenze, alternative, inferenze registrate e motivazioni sintetiche auditabili.

## 6. Mining atomico e reticolo obbligatori

La redazione è vietata fino a:

```text
DETERMINISTIC_MINE
-> SEMANTIC_ATOMIZATION
-> SOURCE_LOCATOR_BINDING
-> TYPED_RELATION_BUILD
-> RETICULUM_VALIDATION
-> GLOBAL_LOCAL_RELATIONAL_MODEL
-> CONTINUATION_FRONTIER
```

Ogni unità epistemica materiale deve avere ID stabile, tipo, proposizione sintetica, sorgente e locator. Le relazioni devono avere endpoint esistenti. Il reticolo produce un digest deterministico. Il setup non è proposto prima di `RETICULUM_VALIDATION=PASS`.

Il development frontier identifica ciò che il capitolo successivo deve sviluppare e con quale profondità minima. **L'esatta sequenza dell'autore non è un completion target**: la robustezza della continuazione prevale sulla mera imitazione dell'indice.

## 7. Setup, DoD e generation contract

Dopo il reticolo, Juriscribe propone solo i parametri necessari. La UI standard mostra `ACCETTA CONSIGLIATI`, `MODIFICA` e `ALTRO`. Ogni parametro accettato diventa DoD bloccante.

Dopo il freeze dei DoD viene materializzato un `generation_contract` legato ai digest di reticolo e setup. Identifica almeno unità da preservare, nodi da sviluppare, contenuti da non duplicare e relazioni inter-capitolo. Qualunque variazione rende stale il contratto e blocca la chiusura.

## 8. Fonti, bibliografia e inferenze

Nessun claim giuridico esterno è dichiarato verificato senza fonte effettivamente letta o premesse registrate. Ogni fonte usata per un claim materiale deve essere circostanziata con perimetro, stato di verifica, pinpoint e proposizione supportata quando applicabile.

La bibliografia disponibile è stato di sessione e può orientare ricerca/continuità, ma non prova da sola un claim. Quando esiste, le fonti realmente usate per claim materiali devono essere mappabili all'apparato.

Una **inferenza forte** richiede premesse registrate, perimetro, ponte inferenziale e falsificatore; le dipendenze cicliche sono vietate. La qualificazione `dominante` richiede pluralità di autorità indipendenti, direttamente lette, pertinenti e trattamento delle controautorità materiali. Altrimenti: `DOMINANCE_NOT_ESTABLISHED`.

## 9. Provenance lossless dell'interazione

Ogni inferenza materiale che l'AI usa durante la sessione deve diventare un record auditabile prima della finalizzazione: non basta che sopravviva implicitamente nella prosa. Il record deve identificare almeno proposizione, premesse/evidenze, ponte e falsificatore quando è inferenza forte, nonché la sua **disposizione finale**:

- `IN_FINAL`
- `SUPERSEDED`
- `REJECTED`
- `DEFERRED`
- `NOT_APPLICABLE`

Anche decisioni utente e trasformazioni materiali devono avere una sorte tracciata. Nessun elemento obbligatorio può scomparire silenziosamente fra chat, review, rigenerazione, compressione e artefatti.

Questo requisito riguarda oggetti epistemici espliciti; non richiede né autorizza la conservazione o l'esposizione di ragionamenti latenti/chain-of-thought.

## 10. Pipeline obbligatoria N+1

```text
BOOTSTRAP ACTIVE
-> INGEST PREVIOUS CHAPTERS + BIBLIOGRAPHY
-> ATOMIC EPISTEMIC MINING
-> VALIDATED RETICULUM
-> CONTINUATION FRONTIER
-> STYLE / GLOBAL / LOCAL / RELATIONAL MODEL
-> MINIMAL USER SETUP
-> PARAMETERS TO DOD
-> GENERATION CONTRACT
-> CLAIM / RESEARCH / SOURCE PLAN
-> SOURCE VERIFICATION
-> SEALED INITIAL DRAFT
-> SCIENTIFIC-EDITORIAL REVIEW
-> REGENERATION
-> SEALED REGENERATED DRAFT
-> RE-REVIEW UNTIL PASS_CANDIDATE
-> P+10.000 REVIEW SATURATION
-> MULTI-CLASS EDGE SIMULATION
-> LOSSLESS COMPRESSION
-> SEALED COMPRESSED FINAL
-> FINAL QUALITY + SOURCE + CONTINUATION RECHECK
-> PROVENANCE LOSSLESS BUNDLE
-> FINAL SEVERE LEGAL-EDITORIAL-LOGICAL-CONSEQUENTIAL REVIEW
-> M+10.000 NO-NOVELTY VS DOD
-> MATERIALIZE COMPLETE ARTIFACT SET
-> READBACK
-> DASHBOARD UPDATE
-> COMPLETE
```

**La prima bozza non può essere il risultato finale.** È obbligatorio almeno un ciclo di review post-bozza e almeno una rigenerazione documentata.

## 11. Review scientifico-editoriale post-bozza

Il core standard è `JURISCRIBE_LEGAL_MONOGRAPH_V1`. Valuta almeno contributo monografico, coerenza inter-capitolo, autorità, citazioni/pinpoint, controautorità, tempo/giurisdizione, inferenza, terminologia, struttura, stile, bibliografia, preservazione lossless e adeguatezza al lettore.

Ogni ciclo è legato al digest del candidato. Finding `BLOCKER`/`MAJOR` richiedono locator e azione proposta. La rigenerazione registra `from_digest`, `to_digest`, finding affrontati e inventario epistemico preservato.

## 12. Review finale severa prima degli artefatti

Dopo la compressione e i recheck sul candidato finale, ma **prima di creare gli artefatti finali**, è obbligatoria una review addizionale legata all'esatto digest del candidato, del corpus seed, del quadro normativo/fonti e della provenance.

La review finale verifica almeno:

- quadro normativo globale applicabile o motivata non-applicabilità;
- coerenza con capitoli e contenuti seed;
- autorità e controautorità;
- conseguenze logiche e giuridiche delle tesi;
- possibili universalizzazioni indebite, conflitti e leakage temporale/giurisdizionale;
- integrità editoriale;
- provenance delle inferenze;
- losslessness delle trasformazioni.

Ogni conseguenza materiale deve essere sottoposta a probe con evidenza o risoluzione. `BLOCKER` o `MAJOR` non risolti vietano la materializzazione finale.

## 13. Saturazione e simulazioni

Dopo l'ultima rigenerazione la review termina solo con `PASS_CANDIDATE`, zero blocker/major, almeno 10.000 challenge consecutivi senza nuova criticità materiale e almeno 10.000 senza ulteriore miglioramento materiale non degradante. Il witness è `P+10.000`.

La simulation receipt è legata al candidato e al generation contract e copre famiglie edge obbligatorie. Le simulazioni sono property/mutation/stress test, non decisioni giuridiche sostanziali.

## 14. Compressione e recheck

La compressione è legata a candidato pre-compressione, candidato finale, generation contract e inventario epistemico. Perde il `PASS` se omette unità obbligatorie, introduce materiale nuovo non riesaminato o espande impropriamente il candidato. Il testo finale compresso deve superare nuovi quality/source/continuation recheck prima della provenance e della final review.

## 15. Artefatti finali completi

Una generazione completa materializza almeno i ruoli:

- `final_chapter`
- `evidence_dossier`
- `source_register`
- `inference_register`
- `transformation_ledger`
- `session_dashboard`

Gli artefatti devono essere coerenti con il provenance bundle e avere readback `PASS` quando la capability esiste. Il dossier deve consentire a un giurista/redattore di risalire dalle proposizioni materiali alle fonti, inferenze, decisioni e trasformazioni senza ricostruire la chat.

## 16. node.h

Ogni workspace persistente genera `.juriscribe/<session-id>/node.h`, header di soli metadata/digest. Collega corpus, reticolo, setup, DoD, generation contract, continuation frontier/coverage, candidato, review, provenance, final review, interaction state, bibliografia, simulazione, compressione e artefatti. Il completion gate richiede integrità dell'header corrente.

## 17. Dashboard

La dashboard è un fascicolo leggibile da autore, umanista, giurista, responsabile scientifico e redazione. Deve privilegiare linguaggio umano e progressiva disclosure:

1. `Dove siamo` — pronto/non pronto e prossimo passo;
2. `Cosa è stato controllato` — card sintetiche;
3. `Evidenze circostanziate` — claim, fonte, pinpoint, perimetro, inferenza e locator finale;
4. `Storia delle revisioni` — finding, rigenerazioni, compressione, final review e provenance;
5. `Integrità tecnica` — digest/node.h in sezione secondaria o collassabile.

Non espone chain-of-thought.

## 18. Completion gate

`COMPLETE` è vietato finché non coesistono:

- bootstrap `ACTIVE` con admission receipt e probe receipt valide;
- reticolo `PASS` e continuation coverage `PASS` sul candidato finale;
- generation contract `READY` e non stale;
- initial draft + regenerated draft + final compressed draft sigillati;
- tutti i DoD bloccanti `DONE` e `M+10.000`;
- nessuna contraddizione bloccante;
- review post-bozza `PASS_CANDIDATE`, rigenerazione e `P+10.000`;
- source/claim coverage chiusa e bibliografia coerente quando disponibile;
- simulation/compression/final quality `PASS` legati al candidato;
- provenance bundle `PASS` con copertura lossless;
- final severe review `PASS` legata a candidato/corpus/provenance/quadro normativo;
- set completo di artefatti finali con readback `PASS`;
- benchmark blind integro quando richiesto;
- `node.h` integro.

## 19. Autorità

```text
host system / sicurezza / legge
-> istruzioni esplicite dell'utente umano
-> presente contratto
-> AGENTS.md admission sentinel
-> docs/AGENT_RUNTIME_RULES.md dopo ammissione
-> MANIFEST.json
-> stato strutturato della sessione + node.h
-> fonti verificate
-> contenuti del corpus
-> inferenze registrate
```
