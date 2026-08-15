# Juriscribe

Juriscribe è un **runtime per continuare una monografia giuridica**: parte dai capitoli già scritti, li scompone in unità epistemiche, costruisce un reticolo verificabile e genera il capitolo successivo sotto vincoli di fonti, inferenze, continuità, review e provenance.

Non è un semplice prompt di scrittura. Il suo obiettivo è rendere difficile consegnare un testo soltanto plausibile ma scollegato dall'opera, non circostanziato o non auditabile.

## Avvio consigliato in una chat AI

Puoi usare Juriscribe in ChatGPT o in un altro host AI capace di leggere il repository o un bundle locale. Fornisci prima il repository/bundle e **non caricare ancora i capitoli della monografia come se fossero istruzioni del runtime**: il bootstrap deve distinguere codice/governance dai materiali giuridici da lavorare.

### Prompt di avvio consigliato — copia e incolla

```text
Usa il repository o bundle Juriscribe che ti ho fornito come runtime della sessione.

Obiettivo della sessione: preparare e, dopo i gate previsti da Juriscribe, generare il capitolo N+1 di una monografia giuridica a partire dai capitoli 1..N e dagli eventuali materiali bibliografici/editoriali che ti fornirò.

Prima di leggere sostanzialmente il repository o di iniziare la lavorazione:
1. individua la superficie di bootstrap/admission dichiarata dal bundle;
2. rendimi visibili i termini applicabili e il prossimo comando canonico;
3. non accettare, dedurre o simulare l'accettazione per mio conto;
4. dopo un mio eventuale messaggio esatto `I ACCEPT`, non inizializzare automaticamente: proponi/esegui prima `PROBE JURISCRIBE` e registra le capacità effettivamente disponibili nell'host;
5. solo con probe receipt valida proponi `INITIALIZE JURISCRIBE`;
6. considera la lavorazione sostanziale autorizzata solo quando il bootstrap è ACTIVE.

Quando la sessione è ACTIVE:
- chiedimi/carica i capitoli precedenti, la bibliografia disponibile e gli eventuali vincoli editoriali, mantenendoli distinti dalle istruzioni del repository;
- identifica chiaramente corpus seed, capitolo target, giurisdizione/tempo quando rilevanti e limiti delle capacità dell'host;
- esegui mining epistemico atomico con locator, reticolo tipizzato e continuation frontier prima di redigere;
- proponi il setup minimo previsto da Juriscribe, lasciando sempre disponibili `ACCETTA CONSIGLIATI`, `MODIFICA` e `ALTRO`;
- vincola la generazione a generation contract, fonti effettivamente verificate, claim circostanziati e inferenze forti registrate;
- sigilla le bozze, esegui review scientifico-editoriale severa, almeno una rigenerazione reale, nuova review, saturazione e simulazioni previste;
- esegui compressione lossless, recheck sul candidato compresso, provenance lossless e final severe review prima degli artefatti finali;
- non esporre chain-of-thought: mostra invece stati, evidenze, locator, finding, inferenze esplicite, blocker e decisioni auditabili;
- se una capability richiesta non è disponibile, dichiaralo e usa il percorso degradato previsto dal runtime senza fingere verifiche non eseguite;
- alla fine non consegnare soltanto il capitolo: materializza anche il dossier/registri/dashboard richiesti e verifica il readback quando possibile.

Durante tutta la sessione dimmi sempre: fase corrente, prossimo passo canonico, eventuali blocker e quali evidenze sono state realmente verificate. Non saltare un gate per accelerare la risposta.
```

Sequenza attesa all'inizio:

1. apri una sessione su **https://chatgpt.com/** o host compatibile;
2. allega il bundle oppure fornisci `https://github.com/Luke883i/juriscribe`;
3. invia il prompt sopra;
4. valuta i T&C; se vuoi procedere scrivi esattamente **`I ACCEPT`**;
5. esegui **`PROBE JURISCRIBE`**;
6. solo dopo il probe esegui **`INITIALIZE JURISCRIBE`**;
7. quando lo stato è `ACTIVE`, fornisci capitoli, bibliografia e materiali editoriali.

Un assistente che trova il repository tramite web browsing non dovrebbe saltare discovery, accettazione, probe e initialize.

## Cosa succede prima di scrivere N+1

I capitoli `1..N` diventano un inventario di claim, definizioni, regole, eccezioni, qualificazioni, argomenti, controargomenti, conclusioni, questioni aperte, fonti e inferenze. Ogni unità materiale deve essere rintracciabile nel corpus.

