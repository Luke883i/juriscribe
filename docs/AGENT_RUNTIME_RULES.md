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

## COMPRESSION & CONSOLIDATION — executable editorial reticulum v2
`canonical_material` è riferimento trasformativo immutabile, non autorità giuridica o scientifica automaticamente verificata. `candidate_material` è rifattorizzabile.

Il runtime deve:
1. inventariare losslessly ogni paragrafo/oggetto con locator e hash;
2. costruire un unico reticolo canonical/candidate con object coverage 1.0;
3. profilare metodo editoriale, scientifico, narrativo e argomentativo dei canonici disponibili;
4. costruire gap evidence e un refactoring contract causale;
5. costruire una sequenza esecutiva di reticoli: `SOURCE_SEMANTIC_RETICULUM` → `EDITORIAL_FUNCTION_RETICULUM` → `REFACTORING_SURGERY_RETICULUM` → `REFINED_PROJECTION_RETICULUM`;
6. classificare, quando semanticamente dichiarato, funzioni come CLAIM, EVIDENCE, WARRANT, METHOD, RESULT, QUALIFIER, LIMITATION, DEFINITION, CONTEXT, TRANSITION e IMPLICATION; non inventare funzioni mancanti;
7. richiedere candidate relation coverage 1.0 e support-path coverage 1.0 per i CLAIM espliciti; un generico `ARGUMENT` non viene auto-promosso a CLAIM;
8. richiedere per ogni trasformazione non-KEEP gap binding, rationale, expected benefit e degradation risk; MOVE/REORDER, MERGE_REDUNDANCY e SPLIT sono consentiti solo se causalmente autorizzati dal piano;
9. per SPLIT mantenere lo stesso semantic-unit id e consentire output binding `ONE_OR_MANY`; non creare nuove unità materiali solo per rappresentare la divisione editoriale;
10. applicare compression discipline: word-ratio 0.40–1.35, espansione >1.05 solo con operazione causale compatibile, nessun paragrafo raffinato esattamente duplicato;
11. privilegiare canonical immutability, structural unit/relationship recall 1.0, no unsupported novelty, chiusura gap, minimo numero di unità toccate e minima distanza trasformativa;
12. esercitare almeno 10.000.000 mutation instances sul gate storico e almeno 10.000.000 seeded editorial mutation instances sul reticolo esecutivo, con almeno 8 seed distinti, scenari semantic preservation/relation/gap/order/merge-split/compression/redundancy/stale binding/human calibration/idempotency/unicode/long-form, almeno 1000 deep checks, zero survivor e zero oracle mismatch; i conteggi restano soak volume, non casi testuali unici;
13. mantenere almeno due campagne 10M con seed space indipendentemente traslato nel gate CI del profilo editoriale v2;
14. richiedere M+1000 genuine no-novelty e N+1000 no-better-lossless-compression con coverage evidence;
15. usare `USER_CALIBRATION`; una decisione materiale rende stale piano, execution reticulum e downstream evidence; ripetizioni non materiali/idempotenti non devono produrre drift;
16. prima del seal costruire proof-carrying semantics ricalcolabile dal testo raffinato; caller-supplied recall è vietato;
17. distinguere sempre structural/editorial readiness da substantive scientific/legal truth e da journal acceptance: `A_LEVEL_EDITORIAL_READY` non certifica verità scientifica, peer review o accettazione da una rivista;
18. eseguire peer-review readiness, provenance e final severe review prima della materializzazione;
19. materializzare `refactoring_report` e N `refined_candidate` DOCX. `READY_FOR_PEER_REVIEW` non significa peer reviewed.

### Local DoD
- structural semantic preservation;
- causal operation authorization;
- editorial function/support coverage;
- compression/redundancy bounds.

### Global DoD
- current seeded 10M editorial stress evidence;
- tutti i candidati sealed con proof ricalcolabile;
- peer-review readiness;
- provenance;
- final severe review;
- materializzazione atomica.

## Artifact-first surface
Dopo modalità, materiali e setup minimo, prosegui autonomamente. **non narrare** mining, ricerca, reticolo, review, simulazioni, saturazione, compressione, provenance o gate. Messaggi ordinari: **1–3 righe**. Interrompi solo per una **decisione umana** materialmente bloccante e non inferibile.

non allegare state.json, session.integrity.json, receipt, provenance raw, JSONL, stderr, traceback o **stack trace** salvo richiesta tecnica esplicita. non trasformare la dashboard in un contenitore tecnico.

## Delivery
Tutti i documenti finali sono veri **DOCX** quando prescritti. `session-dashboard.html` resta HTML state-bound; una dashboard stale non soddisfa il gate. Non sostituire DOCX con Markdown/TXT/JSON/PDF o testo chat. La release è atomica; niente attachment parziali compliant. `DOCX_WRITE` e `DOCX_READBACK` devono essere AVAILABLE quando richiesti.

Il profilo semantico comune resta `JURISCRIBE_LEGAL_HUMANISTIC_EDITORIAL_V1`. Output macchina verboso richiede `JURISCRIBE_VERBOSE_JSON=1` e `--technical-output`.
