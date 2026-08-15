# PR7 validation scope

PR7 conserva integralmente le baseline v0.5/v0.6 e aggiunge il mutation harness v0.7.

CI obbligatoria:

- Python 3.10/3.12 compile + full unittest suite;
- contract/bootstrap/manifest/onboarding integrity;
- 400.000 simulazioni v0.5;
- M+1000 hardening saturation v0.5;
- 10.000 continuation scenarios v0.6;
- 10.000 mutazioni v0.7;
- fixed-point semantico dei quattro receipt.

Le 10.000 mutazioni v0.7 coprono dieci famiglie con selezione round-robin deterministica e firme SHA-256 uniche. I numeri rappresentano test del runtime, non giudizi giuridici o chiamate LLM.
