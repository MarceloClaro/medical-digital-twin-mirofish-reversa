# SPEC-001 — Gêmeo digital médico simulado com MiroFish e Reversa

## Objetivo
Produzir trajetórias contrafactuais reproduzíveis para casos inteiramente sintéticos.

## Critérios de aceite
- CA01: recusar `synthetic=false`.
- CA02: recusar identificadores pessoais proibidos.
- CA03: gerar entre 2 e 12 estados.
- CA04: anexar dispersão e consenso do enxame.
- CA05: declarar que consenso não é probabilidade clínica.
- CA06: executar revisão Reversa.
- CA07: bloquear linguagem prescritiva.
- CA08: gerar SHA-256 canônico.
- CA09: reproduzir trajetória com mesmo caso/seed/adaptador.
- CA10: manter todos os gates clínicos fechados.
