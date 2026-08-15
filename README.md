# Juriscribe

Juriscribe è un **runtime per continuare una monografia giuridica**: prende i capitoli già scritti, ne ricostruisce struttura scientifica, tesi, regole, eccezioni, fonti, stile e relazioni, quindi genera il capitolo successivo sotto vincoli verificabili.

Non è un prompt che “scrive bene”. Il suo scopo è rendere più difficile che un'AI produca un capitolo plausibile ma scollegato dall'opera, privo di fonti circostanziate o editorialmente incoerente.

> **AI admission notice.** Un'AI che apre questo repository per conto di un utente deve prima seguire `AGENTS.md`, `ISENECA_ACCESS_CONTRACT.md` e `ADMISSION.json`. Il runtime sostanziale richiede l'accettazione umana esplicita dei T&C correnti.

## Uso rapido

Per un uso conversazionale non serve conoscere Python o Git.

1. Apri una nuova sessione su **https://chatgpt.com/** (o un altro host AI capace di leggere repository/bundle e creare file).
2. Fornisci il repository `https://github.com/Luke883i/juriscribe` oppure carica un bundle locale del repository.
3. Chiedi, ad esempio: **“Inizializza Juriscribe da questo repository/bundle e guidami nella generazione del capitolo successivo.”**
4. Se l'host segue il protocollo Juriscribe, presenta i T&C correnti: accettali solo se vuoi procedere.
5. Fornisci i capitoli già scritti e, se disponibile, bibliografia/fonti/materiali editoriali.
6. Juriscribe propone una configurazione essenziale. Normalmente basta scegliere **`ACCETTA CONSIGLIATI`** oppure **`MODIFICA`**.
7. Il sistema esegue mining, redazione, review, rigenerazione, verifiche e materializzazione; ti coinvolge di nuovo solo se esiste una scelta interpretativa realmente umana o un blocco non inferibile.

## Cosa deve succedere prima che venga scritto N+1

I capitoli `1..N` vengono trasformati in un inventario di **unità epistemiche atomiche**: claim, regole, definizioni, eccezioni, qualificazioni, argomenti, controargomenti, conclusioni, questioni aperte, fonti e decisioni editoriali.

Le unità vengono collegate in un **reticolo semantico tipizzato**. Ogni unità materiale deve essere rintracciabile nel corpus. Il setup non viene proposto finché il reticolo non supera il validator.

Dopo l'accettazione dei pochi parametri editoriali, Juriscribe congela i DoD e crea un `generation_contract` legato al digest del reticolo. Quel contratto identifica ciò che deve essere preservato, sviluppato, distinto e non duplicato.

## La prima bozza non è il risultato

La pipeline v0.5 tratta la prima bozza come **oggetto da confutare e migliorare**:

```text
CAPITOLI PRECEDENTI
→ MINING ATOMICO
→ RETICOLO SEMANTICO
→ SETUP + DoD
→ GENERATION CONTRACT
→ FONTI / CLAIM / BIBLIOGRAFIA
→ BOZZA SIGILLATA
→ REVIEW SCIENTIFICO-EDITORIALE SEVERA
→ RIGENERAZIONE
→ NUOVA REVIEW
→ SATURAZIONE P + 10.000
→ SIMULAZIONI EDGE-CASE
→ COMPRESSIONE LOSSLESS
→ RECHECK SUL TESTO FINALE
→ MATERIALIZZAZIONE + READBACK
→ COMPLETE
```

La review confronta il capitolo con i capitoli precedenti e con un nucleo publisher-neutral di criteri di redazione monografica: contributo all'opera, coerenza inter-capitolo, autorità giuridiche, tracciabilità delle citazioni, controautorità, perimetro temporale/giurisdizionale, disciplina inferenziale, terminologia, struttura, stile, bibliografia, preservazione lossless e adeguatezza al lettore.

La sintassi citazionale non è hard-coded: il progetto può adottare OSCOLA o lo stile richiesto dall'editore/ordinamento. Vedi `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md`.

