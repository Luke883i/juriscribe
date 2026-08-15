# Juriscribe

Juriscribe è un **runtime per continuare una monografia giuridica**: prende i capitoli già scritti, ne ricostruisce struttura scientifica, tesi, regole, eccezioni, fonti, stile e relazioni, quindi genera il capitolo successivo sotto vincoli verificabili.

Non è un prompt che “scrive bene”. Il suo scopo è rendere più difficile che un'AI produca un capitolo plausibile ma scollegato dall'opera, privo di fonti circostanziate, troppo astratto rispetto ai nodi disponibili o editorialmente incoerente.

> **AI admission notice.** Un'AI che apre questo repository per conto di un utente deve prima seguire `AGENTS.md`, `ISENECA_ACCESS_CONTRACT.md` e `ADMISSION.json`. Il runtime sostanziale richiede l'accettazione umana esplicita dei T&C correnti.

## Uso rapido

1. Apri una nuova sessione su **https://chatgpt.com/** (o un altro host AI capace di leggere repository/bundle e creare file).
2. Fornisci il repository `https://github.com/Luke883i/juriscribe` oppure carica un bundle locale del repository.
3. Chiedi: **“Inizializza Juriscribe da questo repository/bundle e guidami nella generazione del capitolo successivo.”**
4. Se l'host segue il protocollo Juriscribe, presenta i T&C correnti: accettali solo se vuoi procedere.
5. Fornisci i capitoli già scritti e, se disponibile, bibliografia/fonti/materiali editoriali.
6. Juriscribe propone una configurazione essenziale. Normalmente basta scegliere **`ACCETTA CONSIGLIATI`** oppure **`MODIFICA`**.
7. Il sistema esegue mining, redazione, review, rigenerazione, verifiche e materializzazione; ti coinvolge di nuovo solo se esiste una scelta interpretativa realmente umana o un blocco non inferibile.

## Prima di scrivere N+1

I capitoli `1..N` vengono trasformati in **unità epistemiche atomiche**: claim, regole, definizioni, eccezioni, qualificazioni, argomenti, controargomenti, conclusioni, questioni aperte, fonti e decisioni editoriali.

Le unità vengono collegate in un **reticolo semantico tipizzato**. Ogni unità materiale deve essere rintracciabile nel corpus. Dopo il setup Juriscribe congela i DoD e crea un `generation_contract` legato al digest del reticolo, con ciò che deve essere preservato, sviluppato, distinto e non duplicato.

### Development frontier v0.6

Prima della bozza Juriscribe trasforma i nodi da sviluppare in un **development frontier**: obblighi core/supporting/optional, modalità argomentative, profondità minima e alternative non vincolanti. Non tenta di indovinare come requisito l'esatta sequenza scientifica del futuro autore: `sequence_is_binding=false`.

Dopo ogni mutazione del candidato il coverage viene invalidato e deve essere rieseguito. `COMPLETE` richiede che il testo finale sviluppi i core alla profondità prevista, raggiunga il budget ponderato di copertura e non usi temi laterali per mascherare omissioni core. Nuovo materiale è ammesso se collegato al frontier e a fonte/inferenza auditata.

## La prima bozza non è il risultato

```text
CAPITOLI PRECEDENTI
→ MINING ATOMICO
→ RETICOLO SEMANTICO
→ SETUP + DoD
→ GENERATION CONTRACT
→ DEVELOPMENT FRONTIER
→ FONTI / CLAIM / BIBLIOGRAFIA
→ BOZZA SIGILLATA
→ CONTINUATION COVERAGE
→ REVIEW SCIENTIFICO-EDITORIALE SEVERA
→ RIGENERAZIONE
→ NUOVA REVIEW
→ SATURAZIONE P + 10.000
→ SIMULAZIONI EDGE-CASE
→ COMPRESSIONE LOSSLESS
→ CONTINUATION + QUALITY + SOURCE RECHECK SUL TESTO FINALE
→ MATERIALIZZAZIONE + READBACK
→ COMPLETE
```

