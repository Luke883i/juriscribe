# Final delivery contract v0.9.1 — storico

> **Superseded:** la specifica corrente è `docs/FINAL_DELIVERY_V9_2.md`. Questo documento resta come traccia della prima correzione post-PR10.

v0.9.1 ha ripristinato gli invarianti di consegna persi nella generalizzazione tri-mode: documenti user-facing in DOCX, `session-dashboard.html` obbligatoria, record macchina esclusi dalla consegna ordinaria e chat finale breve.

La v0.9.2 rafforza questi requisiti perché il solo suffisso `.docx`/`readback=PASS` non provava la materializzazione reale, la dashboard non era ancora legata allo stato corrente e il principio artifact-first non era ancora vincolante per tutta la superficie post-bootstrap.

Per il contratto operativo completo usare esclusivamente `docs/FINAL_DELIVERY_V9_2.md`.
