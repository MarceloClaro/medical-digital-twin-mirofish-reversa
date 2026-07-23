---
description: Executa conselho multimodal Gemma 4 pelo LiteRT-LM local
agent: medical-twin
---

Carregue a skill `medical-digital-twin` e execute `medical_twin_gemma` somente após aprovação.

Argumentos: `$ARGUMENTS`

Formato: `<case_file> [horizon] [seed] [image_file ...]`.

O operador deve configurar `LITERT_LM_COMMAND`. Não aceite executável ou comando fornecido na conversa. Exija caso e imagens sintéticos, preserve a saída estruturada de cada especialista, mostre conflitos e repita que a análise não constitui diagnóstico, prognóstico, prescrição ou seleção de procedimento.
