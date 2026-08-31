# Juriscribe Physical & Host Convergence v1.1

## Intenzionalità congelata

La v1.1 è una PR di convergenza, non una nuova modalità o un nuovo proof engine. Rende fisicamente vero il modello logico già stabilito da v1/v0.13.

1. **Public-first initialization.** Un host capability-compliant deve poter partire da `Initialize Juriscribe [canonical repo URL]` senza rendere obbligatorio un connector GitHub.
2. **Human acceptance invariant.** L'alias UX non salta `I ACCEPT`, probe, receipt o initialize.
3. **Capability truth.** `UNVERIFIED` non viene promosso; un host degradato deve produrre un blocker specifico, non una sessione simulata.
4. **Lifecycle reachability.** Discovery, bootstrap, work, materialization, delivery e recovery sono proprietà diverse e derivate.
5. **Universal host compatibility.** Provider, browser e OS non ricevono authority: a parità di capability il risultato deve essere identico.
6. **Physical runtime convergence.** `juriscribe.pipeline` non deve più eseguire `pipeline_v11 -> pipeline_v9`; il current CLI vive in un modulo non-versionato.
7. **Explicit public composition.** Nessuno star-import nel pipeline/orchestrator corrente; specialist proof authority resta invariata.
8. **Snapshot/recovery UX.** Recovery bundle rimane un controllo trasversale on-demand e non una quinta modalità.
9. **Scientific semantics preservation.** Le quattro modalità, i sei authority nodes, i gate specialistici, checkpoint e recovery semantics non vengono ridefiniti.

## Reticolo target

`public repo discovery -> exact acceptance -> capability reachability -> admission/probe/initialize -> persisted or memory session -> MODE_REGISTRY -> EXPLICIT_ROUTER -> SPECIALIST_PROOF -> MATERIALIZATION -> PROJECTION`

Le classi di reachability non sono nuovi authority nodes; sono una proiezione capability-only del percorso già esistente.

## DoD globale

- quattro modalità canoniche immutate;
- sei authority nodes immutati;
- zero import di `pipeline_v9`/`pipeline_v11` dal current public pipeline/runtime CLI;
- zero star-import nel current public pipeline/orchestrator;
- connector GitHub non richiesto quando esiste un public pinned source path;
- zero bootstrap success senza revision/contract binding, executable transport e state carrier;
- zero promozioni `UNVERIFIED -> AVAILABLE`;
- provider/browser/OS identity invariance = 100%;
- memory-only work non implica materialization/delivery/recovery;
- recovery export non muta scientific checkpoint e resume richiede fresh probe;
- regression v1 e v0.13 esistenti verdi;
- mutation oracle mismatches = 0;
- semantic mutant survivors = 0.

## DoD intermedie

### Runtime composition

- `pipeline.py -> runtime_cli.py` è l'unico current CLI composition edge;
- historical pipeline modules restano importabili per compatibility/audit, ma non sono nel current execution path;
- C&C e recovery commands sono composti direttamente nel current CLI;
- public shell projection resta separata dal runtime.

### Host bootstrap

- `Initialize Juriscribe` e `Inizializza Juriscribe` bindano il repository canonico;
- un URL non canonico viene rifiutato come bootstrap Juriscribe;
- `plan_runtime_transport` richiede un vero state carrier (`SESSION_CONTEXT` oppure `LOCAL_SCRATCH_IO`);
- installed runtime viene usato soltanto se revision-bound;
- source transport richiede `REPOSITORY_READ + PYTHON_EXECUTION + SOURCE_TO_RUNTIME_BRIDGE`;
- `repository_connector_required=false` è una proprietà esplicita del piano.

### Reachability locale

- `DISCOVERY_READY`: revision + contract pin;
- `BOOTSTRAP_READY`: discovery + executable transport + state carrier;
- `WORK_READY`: bootstrap reale;
- `MATERIALIZATION_READY`: work + filesystem + DOCX write/readback;
- `DELIVERY_READY`: materialization + real delivery surface;
- `RECOVERY_READY`: work + filesystem + real delivery surface.

## Campagna locale eseguita sul candidate classifier

Tre campagne separate, un milione di invocazioni complessive. Sono mutazioni di capability/lifecycle, non un milione di provider fisici, testi giuridici o sessioni LLM.

| Campaign | Seed | Cases | Oracle mismatches | Unique signatures |
|---|---:|---:|---:|---:|
| edge | 602425368693563340 | 333,334 | 0 | 3,680 |
| typical | 6918701765035871741 | 333,333 | 0 | 113 |
| stress/degraded | 4353082734915292282 | 333,333 | 0 | 73,594 |
| **TOTAL** | — | **1,000,000** | **0** | campaign-local |

Candidate digests:

- edge: `60e7c027b612159ab3577937ae785d6a946eef8a90ee29cf6890275005b65343`
- typical: `12c7d0d6bcab88dcd02d638c1e2a09164bb0bf80da98efb27a4155c2db6f2f3c`
- stress: `d2c094e80323c494b2e1d79e74f12cf4a65df8e940c31fa9843266b1aed24ed6`

A separate deep mutation-kill pass executed 50,000 cases against 20 non-equivalent semantic mutants:

- mutation families: **20**;
- mutants killed: **20**;
- survivors: **0**;
- oracle mismatches: **0**;
- provider/browser/OS identity mismatches: **0**.

The CI checker repeats a deterministic 10,000-case semantic mutation kill gate and the dedicated workflow re-executes the full 1,000,000 edge/typical/stress campaign on the repository branch.

## Metriche di accettazione

| Metric | Target |
|---|---:|
| public historical-pipeline imports | 0 |
| public star-imports | 0 |
| canonical mode drift | 0 |
| reachability oracle mismatches | 0 |
| semantic mutation survivors | 0 |
| platform identity decision mismatches | 0 |
| false bootstrap-ready without state carrier | 0 |
| connector-required on equivalent public source host | 0 |
| recovery-without-real-carrier claim | 0 |
| historical semantic regression | 0 |

## Non-goal

La v1.1 non rinomina o riscrive gli specialist proof engines solo per rimuovere numeri di versione dai filename. Il router esplicito resta l'owner della composizione e i proof engines restano authoritative per la loro semantica. Una futura migrazione dei moduli specialistici può avvenire soltanto con equivalence proof dedicata; non viene mescolata a questa PR host/public-path.
