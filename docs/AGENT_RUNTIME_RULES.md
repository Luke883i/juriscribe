# Juriscribe agent runtime rules v0.12.0 — post-bootstrap

Dopo bootstrap e initialize, mostra e usa le modalità restituite dal runtime corrente. La selezione resta esplicita; `ALTRO` resta input libero. La modalità canonica C&C è `COMPRESSION & CONSOLIDATION`.

## Invarianti comuni
- mode contract e standard editoriale first-class;
- mining/reticolo prima delle conclusioni sostanziali;
- setup adattato al genere;
- claim/fonti/inferenze tracciabili;
- review scientifica, contenutistica e redazionale evidence-based;
- provenance e final severe review;
- artefatti mode-specific con readback;
- nessuna esposizione di chain-of-thought latente.

## Bootstrap hardening e fast path
L'accettazione umana non è inferibile. Dopo esatto `I ACCEPT`, usa `bootstrap-after-acceptance` quando disponibile: probe, sealed probe receipt e initialize restano distinti e auditabili. La receipt è single-use; le capability sigillate non vengono ampliate. Se il fast path non è realmente disponibile, usa i comandi canonici senza simulare transizioni.

Se l'host deve trasportare il sorgente, usa prima la `bootstrap_source_paths` closure dichiarata da `ADMISSION.json` quando `SESSION_CONTEXT=AVAILABLE`; non scandire né materializzare l'intero repository per completare admission/probe/initialize. Il runtime completo può essere espanso alla stessa revisione pin-nata quando serve il primo lavoro sostanziale. Le specifiche storiche restano fuori dal percorso corrente salvo audit/migrazione.

## Pipeline lock
Il linguaggio naturale non autorizza cambi impliciti di modalità, artefatto primario, set standard, formati o gate. Una nuova richiesta materiale viene classificata dal contratto conversazionale. Non sopprimere artefatti perché l'utente chiede colloquialmente “solo il documento finale”.

## COMPRESSION & CONSOLIDATION
`canonical_material` è riferimento trasformativo immutabile, non autorità giuridica automaticamente verificata. `candidate_material` è rifattorizzabile.

Il runtime deve:
1. inventariare losslessly ogni paragrafo/oggetto con locator e hash;
2. costruire un unico reticolo canonical/candidate con object coverage 1.0;
3. profilare metodo editoriale, scientifico, narrativo e argomentativo dei canonici disponibili;
4. costruire gap evidence e un refactoring contract causale;
5. privilegiare canonical immutability, structural unit/relationship recall 1.0, no unsupported novelty, chiusura gap, minimo numero di unità toccate e minima distanza trasformativa;
6. esercitare almeno 10.000.000 mutation instances su losslessness, canonical immutability, reticulum, gap evidence, argument strength, local/reticular progression, anomaly/edge, minimality e materialization readiness, rendendo esplicite equivalence classes, class counts e mismatch; il numero di istanze è soak volume, non numero di casi semanticamente unici;
7. richiedere M+1000 genuine no-novelty e N+1000 no-better-lossless-compression con coverage evidence;
8. usare `USER_CALIBRATION`; una decisione materiale rende stale mutation/saturation receipt legate al piano;
9. prima del seal costruire dal testo raffinato una `JURISCRIBE_PROOF_CARRYING_SEMANTICS_V1`: caller-supplied recall è vietato; unità materiali, relazioni richieste, output-object coverage, source/plan/reticulum/canonical bindings devono essere ricalcolati dal runtime;
10. distinguere sempre structural preservation da substantive legal truth/entailment: la prova strutturale non sostituisce review, fonti o giudizio professionale;
11. eseguire peer-review readiness, provenance e final severe review prima della materializzazione;
12. materializzare `refactoring_report` e N `refined_candidate` DOCX. `READY_FOR_PEER_REVIEW` non significa peer reviewed.

## Artifact-first surface
Dopo modalità, materiali e setup minimo, prosegui autonomamente. **non narrare** mining, ricerca, reticolo, review, simulazioni, saturazione, compressione, provenance o gate. Messaggi ordinari: **1–3 righe**. Interrompi solo per una **decisione umana** materialmente bloccante e non inferibile.

non allegare state.json, session.integrity.json, receipt, provenance raw, JSONL, stderr, traceback o **stack trace** salvo richiesta tecnica esplicita. non trasformare la dashboard in un contenitore tecnico.

## Delivery
Tutti i documenti finali sono veri **DOCX** quando prescritti. `session-dashboard.html` resta HTML state-bound; una dashboard stale non soddisfa il gate. Non sostituire DOCX con Markdown/TXT/JSON/PDF o testo chat. La release è atomica; niente attachment parziali compliant. `DOCX_WRITE` e `DOCX_READBACK` devono essere AVAILABLE quando richiesti.

Il profilo semantico comune resta `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`. Output macchina verboso richiede `JURISCRIBE_VERBOSE_JSON=1` e `--technical-output`.
