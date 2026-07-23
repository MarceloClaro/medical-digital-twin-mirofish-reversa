# Política de segurança médica

Este software é exclusivamente educacional, metodológico e experimental.

## Invariantes

1. Somente dados sintéticos.
2. Identificadores pessoais conhecidos são recusados.
3. `clinical_use_allowed=false`.
4. `prescription_allowed=false`.
5. `diagnostic_claim_allowed=false`.
6. `prognostic_claim_allowed=false`.
7. `procedure_selection_allowed=false`.
8. Revisão humana obrigatória.
9. Consenso do enxame ou conselho não é probabilidade clínica.
10. Ação de cenário não possui efeito causal presumido.
11. Especialistas que compartilham o mesmo modelo não são independentes.
12. Imagens só podem estar dentro do worktree e em PNG/JPEG/WEBP.
13. O adapter hermético não interpreta pixels.
14. LiteRT-LM e MiroFish exigem comandos administrativos fora do prompt.
15. Saídas livres ou sem schema são recusadas.

## Fora de escopo

- diagnóstico de pessoa real;
- prescrição, dose, suspensão ou troca de medicamentos;
- recomendação de procedimentos;
- dieta ou exercício individualizado;
- cálculo individual de risco;
- triagem de emergência;
- substituição de profissional habilitado;
- uso de prontuário identificável;
- laudo radiológico ou patológico;
- Grad-CAM ou mapa de atenção apresentado como explicação clínica validada;
- inferência causal a partir de concordância entre agentes.