## Fonti e inferenze

Un claim materiale esterno non è verificato perché “sembra noto”. Juriscribe richiede una fonte effettivamente letta o premesse registrate. Per le fonti usate come supporto materiale il ledger registra, quando applicabile, fonte, verifica, perimetro, pinpoint e proposizione supportata.

Una **inferenza forte** resta distinta da un fatto attestato e richiede premesse, ponte inferenziale e falsificatore. Le catene cicliche vengono respinte. “Letteratura dominante” o “giurisprudenza dominante” non possono derivare dal ranking web o dalla ripetizione: se la copertura non basta, il sistema deve dichiarare `DOMINANCE_NOT_ESTABLISHED`.

## Bibliografia

Se disponibile, la bibliografia dei capitoli precedenti diventa stato di sessione di prima classe. Può orientare ricerca e continuità, ma non sostituisce la verifica claim-level. Le fonti effettivamente usate per claim materiali devono essere mappabili all'apparato bibliografico quando tale apparato esiste.

## Saturazione e simulazioni

Juriscribe usa due fixed point distinti:

- **DoD saturation:** almeno `M+10.000` challenge consecutivi senza novità materiale rispetto ai DoD;
- **review/regeneration saturation:** dopo l'ultima rigenerazione, `P+10.000` challenge consecutivi senza nuova criticità **e** senza miglioramento materiale ancora disponibile che non introduca degradazione.

Le simulazioni sono property/mutation/stress test computazionali: non vengono rappresentate come centinaia di migliaia di giudizi giuridici o chiamate LLM.

La baseline v0.5 documenta 400.000 casi, divisi in parti uguali fra avversi, favorevoli, stress, review editoriale e review logico-semantica. Vedi `validation/simulation-v5.json` e `docs/RUNTIME_V5_REVIEW_LOOP.md`.

## `node.h`: indice locale della sessione

Ogni workspace genera `.juriscribe/<session-id>/node.h`. Non contiene il testo giuridico: contiene digest e puntatori dello stato corrente per collegare corpus, reticolo, setup, DoD, generation contract, candidato, review, bibliografia, simulazioni e compressione. Serve a rilevare mismatch/stato stale fra passaggi. Vedi `docs/SESSION_NODE_H.md`.

## Dashboard

`session-dashboard.html` è un **fascicolo di lavorazione per autore, responsabile scientifico e redazione**. La prima informazione è `PRONTO PER CONSEGNA` / `NON PRONTO`, con i blocker leggibili. Seguono mappa scientifica, continuità monografica, review/rigenerazioni, fonti e bibliografia, inferenze, DoD, simulazioni, saturazione, compressione, limiti e artefatti.

La dashboard mostra evidenze e stati; non espone chain-of-thought.

## CI/CD anti-regressione

Su pull request e push a `main`, GitHub Actions esegue:

- compile e unit/lifecycle test su Python 3.10 e 3.12;
- integrità admission/contratto/manifest;
- **400.000 simulazioni multi-seed** sulle cinque classi di rischio;
- riflessione architetturale `1..M` + `M+1000` senza nuova firma;
- fixed-point dei receipt `validation/`.

Una modifica del comportamento che rende stale le baseline o riapre un gate fallisce la CI.

## Limiti dichiarati

Juriscribe non prova automaticamente che una conclusione giuridica sia corretta, non può garantire completezza assoluta della ricerca, non elimina la conoscenza pregressa del modello e non sostituisce il giudizio del responsabile scientifico. Il runtime rende però più osservabili omissioni, drift, fonti non circostanziate, inferenze deboli, duplicazioni e trasformazioni editoriali non lossless.

## Versioni

- runtime: `0.5.0`
- access contract: `1.4.0`
- manifest: `juriscribe-manifest/v5`

Dopo ammissione valida, vedi `docs/AGENT_RUNTIME_RULES.md`, `docs/RUNTIME_V5_REVIEW_LOOP.md` e `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md`.
