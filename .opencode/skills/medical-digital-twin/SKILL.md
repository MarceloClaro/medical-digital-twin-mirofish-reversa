---
name: medical-digital-twin
description: Executa, valida e audita gêmeos digitais e conselhos multimodais exclusivamente de casos médicos sintéticos, com MiroFish, Gemma/LiteRT-LM e Reversa opcionais.
license: Apache-2.0
compatibility: opencode
metadata:
  domain: medical-simulation
  safety: simulation-only
  contract: medical-specialist-council/1.0
---

## Finalidade
Use apenas para ensino, testes de software, residência simulada e pesquisa metodológica com casos fictícios.

## Fluxo obrigatório
1. Validar que `synthetic` é `true` e que não há identificadores pessoais.
2. Preferir `medical_twin_validate` antes de novas simulações.
3. Usar `medical_twin_simulate` para o gêmeo local determinístico.
4. Usar `medical_twin_council` para conselho hermético e validação cruzada.
5. Usar `medical_twin_mirofish` somente sob aprovação e bridge administrativo.
6. Usar `medical_twin_gemma` somente sob aprovação e `LITERT_LM_COMMAND` administrativo.
7. Ler a decisão e os achados do Reversa.
8. Informar artefato, hashes, seed, horizonte, especialistas, conflitos e limitações.

## Conselho de especialistas
- A primeira rodada deve permanecer independente.
- Claims devem ser comparados por `claim_id`, stance e confiança.
- Pesos `nash-product-inspired` não são prova clínica.
- Divergências e opiniões minoritárias não podem ser apagadas.
- Especialistas que usam o mesmo modelo-base têm independência epistêmica limitada.
- Intervenções aparecem somente como perguntas para revisão humana.

## Interpretação proibida
- `outcome_index` não é melhora, cura ou sobrevida.
- `stability_index` não mede estabilidade clínica real.
- `consensus` não é probabilidade diagnóstica.
- peso de especialista não é autoridade profissional.
- `scenario_action` não é tratamento nem recomendação.
- observação visual do Gemma não é laudo, segmentação ou Grad-CAM validado.

## Resposta mínima
Inclua `case_id`, `twin_id` ou `council_id`, hash, adapter, especialistas, conflitos, decisão Reversa, caminho do artefato e gates de segurança.
