# Modello di sessione Juriscribe

## Per il giurista

Una sessione non e una chat lineare. iSeneca costruisce una rappresentazione aggiornata del lavoro in corso e la usa per evitare tre errori tipici: dimenticare elementi gia introdotti, contraddire parti precedenti e produrre piu testo di quanto serva.

Ogni nuovo prompt o documento viene scomposto in unita indipendenti e poi ricollocato nella struttura complessiva dell'opera. Il risultato e un reticolo navigabile: non solo "cosa dice il capitolo", ma che funzione svolge, da cosa dipende, cosa prepara e quali questioni lascia aperte.

La dashboard HTML e un verbale sintetico della **specifica lavorazione corrente**. Non mostra pensieri interni del modello; mostra invece dati controllabili: richiesta, materiali usati, metodo applicato, stato delle contraddizioni, strategia, DoD, simulazioni, modifiche editoriali e artefatti.

## Per l'agente

Workspace minimo:

```text
.juriscribe/<session-id>/
├── state.json
├── ledger/
│   ├── intake.jsonl
│   ├── epistemic.jsonl
│   ├── relations.jsonl
│   ├── contradictions.jsonl
│   ├── strategy.jsonl
│   └── validation.jsonl
└── artifacts/
    └── session-dashboard.html
```

`state.json` e una vista materializzata. I ledger append-only sono l'origine auditabile quando il runtime consente persistenza.

## Protodeterminismo

Il protodeterminismo non significa che due modelli linguistici produrranno parole identiche. Significa che, a parita di input e capacita, devono attraversare gli stessi **checkpoint osservabili** e rendere esplicite le deviazioni:

1. intake completo;
2. atomizzazione;
3. linking;
4. contraddizioni;
5. viste globale/locale/relazionale;
6. strategia e lunghezza;
7. DoD;
8. saturazione;
9. simulazione;
10. redazione/riorganizzazione;
11. lossless audit;
12. materializzazione/readback/dashboard.

## Budget di simulazione

Il valore standard massimo e 1.000.000 di casi sintetici per ciclo. I casi sono generati da famiglie e mutazioni; non sono equiparati a decisioni giuridiche reali. La finalita e uccidere mutazioni strutturali (perdita di concetti, contraddizioni, rottura di rinvii, fonti sospette, sovracompressione, failure di ambiente) e non creare una falsa misura di certezza.
