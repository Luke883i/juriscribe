# Juriscribe agent runtime rules v0.5 — post-admission

Queste regole si applicano solo dopo receipt valida.

## Missione

Generare un capitolo giuridico `N+1` dai capitoli `1..N`. Un testo plausibile non è sufficiente: ogni bozza deve restare vincolata al reticolo epistemico, alle fonti e alla traiettoria dell'opera.

## UX

Dopo mining/reticolo mostra una configurazione raccomandata essenziale con due sole scelte: `ACCETTA CONSIGLIATI` o `MODIFICA`. Dopo l'accettazione l'utente attende il risultato; interrompere solo per una decisione interpretativa materialmente non inferibile.

## Invarianti pre-bozza

- reticolo epistemico validato prima del setup;
- parametri accettati → DoD bloccanti;
- generation contract legato a reticolo/setup;
- claim materiali circostanziati; inferenze forti con premesse/ponte/falsificatore;
- confronto con capitoli precedenti e bibliografia se disponibile.

## Invarianti post-bozza

- sigillare la prima bozza;
- eseguire review scientifico-editoriale secondo `JURISCRIBE_LEGAL_MONOGRAPH_V1` o standard esplicitamente più restrittivo;
- materializzare finding, scorecard ed evidenze;
- eseguire almeno una rigenerazione e provarne la preservazione epistemica;
- ripetere review/rigenerazione finché il candidato è `PASS_CANDIDATE`;
- chiudere la review solo dopo `P+10.000` no-novelty e `P+10.000` no-improvement-without-degradation;
- simulazione multi-classe legata al candidato;
- compressione lossless legata a candidato/inventario;
- quality/source recheck sul testo finale compresso;
- materializzazione/readback prima di `COMPLETE`.

## Standard e fonti

Il core review è publisher-neutral. Lo stile citazionale è quello del progetto/editor (`PROJECT_DEFINED` di default; OSCOLA è supportabile ma non imposto universalmente). “Dominante” è uno stato da dimostrare, non una formula retorica.

## node.h

`node.h` è generato a ogni save e contiene metadata/digest. Il completion gate richiede integrità dell'header corrente.

## Dashboard

La dashboard deve servire autore, responsabile scientifico e redazione: decisione di consegnabilità prima, blocker leggibili, poi evidenze. Non esporre chain-of-thought.
