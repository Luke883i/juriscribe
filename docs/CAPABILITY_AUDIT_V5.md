# Juriscribe Capability Audit — PR4 baseline → runtime v0.5

## Oggetto dell'audit

Questo audit risponde a una domanda operativa: **Juriscribe, alla baseline post-PR4, vincola davvero la generazione del capitolo N+1 ai capitoli 1..N e possiede prove sufficienti prima di dichiarare il lavoro completo?**

Baseline osservata: merge PR4 `83ca2d0131ff09586c7dbd3d42ee9b1b9c4e8be8`. La relativa GitHub Actions `Juriscribe runtime regression` risultava completata con successo. L'audit distingue capacità realmente implementate, controlli parziali e capacità mancanti; non equipara test computazionali a correttezza giuridica sostanziale.

## Esito sintetico sulla v0.4

| Capacità | v0.4 | Evidenza osservata | Gap che motiva v0.5 |
|---|---|---|---|
| Mining atomico + reticolo prima del setup | GOOD | `validate_reticulum()` e `generation_contract` erano gate reali | mancava il secondo fixed point post-bozza |
| Binding fra N+1 e capitoli precedenti | GOOD/PARTIAL | generation contract legato a reticolo/setup | la review della bozza non era causalmente legata a una rigenerazione |
| Fonti circostanziate + strong inference | GOOD/PARTIAL | direct read, verified_at, pinpoint, proposition, anti-cycle | completezza della ricerca resta dipendente dal corpus/host |
| Bibliografia precedente | PARTIAL | poteva essere rappresentata come fonte/corpus | non era stato di sessione di prima classe con coverage gate |
| Simulazioni edge-case | PARTIAL | famiglie obbligatorie e receipt | receipt non legata al digest della bozza valutata |
| Compressione lossless | PARTIAL | inventario preservato | receipt non legata in modo forte ai digest before/after del candidato |
| Review scientifico-editoriale post-bozza | MISSING | quality audit esisteva | nessuna review severa obbligatoria + findings + rigenerazione |
| Rigenerazione dopo findings | MISSING | non richiesta da `COMPLETE` | una prima bozza poteva essere finalizzata senza ciclo correttivo |
| Saturazione post-review P+10.000 | MISSING | esisteva M+10.000 vs DoD | mancava no-novelty **e** no-better-improvement-without-degradation |
| Evidenza causale review→regen→review | MISSING | nessun chain validator | possibile scorecard cosmetica senza prova di correzione |
| Stato locale `node.h` | MISSING | solo `state.json` | nessun indice digest-first per mismatch/stale state |
| Dashboard per redazione | GOOD/PARTIAL | fascicolo e blocker leggibili | mancavano cronologia review/regen e fixed point post-review |
| CI anti-regressione | GOOD | compile, unit, 100k multi-seed, fixed-point | non copriva il nuovo review loop né 400k classi bilanciate |

## Correzione v0.5

La v0.5 introduce una distinzione non negoziabile: **prima bozza ≠ deliverable**.

```text
chapters 1..N
→ atomic epistemic mining
→ semantic reticulum
→ setup + DoD + generation contract
→ source / bibliography / inference checks
→ sealed INITIAL draft
→ severe scientific-editorial review
→ findings + criterion-level evidence
→ causal regeneration
→ sealed REGENERATED draft
→ new review
→ P+10.000 no-new-finding AND no-better-improvement-without-degradation
→ 400k edge/stress/editorial/logical-semantic simulation receipt
→ lossless compression bound to before/after digests
→ final quality/source recheck bound to compressed candidate
→ final artifact + readback
→ COMPLETE
```

Il completion gate richiede almeno una rigenerazione causata da findings reali e una review successiva del candidato rigenerato. La saturation receipt è legata al digest del candidato riesaminato; `probes >= P + 10.000` e i due streak di 10.000 devono essere verificabili.

## Standard scientifico-editoriale dichiarato ex ante

La review usa il profilo `JURISCRIBE_LEGAL_MONOGRAPH_V1`, publisher-neutral, con tredici criteri obbligatori:

1. contributo monografico;
2. coerenza inter-capitolo;
3. autorità giuridica;
4. tracciabilità citazionale;
5. controautorità;
6. perimetro temporale e giurisdizionale;
7. disciplina dell'inferenza;
8. terminologia;
9. struttura;
10. stile editoriale;
11. integrità bibliografica;
12. preservazione lossless;
13. adeguatezza al lettore.

Ogni criterio deve avere evidenza localizzata o un `NOT_APPLICABLE` motivato. `BLOCKER` e `MAJOR` impediscono il fixed point. Lo stile citazionale è configurabile: OSCOLA è un riferimento forte per legal citation, ma non viene imposto quando editore, collana o ordinamento richiedono altro.

