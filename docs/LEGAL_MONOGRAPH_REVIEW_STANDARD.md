# Juriscribe Legal Monograph Review Standard v1

## Scopo

Questo documento definisce il nucleo comune della review scientifico-editoriale di Juriscribe. Non pretende di sostituire la peer review umana né di imporre un unico stile editoriale a tutti gli ordinamenti.

Il nucleo è **publisher-neutral**: combina pratiche convergenti di editoria accademica e legal writing, mentre lo stile citazionale concreto resta configurabile dal progetto.

## Base esterna verificata

Fonti ufficiali consultate per il disegno v0.5 (verifica 2026-08-15):

- Oxford Faculty of Law, OSCOLA: https://www.law.ox.ac.uk/oscola — accuratezza nella citazione di autorità/materiali giuridici; uso ampio in scuole di diritto e editoria giuridica.
- Oxford Faculty of Law, notizia OSCOLA 5th ed. (25 marzo 2026): https://www.law.ox.ac.uk/content/news/fifth-edition-oxford-university-standard-citation-legal-authorities-published — principi dichiarati di coerenza e considerazione per il lettore.
- Oxford University Press, Style and references: https://academic.oup.com/pages/for-authors/books/the-book-publishing-process/writing-and-content-preparation/style-and-references — riferimenti chiari, completi, coerenti; stile da concordare con l'editor.
- Oxford University Press, Review: https://academic.oup.com/pages/for-authors/books/the-book-publishing-process/review — peer review per validare e migliorare; contributo alla letteratura, qualità, scopo, approccio, punti deboli/forti, pubblico e conoscenza corrente.
- Oxford Faculty of Law, Legal research skills: https://www.law.ox.ac.uk/legal-research-and-mooting-skills-programme/introduction — valutare autorità/aggiornamento delle risorse e citare anche idee, argomenti e parafrasi.

Queste fonti supportano criteri generali, non una pretesa di universalità. Le regole specifiche dell'editore, collana, rivista, ordinamento o autore prevalgono quando registrate nel setup.

## Criteri obbligatori

Il runtime usa gli ID definiti in `juriscribe.review.REVIEW_CRITERIA`:

1. **MONOGRAPHIC_CONTRIBUTION** — il capitolo svolge una funzione necessaria e non ripete ciò che i capitoli precedenti hanno già concluso.
2. **INTERCHAPTER_COHERENCE** — tesi, definizioni, eccezioni, rinvii e dipendenze restano coerenti col reticolo dell'opera.
3. **LEGAL_AUTHORITY** — claim materiali supportati da autorità adeguate, lette e circostanziate.
4. **CITATION_TRACEABILITY** — claim → fonte/premessa → pinpoint → posizione nell'artefatto.
5. **COUNTERAUTHORITY** — controautorità e obiezioni materialmente rilevanti non vengono occultate.
6. **TEMPORAL_JURISDICTION** — tempo, vigenza e giurisdizione sono qualificati quando incidono sul claim.
7. **INFERENCE_DISCIPLINE** — inferenze forti distinguibili dai fatti attestati, con premesse/ponte/falsificatore.
8. **TERMINOLOGY** — definizioni e termini tecnici stabili o variazioni motivate.
9. **STRUCTURE** — progressione proporzionata, gerarchia leggibile, assenza di over-sectioning artificiale.
10. **EDITORIAL_STYLE** — continuità di registro, densità e sintassi senza imitazione meccanica.
11. **BIBLIOGRAPHY_INTEGRITY** — coerenza tra fonti usate, apparato e bibliografia disponibile.
12. **LOSSLESS_PRESERVATION** — nessuna perdita silenziosa di tesi/regole/eccezioni/qualificazioni/dipendenze obbligatorie.
13. **AUDIENCE_FIT** — livello e chiarezza adeguati al lettore giuridico/scientifico dichiarato.

## Severità e soglie

- `BLOCKER`: impedisce la prosecuzione verso la consegna.
- `MAJOR`: richiede rigenerazione o decisione umana prima della chiusura.
- `MINOR`: miglioramento editoriale tracciato; non può mascherare un difetto sostanziale.
- `NOTE`: osservazione non bloccante.

I criteri marcati `blocking` richiedono score almeno `0.90` e nessun BLOCKER/MAJOR irrisolto. Gli altri richiedono almeno `0.80` per `PASS_CANDIDATE`. Le soglie sono policy runtime esplicite e modificabili solo con variazione tracciata del contratto/standard.

## Citation style

OSCOLA 5 è un riferimento forte per legal citation e può essere scelto dal progetto, ma Juriscribe non lo impone universalmente. `citation_style=PROJECT_DEFINED` significa: applicare lo stile accettato nel setup/editorial brief e valutarne coerenza, completezza e leggibilità.

## Ciclo di review

```text
SEALED INITIAL DRAFT
→ REVIEW CYCLE
→ FINDINGS + SCORECARD + EVIDENCE
→ REGENERATION
→ SEALED REGENERATED DRAFT
→ REVIEW CYCLE
→ ...
→ PASS_CANDIDATE
→ P+10.000 SATURATION
→ COMPRESSION
→ FINAL QUALITY/SOURCE RECHECK
```

Una review non è una lista generica: ogni finding BLOCKER/MAJOR deve avere locator nell'artefatto e azione proposta. La rigenerazione deve dichiarare finding affrontati realmente appartenenti al ciclo sorgente, `from_digest`/`to_digest` e inventario epistemico preservato; il candidato rigenerato deve poi ricevere un nuovo ciclo di review.

## Saturazione della review

La review termina solo quando coesistono:

- ultimo candidato `PASS_CANDIDATE`;
- nessun BLOCKER/MAJOR aperto;
- almeno una rigenerazione dopo la prima review;
- `10.000` challenge consecutivi senza nuova criticità;
- `10.000` challenge consecutivi senza miglioramento materiale ancora ottenibile senza degradazione;
- zero degradation escape.

Il contatore è evidenza computazionale/challenge-based: non rappresenta 10.000 catene di pensiero nascoste.
