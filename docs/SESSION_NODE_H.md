# Session `node.h`

## Perché esiste

Ogni sessione Juriscribe ha più stati che devono restare sincronizzati: corpus, reticolo, setup, DoD, generation contract, candidato, review, bibliografia, simulazione e compressione. `node.h` è una piccola capsula locale di integrità che rende verificabili mismatch e receipt stale.

## Posizione

```text
.juriscribe/<session-id>/
├── state.json
├── node.h
├── ledger/
└── artifacts/
```

## Micro-struttura ex ante

`node.h` è generato deterministicamente da `juriscribe.node_header` e contiene **solo metadata/digest**, mai il testo della monografia.

Macro principali:

- `JURISCRIBE_NODE_H_VERSION`
- `JURISCRIBE_SESSION_ID`
- `JURISCRIBE_PHASE`
- `JURISCRIBE_CORPUS_SHA256`
- `JURISCRIBE_SOURCES_SHA256`
- `JURISCRIBE_CLAIMS_SHA256`
- `JURISCRIBE_SOURCE_INTELLIGENCE_SHA256`
- `JURISCRIBE_RETICULUM_SHA256`
- `JURISCRIBE_SETUP_SHA256`
- `JURISCRIBE_DOD_SHA256`
- `JURISCRIBE_GENERATION_CONTRACT_SHA256`
- `JURISCRIBE_CURRENT_CANDIDATE_SHA256`
- `JURISCRIBE_REVIEW_SHA256`
- `JURISCRIBE_BIBLIOGRAPHY_SHA256`
- `JURISCRIBE_SIMULATION_SHA256`
- `JURISCRIBE_COMPRESSION_SHA256`
- `JURISCRIBE_QUALITY_SHA256`
- `JURISCRIBE_BENCHMARK_SHA256`
- `JURISCRIBE_ARTIFACTS_SHA256`
- `JURISCRIBE_READY`

Più i puntatori relativi a `state.json`, `ledger/`, `artifacts/`.

## Regola

Il workspace rigenera `node.h` a ogni save. Prima del completion gate il runtime verifica che l'header corrisponda allo stato corrente. Un mismatch rende la sessione non consegnabile finché lo stato non viene riallineato.