La review confronta il capitolo con i capitoli precedenti e con un nucleo publisher-neutral: contributo all'opera, coerenza inter-capitolo, autorità giuridiche, citazioni/pinpoint, controautorità, tempo/giurisdizione, inferenze, terminologia, struttura, stile, bibliografia, preservazione lossless e adeguatezza al lettore. La sintassi citazionale resta quella del progetto/editor.

## Fonti, inferenze e bibliografia

Un claim materiale esterno non è verificato perché “sembra noto”. Juriscribe richiede una fonte effettivamente letta o premesse registrate. Una **inferenza forte** richiede premesse, ponte inferenziale e falsificatore. “Letteratura dominante” o “giurisprudenza dominante” non possono derivare dal ranking web o dalla ripetizione; se la copertura non basta, il sistema deve dichiarare `DOMINANCE_NOT_ESTABLISHED`.

Se disponibile, la bibliografia dei capitoli precedenti diventa stato di sessione di prima classe, ma non sostituisce la verifica claim-level.

## Saturazione, simulazioni e benchmark

Juriscribe usa due fixed point principali:

- **DoD saturation:** almeno `M+10.000` challenge consecutivi senza novità materiale rispetto ai DoD;
- **review/regeneration saturation:** dopo l'ultima rigenerazione, `P+10.000` challenge consecutivi senza nuova criticità e senza miglioramento materiale ancora disponibile che non introduca degradazione.

Le simulazioni sono property/mutation/stress test computazionali, non giudizi giuridici simulati. La baseline v0.5 mantiene **400.000** casi multi-seed; v0.6 aggiunge **10.000 scenari unici** dedicati a omissione, profondità core, anticipazione e nuovo materiale non legato.

Nei benchmark ciechi ex post Juriscribe misura copertura, profondità, omissioni e surplus. **Non premia la coincidenza dell'ordine delle sezioni con il capitolo reale.** Vedi `docs/BENCHMARK_ROMANO_V6.md`.

## `node.h` e dashboard

Ogni workspace genera `.juriscribe/<session-id>/node.h`. v3 include anche il digest del development frontier/coverage per rilevare mismatch o stato stale.

`session-dashboard.html` è un fascicolo per autore, responsabile scientifico e redazione: la prima informazione è `PRONTO PER CONSEGNA` / `NON PRONTO`, con blocker leggibili. La dashboard mostra evidenze e stati; non espone chain-of-thought.

## CI/CD anti-regressione

Su pull request e push a `main`, GitHub Actions esegue:

- compile e unit/lifecycle test su Python 3.10 e 3.12;
- integrità admission/contratto/manifest;
- 400.000 simulazioni multi-seed v0.5;
- riflessione architetturale `1..M` + `M+1000`;
- **10.000 scenari unici di continuation coverage v0.6**;
- fixed-point semantico dei receipt `validation/`.

Una modifica del comportamento che rende stale le baseline o riapre un gate fallisce la CI.

## Limiti dichiarati

Juriscribe non prova automaticamente che una conclusione giuridica sia corretta, non garantisce completezza assoluta della ricerca, non elimina la conoscenza pregressa del modello e non sostituisce il giudizio del responsabile scientifico. Non pretende inoltre di ricostruire l'esatta futura sequenza scientifica di un autore. Il runtime rende però più osservabili omissioni, sottosviluppi, drift, fonti non circostanziate, inferenze deboli, duplicazioni e trasformazioni editoriali non lossless.

## Versioni

- runtime: `0.6.0`
- access contract: `1.4.0`
- manifest: `juriscribe-manifest/v6`

Dopo ammissione valida, vedi `docs/AGENT_RUNTIME_RULES.md`, `docs/RUNTIME_V6_CONTINUATION_COVERAGE.md`, `docs/RUNTIME_V5_REVIEW_LOOP.md` e `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md`.
