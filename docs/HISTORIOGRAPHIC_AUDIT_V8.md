# Audit storiografico del runtime — v0.8

## Perimetro e metodo

Questo audit ricostruisce l'evoluzione documentata dalle PR 1–7 e la confronta con lo stato di `main` successivo al merge della PR7. “Storiografico” qui significa ricostruzione delle intenzioni dichiarate, delle mutazioni terminologiche e della sedimentazione tecnica del repository; non pretende di sostituire un'analisi forense di ogni oggetto Git mai creato.

## Linea evolutiva

- **PR1** — nasce il runtime/session kernel: workspace, ledger, unità epistemiche, saturazione e dashboard.
- **PR2** — mining profondo, setup, DoD, fonti e completion gate; la riflessione architetturale è descritta come `1..M + 100 no-novelty`.
- **PR3** — quality/evidence gate e blind benchmark; l'hardening architetturale passa a un witness più ampio.
- **PR4** — reticolo obbligatorio e generation contract eseguibile prima della generazione.
- **PR5** — review/rigenerazione scientifico-editoriale post-bozza e introduzione esplicita di `.juriscribe/<session>/node.h` come “header locale” di soli digest/metadati.
- **PR6** — `node.h` viene portato a v3 e lega anche continuation plan/coverage.
- **PR7** — `node.h` arriva a v4 e lega bootstrap, interaction, provenance e final review.

La traiettoria complessiva è coerente: ogni release ha spostato più stato critico dalla prosa implicita a record verificabili e candidate-bound.

## Finding principale: che cos'è `node.h`?

`node.h` **non è Node.js**, non identifica un “nodo” del reticolo e non è l'abbreviazione di un inesistente `node.s`.

L'implementazione corrente chiarisce l'origine del nome: il file è materializzato come un vero e proprio header in stile C, con include guard e direttive `#define JURISCRIBE_*`. È quindi una metafora tecnica deliberata di “header di integrità”. Tuttavia:

1. Juriscribe è un runtime Python stdlib-only;
2. non esiste un consumatore C necessario al funzionamento;
3. `.h` induce ragionevolmente a pensare a C/C++ o a una dipendenza nativa;
4. `node` è già un termine semanticamente carico in un sistema a reticolo;
5. la documentazione precedente non spiegava l'origine né lo status del nome.

Conclusione: **non era un typo, ma è debito semantico/UX reale**.

## Decisione di hardening

Da v0.8 il record canonico è:

```text
.juriscribe/<session-id>/session.integrity.json
```

È un manifest JSON deterministico che contiene soltanto schema/tipo, ID sessione, fase/readiness, path relativi e digest dello stato materiale protetto dal runtime. Non contiene testo del corpus né chain-of-thought.

### Perché `node.h` non viene cancellato subito

Il contratto di accesso 1.5.0 nomina esplicitamente `node.h` e ne richiede l'integrità. Rimuoverlo nella stessa release trasformerebbe un chiarimento terminologico in un cambio materiale di protocollo e invaliderebbe compatibilità/sessioni esistenti.

Per questo v0.8 usa una migrazione a due livelli:

- `session.integrity.json` = **record canonico**;
- `node.h` = **proiezione legacy deprecata**, ancora prodotta e verificata finché il contratto 1.5.0 la richiede.

Un workspace legacy che possiede un `node.h` valido ma non il nuovo manifest può materializzare il manifest canonico al caricamento senza reinterpretare il contenuto giuridico.

## Finding secondario: deriva della parola “M”

La storia del repository usa lettere simili per witness diversi. Senza distinzione, il lettore può credere che siano lo stesso gate:

- `M+10.000` — no-novelty rispetto ai DoD/completion;
- `P+10.000` — saturazione della review post-rigenerazione;
- `Q+1000`/`M+1000` — hardening architetturale di release precedenti;
- `1..M + 100` — forma originaria della riflessione architetturale in PR2 e witness richiesto per questo audit v0.8.

La v0.8 documenta quindi sempre **scopo + target**, non soltanto la lettera.

## Saturazione v0.8

L'harness `scripts/reflect_v8.py` enumera un modello finito ed esplicito del rischio di questa modifica lungo otto dimensioni: presenza canonical/legacy, validità dei due record, fase, readiness, interfaccia, etichetta documentale e compatibilità contrattuale.

Il prodotto cartesiano forma `M`. Dopo aver enumerato `1..M`, l'harness esegue altri 100 probe deterministici che devono produrre solo firme già osservate. La receipt registra `M`, streak, digest e stato.

Questo dimostra la saturazione **del modello di rischio dichiarato**, non l'assenza universale di bug e non la correttezza di contenuti giuridici.

## Esiti di fine-tuning documentale

La v0.8 rende `session.integrity.json` il termine canonico nei documenti nuovi, conserva `node.h` solo come nome legacy spiegato, chiarisce che `node.s` non esiste, separa i diversi witness di saturazione e rende il prompt di onboarding della README operativo e circostanziato.

## Limite residuo

La completa rimozione di `node.h` richiede una futura modifica del contratto che elimini il riferimento normativo al legacy header. Fino ad allora la doppia verifica è intenzionale, non duplicazione accidentale.
