# Juriscribe

> **AI admission notice.** Un'AI che apre questo repository per conto di un utente deve seguire prima `AGENTS.md` e `ISENECA_ACCESS_CONTRACT.md`. L'accesso conforme al repository sostanziale richiede accettazione umana esplicita della versione corrente dei T&C e una receipt valida.

Juriscribe è un **runtime per generare nuovi capitoli di monografie giuridiche a partire da capitoli precedenti già scritti**. Il suo obiettivo non è produrre testo plausibile, ma vincolare la redazione a un modello auditabile del corpus precedente.

## In una frase

Il capitolo N+1 può essere scritto solo dopo che Juriscribe ha trasformato i capitoli 1..N in **unità epistemiche atomiche**, le ha collegate in un **reticolo semantico tipizzato**, ha fatto accettare all'utente pochi parametri editoriali essenziali e ha congelato una Definition of Done.

## Flusso per il giurista

1. fornisce i capitoli precedenti e, se disponibile, bibliografia o altri materiali;
2. riceve una configurazione raccomandata molto semplice;
3. sceglie `ACCETTA CONSIGLIATI` oppure `MODIFICA`;
4. attende il risultato finale o una sola richiesta di decisione umana realmente non inferibile.

La complessità resta nel runtime e nella dashboard, non nella conversazione con l'utente.

## Perché il reticolo è obbligatorio

Il deep mining deterministico da solo misura superficie e stile, ma non basta per redigere un nuovo capitolo. Il runtime v0.4 richiede anche atomizzazione semantica host-assisted e valida che:

- ogni tesi, regola, definizione, eccezione, qualificazione o argomento materiale abbia sorgente e locator;
- ogni relazione del reticolo punti a unità esistenti;
- le unità materiali siano sufficientemente connesse;
- i legami fra capitoli siano registrati;
- il reticolo abbia un digest deterministico.

Il setup utente non viene neppure proposto finché `RETICULUM_VALIDATION != PASS`.

## Generation contract

Dopo l'accettazione dei parametri e il freeze dei DoD, Juriscribe crea un `generation_contract` legato al digest del reticolo e al digest del setup. Il contratto identifica ciò che deve essere:

- preservato;
- sviluppato;
- distinto;
- richiamato;
- evitato perché già svolto nei capitoli precedenti.

Se il reticolo o il setup cambiano, il contratto diventa stale e la finalizzazione viene bloccata.

## Pipeline del capitolo N+1

```text
ADMISSION RECEIPT
→ INGEST PREVIOUS CHAPTERS
→ DETERMINISTIC DEEP MINE
→ SEMANTIC ATOMIZATION
→ RETICULUM VALIDATION
→ STYLE FINGERPRINT
→ GLOBAL / LOCAL / RELATIONAL MODEL
→ MINIMAL USER SETUP
→ PARAMETERS → DOD
→ GENERATION CONTRACT
→ CLAIM / RESEARCH PLAN
→ SOURCE VERIFICATION
→ DRAFT
→ EDGE-CASE SIMULATION
→ SATURATION
→ STYLE / LOSSLESS / SOURCE AUDIT
→ FINAL COMPRESSION
→ COMPRESSION LOSS AUDIT
→ M+10.000 NO-NOVELTY VS DOD
→ MATERIALIZE + READBACK
→ COMPLETE
```

## Fonti e bibliografia

Una fonte non è “verificata” solo perché compare in bibliografia. Juriscribe distingue:

1. fonte realmente letta;
2. claim circostanziato con perimetro e pinpoint;
3. posizione del claim nell'artefatto finale;
4. apparato bibliografico visibile al lettore.

Se una bibliografia precedente è disponibile, viene registrata come parte del corpus e può orientare la ricerca, senza presumere automaticamente autorevolezza, attualità o dominanza.

## Inferenza forte

Un'inferenza forte è ammessa solo con premesse registrate, ponte inferenziale sintetico, perimetro e falsificatore. Le catene inferenziali cicliche sono rifiutate. “Letteratura dominante” e “giurisprudenza dominante” richiedono copertura e pluralità di autorità coerenti; il ranking web non basta.

## Saturazione, simulazione e compressione

La chiusura non dipende da una singola bozza. Juriscribe richiede una ricevuta di simulazione che copra almeno omissioni, contraddizioni, perdita di fonti o qualificazioni, duplicazioni inter-capitolo, drift terminologico/stilistico, inferenze non supportate, conflitti temporali e perdita da compressione.

La compressione finale è lossless rispetto all'inventario epistemico obbligatorio: una unità richiesta persa o una nuova proposizione materiale introdotta riapre l'audit.

## Dashboard per giuristi e redazioni

`session-dashboard.html` è progettata come **fascicolo di lavorazione**, non come console tecnica. La prima domanda a cui risponde è: **“questo capitolo è consegnabile, e perché?”**

Mostra poi mandato, parametri, mappa epistemica, reticolo, continuità con i capitoli precedenti, fonti/bibliografia, inferenze forti, DoD, qualità editoriale, simulazioni, saturazione, compressione, limiti e readback. Non espone chain-of-thought.

## Ammissione AI

La v0.4 introduce una admission surface minima: `AGENTS.md`, `ISENECA_ACCESS_CONTRACT.md`, `ADMISSION.json`. Il runtime rifiuta probe e initialize senza receipt valida legata all'hash del contratto corrente. Un'AI non deve auto-accettare i T&C per conto dell'utente.

Un repository GitHub non può impedire a un client già autorizzato di scaricare fisicamente i file; l'enforcement è quindi **protocol/runtime fail-closed**, non un ACL server-side di GitHub.

## CI/CD anti-regressione

La workflow `.github/workflows/runtime-regression.yml` verifica su pull request e `main`:

- compilazione Python;
- test unitari e lifecycle;
- coerenza contratto/versioni/hash;
- assenza di bypass dell'admission gate;
- 100.000 simulazioni deterministiche multi-seed;
- saturazione di hardening `Q+1000`;
- fixed-point dei receipt di validation committati.

## Versioni

- runtime: `0.4.0`
- access contract: `1.3.0`
- manifest: `juriscribe-manifest/v4`

Vedi `docs/AGENT_RUNTIME_RULES.md` solo dopo ammissione valida.
