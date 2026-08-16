# Juriscribe session model v0.9.2

Una sessione lega: request, bootstrap, mode selection, mode contract, editorial standard, corpus/concept/review target, reticolo, setup, DoD, fonti/claim/inferenze, eventuale generation/continuation contract, drafts o review target, review, provenance, final review, artifact registry, delivery evidence e completion evidence.

`session.integrity.json` è il manifest canonico interno. Il suo digest non contiene corpus text né chain-of-thought e non è un allegato ordinario.

La modalità è immutabile dopo l'ingestione sostanziale; per cambiare tipo di lavoro si apre una nuova sessione o si resetta prima del corpus.

## Delivery state

Gli artefatti hanno un confine esplicito fra `ATTACH` e `INTERNAL`. Solo i ruoli finali previsti dal mode contract possono diventare allegati ordinari. I documenti `ATTACH` devono essere DOCX materializzati e verificati; `session_dashboard` deve essere HTML.

La dashboard contiene un digest deterministico dello stato sostanziale della sessione. Il delivery gate ricalcola tale digest: una dashboard generata prima di una mutazione sostanziale è stale e non consente `COMPLETE`.

Il final delivery manifest registra per gli allegati path, formato, readback, size e SHA-256. Log, receipt, provenance raw, integrity e altri record macchina restano nello stato/ledger interno.
