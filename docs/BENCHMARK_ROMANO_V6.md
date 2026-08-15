# Benchmark Romano — lezione di hardening v0.6

## Protocollo

Il benchmark è stato generato alla cieca usando come corpus sostanziale soltanto la Parte I (§§1–24) di Santi Romano, *L'ordinamento giuridico*. Dopo la chiusura del candidato sintetico è stata rivelata e confrontata la Parte II reale.

Il confronto non usa la coincidenza dell'indice come metrica di qualità. L'ordine scientifico di un autore è solo una delle molte continuazioni plausibili.

## Risultato qualitativo

La versione sintetica ha anticipato correttamente il nucleo della Parte II: pluralità/autonomia degli ordinamenti, rapporti tra ordinamenti, rilevanza, subordinazione e relatività dell'illiceità. Ha però sviluppato in modo più astratto e compatto alcune dimensioni che la Parte II reale tratta attraverso una maggiore densità di famiglie istituzionali e distinzioni dei modi di rilevanza.

Sono stati classificati come **surplus plausibili**, non come errori, gli sviluppi sintetici su identità/continuità, conflitti di appartenenza e conseguenze interpretative.

## Opportunità generalizzabili

1. Rendere esplicito il frontier di sviluppo derivato dal reticolo.
2. Misurare profondità e copertura, non sola presenza nominale di un tema.
3. Rendere visibili famiglie di casi, controargomenti e distinzioni quando sono disponibili nel corpus/reticolo.
4. Impedire che sviluppo elegante di temi laterali mascheri omissioni core.
5. Permettere nuovo materiale solo con binding auditabile a frontier + fonte/inferenza.
6. Nei benchmark post-hoc separare omissione, sottosviluppo e surplus; disabilitare lo scoring della sequenza.

## Validazione v0.6

Il nuovo harness aggiunge 10.000 scenari strutturati unici su quattro assi: profondità core, sviluppo laterale, omissione e nuovo materiale non legato. Sono property tests osservabili, non catene di pensiero o 10.000 giudizi giuridici.
