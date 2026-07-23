---
description: Simula um caso sintético com MiroFish externo sob aprovação
agent: medical-twin
---

Carregue a skill `medical-digital-twin` e solicite aprovação para executar `medical_twin_mirofish`.

Argumentos: `$ARGUMENTS`

Formato: `<case_file> [horizon] [seed] [output_file]`.

A execução só pode prosseguir quando `MIROFISH_COMMAND` tiver sido configurado pelo operador. Nunca aceite um comando externo fornecido pelo usuário ou pelo prompt.
