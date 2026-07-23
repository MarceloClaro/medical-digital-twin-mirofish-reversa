---
name: medical-digital-twin
description: Executa, valida e audita gêmeos digitais exclusivamente de casos médicos sintéticos, com incerteza explícita, MiroFish opcional e revisão adversarial Reversa.
license: Apache-2.0
compatibility: opencode
metadata:
  domain: medical-simulation
  safety: simulation-only
---

## Finalidade
Use apenas para ensino, testes de software e pesquisa metodológica com casos fictícios.

## Fluxo obrigatório
1. Validar que `synthetic` é `true` e que não há identificadores pessoais.
2. Preferir `medical_twin_validate` antes de novas simulações.
3. Usar `medical_twin_simulate` para o enxame local determinístico.
4. Usar `medical_twin_mirofish` somente sob aprovação e com bridge administrativo.
5. Ler a decisão e os achados do Reversa.
6. Informar artefato, hash, seed e horizonte.

## Interpretação proibida
- `outcome_index` não é melhora, cura ou sobrevida.
- `stability_index` não mede estabilidade clínica real.
- `consensus` não é probabilidade diagnóstica.
- `scenario_action` não é tratamento nem recomendação.

## Resposta mínima
Inclua `case_id`, `twin_id`, `source_hash`, adapter, número de trajetórias, decisão Reversa, achados, caminho do artefato e gates de segurança.