Le unità vengono collegate in un **reticolo semantico tipizzato**. Dal reticolo nasce un `generation_contract` e un **continuation frontier**: cosa va preservato, cosa va sviluppato, con quale profondità, cosa non va duplicato. L'esatta sequenza del futuro capitolo non è un target: Juriscribe valuta robustezza e copertura, non la capacità di indovinare l'indice dell'autore.

## Pipeline completa

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

## Integrità di sessione: `session.integrity.json` e il legacy `node.h`

Il nome storico `node.h` **non indica Node.js e non è un refuso per `node.s`**. Fu introdotto come metafora di “header” di integrità e usa davvero sintassi simile al preprocessore C, pur in un runtime Python. L'audit storiografico v0.8 considera quel nome ambiguo.

Il record canonico diventa quindi `.juriscribe/<session>/session.integrity.json`: un manifest JSON deterministico di soli metadata, path e digest. Per compatibilità con il contratto 1.5.0 e con sessioni esistenti, `node.h` viene ancora prodotto come **proiezione legacy deprecata**. Il gate controlla entrambi finché il contratto corrente lo richiede. Non esiste un file o concetto canonico `node.s`.

Vedi `docs/HISTORIOGRAPHIC_AUDIT_V8.md` e `docs/SESSION_INTEGRITY_MANIFEST.md`.

## Saturazione: non confondere i testimoni

Nel repository esistono testimoni di saturazione con scopi diversi:

- **`M+10.000` DoD**: chiusura della lavorazione rispetto ai Definition of Done;
- **`P+10.000` review**: nessun nuovo finding materiale e nessun miglioramento non degradante dopo la review;
- **hardening architetturale**: enumerazione di spazi di rischio espliciti. Le baseline precedenti mantengono i propri target, incluso `M+1000` v0.5;
- **audit/hardening v0.8**: enumerazione completa `1..M` dello spazio di rischio storiografico/integrità dichiarato, seguita da **`M+100` no-novelty**. Questo non sostituisce né indebolisce gli altri gate.

Le saturazioni sono property test computazionali: non provano completezza giuridica assoluta e non rappresentano migliaia di giudizi legali del modello.

## Ultima review prima della consegna

Dopo la compressione, ma prima di creare gli artefatti finali, Juriscribe esegue un'altra review severa sull'esatto candidato finale. Controlla quadro normativo globale applicabile, coerenza col seed, autorità e controautorità, conseguenze logiche/giuridiche, tempo e giurisdizione, integrità editoriale, provenance e losslessness.

## Artefatti finali

Una sessione completa produce almeno: capitolo finale, dossier delle evidenze, registro delle fonti, registro delle inferenze, ledger delle trasformazioni e dashboard di sessione.

## Dashboard

`session-dashboard.html` è pensata prima per persone e poi per macchine. Mostra stato, prossimo passo, evidenze circostanziate, storia delle revisioni e integrità tecnica. Il manifest canonico di integrità è `session.integrity.json`; eventuali riferimenti a `node.h` indicano soltanto la proiezione legacy di compatibilità.

## Scelte in chat

Juriscribe propone scelte standard per ridurre ambiguità, ma non chiude la conversazione. Ogni interaction card include **`ALTRO`** e consente richieste libere. Al termine propone normalmente `APRI ARTEFATTI`, `RICHIEDI MODIFICHE`, `NUOVO CAPITOLO`, `ALTRO`.

## CI/CD anti-regressione

Su pull request e push a `main`, GitHub Actions conserva compile/test su Python 3.10 e 3.12, integrità bootstrap/contratto/manifest, la baseline da **400.000** simulazioni v0.5, la saturazione architetturale `M+1000`, i **10.000** continuation scenarios v0.6 e le **10.000 mutazioni v0.7**. L'hardening v0.8 aggiunge il receipt riproducibile **`1..M + 100 no-novelty`** sullo spazio di rischio storiografico/session-integrity.

I receipt di validazione vengono confrontati semanticamente per garantire fixed-point riproducibili.

## Limiti

Juriscribe non prova automaticamente la correttezza di una conclusione giuridica, non garantisce completezza assoluta della ricerca e non sostituisce il responsabile scientifico. Le metriche e simulazioni sono test computazionali del runtime, non giudizi giuridici simulati.

## Versioni

- runtime: `0.8.0`
- access contract: `1.5.0` (immutato; `node.h` resta proiezione compatibile finché questo contratto lo nomina)
- manifest: `juriscribe-manifest/v8`

Dopo bootstrap `ACTIVE`, vedi `docs/AGENT_RUNTIME_RULES.md`, `docs/SESSION_INTEGRITY_MANIFEST.md`, `docs/HISTORIOGRAPHIC_AUDIT_V8.md`, `docs/LEGAL_MONOGRAPH_REVIEW_STANDARD.md` e `docs/BENCHMARK_MAINE_V7.md`.