Le basi esterne e i limiti della sintesi sono documentati in `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md`.

## Simulazioni v0.5: criteri e classi

La baseline v0.5 usa **400.000 casi computazionali**, bilanciati ex ante:

| Classe | Budget | Criterio di successo |
|---|---:|---|
| adversarial | 80.000 | receipt stale/forgiate/incomplete/degradate devono essere respinte |
| favorable | 80.000 | package puliti devono essere accettati; misura falsi positivi |
| stress | 80.000 | reticoli/ledger più grandi restano deterministici; corruzioni falliscono |
| editorial_review | 80.000 | drift, over-sectioning, evidenza review incompleta, score insufficienti e findings non localizzati hanno l'esito atteso |
| logical_semantic_review | 80.000 | orphan/cycle/unsupported/stale/lossy semantic states sono respinti |

Il receipt materializza seed, famiglie, category counts, scenario digest, mutanti intercettati, controlli accettati, escape e falsi positivi. Questi casi sono property/mutation/stress tests: **non** sono 400.000 decisioni giuridiche o chiamate LLM.

## Riflessione di hardening

Lo spazio osservabile v0.5 combina task, corpus, reticulum, fonti, bibliografia, inferenza, review, rigenerazione, host e scelta utente. La riflessione architetturale enumera le firme distinte e termina soltanto dopo ulteriori 1.000 osservazioni senza nuova firma. Il risultato è un controllo di copertura dello spazio di stati, non esposizione di chain-of-thought.

## `node.h` ex ante

Ogni workspace genera `.juriscribe/<session-id>/node.h`, un indice locale **senza testo giuridico**, con digest e puntatori per:

- corpus/sources/claims/source intelligence;
- reticolo;
- setup e DoD;
- generation contract;
- candidato corrente;
- review/rigenerazioni/saturazione;
- bibliografia;
- simulazioni;
- compressione;
- quality/benchmark/artifacts;
- decisione ready/not-ready.

`node.h` serve a rilevare mismatch e stato stale tra passaggi; non è una firma crittografica di terza parte e non sostituisce `state.json`/ledger.

## Opportunità ulteriori dopo v0.5

### Potenziamento cognitivo

- reticolo temporale delle tesi per distinguere evoluzione concettuale, non solo collegamenti statici;
- dissent ledger per mantenere interpretazioni concorrenti senza falsa armonizzazione;
- reviewer plurality: più profili di review indipendenti e registro del disaccordo;
- semantic diff tra versioni del capitolo, legato alle unità epistemiche e non solo al testo.

### Potenziamento giuridico

- policy di autorità per giurisdizione/materia (es. precedenza, gerarchia, valore persuasivo);
- grafo di vigenza/supersession per norme e giurisprudenza;
- conflict-of-authorities matrix con controautorità obbligatoria quando materialmente pertinente;
- adapter citazionali per OSCOLA, stili editoriali italiani e profili di collana.

### Potenziamento scientifico/editoriale

- protocolli blind multi-monografia, non un solo benchmark;
- calibrazione delle soglie di score con reviewer umani e disagreement analysis;
- rubriche per introduzioni/conclusioni/capitoli dogmatici/ricostruttivi/comparati diverse per funzione;
- proof package esportabile per referee/editor con claim map, findings, rigenerazioni e final fixed point.

### Scalabilità e hardening

- sharding del reticolo per monografie molto grandi con digest Merkle o equivalente;
- ricevute firmate opzionali per `node.h` e validation packages;
- budget adattivo delle simulazioni per rischio, mantenendo un minimo anti-regressione;
- test di performance/memoria su corpus molto grandi e input malformati;
- policy CI che renda obbligatori i check runtime prima del merge tramite branch protection GitHub.

## Limiti residui da non occultare

- la qualità dell'atomizzazione semantica avanzata dipende ancora dall'host AI;
- il runtime non può dimostrare completezza assoluta della ricerca giuridica;
- `dominante` resta una conclusione conservativa legata a copertura/campionamento del corpus;
- un editore o responsabile scientifico può imporre standard che prevalgono sul core publisher-neutral;
- simulazioni e saturation receipts provano invarianti del processo, non verità giuridica;
- `node.h` è integrity metadata locale, non attestazione notarile;
- l'admission gate disciplina runtime/agent conformi, non è un ACL GitHub server-side.

## Giudizio consolidato

**PR4/v0.4 svolge bene il pre-draft epistemic/evidence gating, ma solo parzialmente la funzione completa di “scrivere il capitolo successivo come parte di una monografia scientifica”.** Il difetto decisivo è l'assenza di un ciclo obbligatorio post-bozza di review severa, rigenerazione causale e secondo fixed point. La v0.5 è progettata specificamente per chiudere questo gap senza trasformare le metriche in una pretesa di giudizio giuridico automatico.
