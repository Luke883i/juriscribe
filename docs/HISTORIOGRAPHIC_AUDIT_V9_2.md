# Historiographic audit — PR10 / main → v0.9.2 hardening

## Oggetto

L'audit confronta il main post-PR10 con gli invarianti documentati nelle versioni precedenti, in particolare v0.4/v0.5, dove l'esperienza del giurista era intenzionalmente semplice: materiali, setup minimo, quindi risultato finale oppure una richiesta umana realmente non inferibile. La complessità doveva restare nel runtime e nella dashboard.

PR10 ha corretto regressioni importanti della generalizzazione tri-mode: formato DOCX dichiarato, dashboard nel set finale, separazione fra record interni e allegati, chat finale breve. L'audit successivo identifica ciò che era ancora incompleto.

## Finding 1 — formato dichiarato ≠ artefatto materializzato

Il gate v0.9.1 verificava suffisso `.docx`, `readback=PASS` e capability dichiarate, ma non verificava l'esistenza del file né che fosse un reale pacchetto OOXML. I regression test stessi usavano path fittizi e consideravano valido il manifest.

**Rischio:** path inesistente, file vuoto o JSON rinominato `.docx` potevano soddisfare formalmente il delivery gate.

**Hardening:** verifica filesystem, ZIP OOXML, membri WordprocessingML minimi, testo rileggibile, size e SHA-256.

## Finding 2 — dashboard presente ≠ dashboard corrente

La dashboard era obbligatoria per ruolo ma non era legata allo stato corrente. Alcuni percorsi della pipeline salvavano mutazioni senza rigenerarla; inoltre il gate non poteva distinguere una dashboard aggiornata da una stale.

**Hardening:** digest deterministico dello stato sostanziale incorporato nel meta HTML e verificato al delivery gate; il facade aggiorna la dashboard dopo ogni comando post-bootstrap che dispone di workspace.

## Finding 3 — il vincolo artifact-first era troppo basso nella gerarchia

PR10 aveva rafforzato README, agent rules e manifest, ma `ISENECA_ACCESS_CONTRACT.md` 1.6.0 — superiore nella catena di autorità — non conteneva ancora il vincolo conversazionale/DOCX equivalente e manteneva una formula più permissiva sul readback “quando la capability esiste”.

**Hardening:** contratto 1.7.0 rende artifact-first, materializzazione, dashboard freshness e capability DOCX requisiti normativi. La modifica invalida correttamente le vecchie admission receipt.

## Finding 4 — era stato ripristinato soprattutto il silenzio finale, non l'autonomia silenziosa

La storia v0.4 diceva esplicitamente che l'utente, dopo materiali e setup, attende il risultato oppure riceve una sola decisione realmente non inferibile. PR10 imponeva 1–3 righe soprattutto “alla chiusura”.

**Rischio:** un host AI poteva restare conforme al delivery finale ma narrare in chat ogni passaggio di mining, ricerca, review o saturazione.

**Hardening:** il contratto 1.7 e le runtime rules definiscono tutta la superficie post-bootstrap come control surface: niente narrazione intermedia, niente conferme meccaniche, interruzioni solo per blocker non inferibili.

## Finding 5 — eccezioni e stderr potevano riaprire la complessità in chat

Il facade v0.9.1 catturava stdout ma un'eccezione Python poteva ancora produrre traceback/diagnostica non redatta.

**Hardening:** stdout e stderr sono catturati; le eccezioni ordinarie producono un solo messaggio pubblico. Il dettaglio viene registrato in `ledger/runtime-errors.jsonl` come INTERNAL e sintetizzato come runtime blocker nella dashboard. La modalità verbosa resta opt-in tecnico.

## Finding 6 — la dashboard umana elencava ancora record tecnici

Pur escludendoli dagli allegati, il renderer mostrava l'intero artifact registry, compresi record come `session_integrity`.

**Hardening:** il corpo principale del fascicolo mostra soltanto deliverable user-facing; i record interni restano esclusi e sono rappresentati al massimo da un conteggio nella sezione tecnica collassata.

## Finding 7 — il test contractuale non copriva questi invarianti

`check_contract.py` controllava token DOCX/dashboard/chat finale, ma non OOXML, dashboard state binding, stderr redaction, autonomia post-bootstrap o autorità contrattuale.

**Hardening:** i nuovi regression test e contract checks rendono queste proprietà parte della CI.

## Finding 8 — hardening nuovo non deve comprimere il contratto storico

Il primo draft del contratto 1.7, pur rafforzando delivery e superficie AI, aveva sintetizzato troppo il contratto 1.6. Il confronto storiografico riga-per-riga ha mostrato che una riscrittura abbreviata rischiava di perdere granularità normativa su pipeline distinte per `CONTINUATION`, `GREENFIELD` e `REVIEW`, rubriche scientifico-editoriali, applicabilità motivata dei criteri, witness di saturazione `REPORT_ONLY`, simulazioni multi-classe e compressione lossless.

**Rischio:** un hardening UX poteva involontariamente diventare una regressione scientifico-metodologica pur passando test token-based.

**Hardening:** il contratto 1.7 definitivo è una **estensione conservativa del 1.6**: conserva le 19 sezioni e le pipeline/rubriche dettagliate, modificando soltanto dove necessario materializzazione, delivery, dashboard, interazione e completion. Il contract checker mantiene anche marker storici di granularità per impedire future riscritture eccessivamente riduttive.

## Invariante consolidato

```text
BOOTSTRAP VISIBILE
→ MODE + MATERIALI + SETUP MINIMO
→ PIPELINE SCIENTIFICA MODE-SPECIFIC PRESERVATA
→ LAVORO AUTONOMO / SILENZIOSO
→ dettagli scientifici-editoriali nei DOCX e nella dashboard
→ interruzione solo per decisione umana bloccante non inferibile
→ verifica reale dei DOCX
→ dashboard state-bound corrente
→ delivery manifest senza record macchina
→ 1–3 righe finali + allegati
```

Il “silenzio” riguarda la superficie conversazionale ordinaria, non l'auditabilità: Juriscribe deve registrare più evidenza internamente e negli artefatti, non meno. L'hardening della superficie non può ridurre la granularità scientifica, editoriale o probatoria costruita dalle versioni precedenti.
