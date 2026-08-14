# iSeneca runtime v0.2 — deep mining, setup minimo, evidenza e completion gate

## Esperienza dell'utente

Dopo aver ricevuto i capitoli o gli altri materiali, iSeneca **non redige subito**. Prima esegue mining profondo e presenta una sola configurazione raccomandata, già compilata. L'utente vede soltanto due scelte: **ACCETTA CONSIGLIATI** e **MODIFICA**. La configurazione minima riguarda funzione del nuovo capitolo, lunghezza, profondità della ricerca/fonti e postura argomentativa. Ogni parametro accettato diventa un DoD bloccante.

## Mining profondo

Il mining combina baseline deterministica (lunghezza, paragrafi, ritmo, periodi, densità citazionale, connettori, qualificazioni, registro e ricorrenze) e annotazioni semantiche dell'host AI (tesi, argomenti, eccezioni, domande aperte, dipendenze, fonti, letteratura e giurisprudenza). Lo strato deterministico non viene presentato come comprensione giuridica completa.

## Style fingerprint

Il nuovo capitolo deve mantenere continuità su registro, lunghezza e struttura dei periodi, ampiezza dei paragrafi, connettori, densità e forma delle citazioni, ritmo argomentativo e rapporto tesi/qualificazioni/obiezioni/sintesi. La replica è continuità controllata, non imitazione cieca.

## Claim circostanziato

Ogni claim materiale prodotto usando ricerca esterna deve avere un record con perimetro, fonte o premesse, stato e — per inferenza forte — ponte inferenziale e falsificatore. La ricerca web è una capacità dell'host: il runtime prepara query-goal e criteri di fonte, quindi registra soltanto fonti effettivamente lette/verificate.

La posizione nei risultati di ricerca non dimostra dominanza. Letteratura o giurisprudenza possono essere marcate come dominanti soltanto dopo pluralità di fonti indipendenti, dirette e di sufficiente autorità.

## Saturazioni

- Riflessione architetturale: `1..M` + `100` challenge consecutivi senza novità materiale.
- Semantica/strategia: continuano i monitor esistenti.
- Completion gate: dopo che ogni DoD bloccante è `DONE`, servono `10.000` probe consecutivi senza novità materiale **rispetto ai DoD** e senza contraddizioni bloccanti.

`COMPLETE` è uno stato provato, non un'etichetta editoriale.
