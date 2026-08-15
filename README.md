# Juriscribe

Juriscribe è un **runtime per continuare una monografia giuridica**: parte dai capitoli già scritti, li scompone in unità epistemiche, costruisce un reticolo verificabile e genera il capitolo successivo sotto vincoli di fonti, inferenze, continuità, review e provenance.

Non è un prompt di scrittura. Il suo obiettivo è rendere difficile consegnare un testo semplicemente plausibile ma scollegato dall'opera, non circostanziato o non auditabile.

## Avvio rapido in una chat AI

Puoi usarlo senza conoscere Python o Git.

1. Apri una sessione su **https://chatgpt.com/** o un host compatibile.
2. Fornisci `https://github.com/Luke883i/juriscribe` oppure un bundle locale.
3. Chiedi: **“Avvia il bootstrap Juriscribe da questo repository/bundle e guidami nella generazione del capitolo successivo.”**
4. L'AI deve fermarsi e mostrarti i T&C. Se vuoi procedere, scrivi esattamente **`I ACCEPT`**.
5. L'AI deve poi mostrarti **`PROBE JURISCRIBE`**. Sceglilo per verificare le capacità effettive dell'host e produrre la probe receipt.
6. Solo dopo il probe l'AI deve mostrarti **`INITIALIZE JURISCRIBE`**. Sceglilo per creare la sessione.
7. Solo quando la sessione è `ACTIVE` fornisci i capitoli precedenti, bibliografia e materiali editoriali.
8. Al setup puoi normalmente scegliere **`ACCETTA CONSIGLIATI`**, **`MODIFICA`** oppure **`ALTRO`** per una richiesta libera.

Un assistente che trova il repository tramite web browsing non dovrebbe saltare questi passaggi: discovery, accettazione, probe e initialize sono stati distinti.

## Cosa succede prima di scrivere N+1

I capitoli `1..N` diventano un inventario di claim, definizioni, regole, eccezioni, qualificazioni, argomenti, controargomenti, conclusioni, questioni aperte, fonti e inferenze. Ogni unità materiale deve essere rintracciabile nel corpus.

Le unità vengono collegate in un **reticolo semantico tipizzato**. Dal reticolo nasce un `generation_contract` e un **continuation frontier**: cosa va preservato, cosa va sviluppato, con quale profondità, cosa non va duplicato. L'esatta sequenza del futuro capitolo non è un target: Juriscribe valuta robustezza e copertura, non capacità di indovinare l'indice dell'autore.

## La pipeline completa

```text
BOOTSTRAP ACTIVE
→ CAPITOLI PRECEDENTI + BIBLIOGRAFIA
→ MINING ATOMICO
→ RETICOLO
→ CONTINUATION FRONTIER
→ SETUP + DoD
→ GENERATION CONTRACT
→ FONTI / CLAIM / INFERENZE
→ BOZZA SIGILLATA
→ REVIEW SCIENTIFICO-EDITORIALE
→ RIGENERAZIONE
→ NUOVA REVIEW
→ P+10.000
→ SIMULAZIONI
→ COMPRESSIONE LOSSLESS
→ QUALITY / SOURCE / CONTINUATION RECHECK
→ PROVENANCE LOSSLESS
→ REVIEW FINALE GIURIDICO-EDITORIALE-LOGICO-CONSEQUENZIALE
→ M+10.000
→ ARTEFATTI FINALI + READBACK
→ COMPLETE
```

La prima bozza non è mai il risultato finale.

## Fonti e inferenze

Un claim materiale esterno non è verificato perché “sembra noto”. Le fonti effettivamente usate devono essere lette e, quando applicabile, registrate con perimetro, verifica, pinpoint e proposizione supportata.

Una **inferenza forte** richiede premesse, ponte inferenziale e falsificatore. “Dottrina dominante” o “giurisprudenza dominante” richiedono un corpus adeguato di autorità indipendenti: il ranking web non basta.

## Provenance: niente sparisce silenziosamente

Prima degli artefatti finali Juriscribe crea un provenance bundle legato al testo finale e al corpus. Ogni inferenza materiale registrata, claim materiale, decisione utente e trasformazione richiesta deve avere una sorte esplicita: `IN_FINAL`, `SUPERSEDED`, `REJECTED`, `DEFERRED` o `NOT_APPLICABLE`.

Questo non significa salvare chain-of-thought: si conservano solo oggetti auditabili — proposizioni, evidenze, inferenze esplicite, decisioni e trasformazioni.

## Ultima review prima della consegna

Dopo la compressione, ma prima di creare gli artefatti finali, Juriscribe esegue un'altra review severa sull'esatto candidato finale. Controlla quadro normativo globale applicabile, coerenza col seed, autorità e controautorità, conseguenze logiche/giuridiche, tempo e giurisdizione, integrità editoriale, provenance e losslessness.

## Artefatti finali

Una sessione completa produce almeno:

- capitolo finale;
- dossier delle evidenze;
- registro delle fonti;
- registro delle inferenze;
- ledger delle trasformazioni;
- dashboard di sessione.

L'obiettivo è permettere a un responsabile scientifico o redattore di controllare il risultato senza dover ricostruire la chat.

## Dashboard

`session-dashboard.html` è pensata prima per persone e poi per macchine. Mostra:

1. **Dove siamo** — pronto/non pronto e prossimo passo;
2. **Cosa è stato controllato** — card semplici;
3. **Evidenze circostanziate** — claim, fonte, perimetro, inferenza e locator finale;
4. **Storia delle revisioni** — finding, rigenerazioni, consequence probes e final review;
5. **Integrità tecnica** — digest e `node.h` in secondo piano.

## Scelte in chat

Juriscribe propone scelte standard per ridurre ambiguità, ma non chiude la conversazione. Ogni interaction card include **`ALTRO`** e consente richieste libere. Al termine propone normalmente `APRI ARTEFATTI`, `RICHIEDI MODIFICHE`, `NUOVO CAPITOLO`, `ALTRO`.

## CI/CD anti-regressione

Su pull request e push a `main`, GitHub Actions esegue compile/test su Python 3.10 e 3.12, integrità bootstrap/contratto/manifest, la baseline da **400.000** simulazioni v0.5, la saturazione architetturale `M+1000`, i **10.000** continuation scenarios v0.6 e ulteriori **10.000 mutazioni v0.7** su bootstrap, interaction, provenance, final review e artefatti.

I receipt di validazione vengono confrontati semanticamente per garantire fixed-point riproducibili.

## Limiti

Juriscribe non prova automaticamente la correttezza di una conclusione giuridica, non garantisce completezza assoluta della ricerca e non sostituisce il responsabile scientifico. Le metriche e simulazioni sono test computazionali del runtime, non migliaia di giudizi giuridici simulati.

## Versioni

- runtime: `0.7.0`
- access contract: `1.5.0`
- manifest: `juriscribe-manifest/v7`

Dopo bootstrap `ACTIVE`, vedi `docs/AGENT_RUNTIME_RULES.md`, `docs/RUNTIME_V7_FINALIZATION.md`, `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md` e `docs/BENCHMARK_MAINE_V7.md`.
