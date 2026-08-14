# Juriscribe

Juriscribe è un **agent repository** per progettare, scrivere, riorganizzare e verificare monografie giuridiche guidate da un giurista. L'assistente operativo è **iSeneca**.

## Esperienza essenziale

L'utente fornisce richiesta e materiali. iSeneca esegue mining profondo del contesto, propone una configurazione raccomandata e mostra soltanto due scelte: **ACCETTA CONSIGLIATI** oppure **MODIFICA**. Dopo l'accettazione, i parametri entrano nei DoD e iSeneca procede autonomamente fino a prova di completamento.

## Invarianti runtime

- deep mining di contenuto, relazioni e stile prima della generazione;
- parametri utente come DoD bloccanti;
- style fingerprint del corpus precedente e controllo di continuità;
- claim materiali circostanziati e fonti direttamente verificate;
- inferenza forte con premesse, ponte e falsificatore;
- nessuna dichiarazione di letteratura/giurisprudenza dominante da ranking web;
- completion gate: ogni DoD `DONE` + `M+10.000` no-novelty vs DoD + nessuna contraddizione bloccante;
- dashboard esclusivamente riferita alla sessione corrente.

Vedi `docs/RUNTIME_V2.md` e `AGENTS.md`.
