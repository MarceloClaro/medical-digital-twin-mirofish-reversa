# Gemma 4 multimodal com LiteRT-LM

## Escopo

A integração usa Gemma 4 como modelo multimodal local para produzir opiniões estruturadas de casos sintéticos. O modelo não recebe autoridade para diagnosticar, prescrever, selecionar procedimento ou emitir prognóstico.

## Arquitetura

```text
OpenCode medical_twin_gemma
        ↓ aprovação
OpenCodeBridge
        ↓ LITERT_LM_COMMAND
LiteRTLMExternalAdapter
        ↓ JSON stdin/stdout
scripts/litert_lm_openai_bridge.py
        ↓ loopback HTTP
Servidor OpenAI-compatible do LiteRT-LM
        ↓
Gemma 4 local
```

O projeto não fixa a sintaxe de inicialização do servidor porque ela pode mudar entre versões. Use o comando documentado pela versão instalada e confirme o endpoint OpenAI-compatible.

## Configuração

```bash
export LITERT_LM_BASE_URL=http://127.0.0.1:8000/v1
export LITERT_LM_MODEL=gemma-4
export LITERT_LM_COMMAND="python3 scripts/litert_lm_openai_bridge.py"
```

Por padrão, o bridge aceita apenas loopback. A liberação remota exige `LITERT_LM_ALLOW_REMOTE=1`.

## Ordem multimodal

O bridge coloca imagens antes do texto. Formatos permitidos: PNG, JPEG e WEBP. Limites: 10 imagens, 20 MiB por imagem, caminhos dentro do worktree e `synthetic: true`.

## Contrato de saída

A saída contém `observations`, `claims`, `must_not_miss`, `missing_information`, `intervention_questions`, `limitations`, `confidence` e `evidence_strength`. Saídas livres, sem JSON ou sem campos obrigatórios são recusadas.

## Limitações

- Gemma 4 é multimodal geral, não dispositivo médico validado.
- Especialistas podem compartilhar o mesmo modelo-base.
- Validação cruzada entre prompts do mesmo modelo não equivale a validação externa.
- DICOM, volumes CT/MRI e histopatologia exigem pipelines próprios.
- Mapas de atenção não devem ser apresentados como Grad-CAM validado.
