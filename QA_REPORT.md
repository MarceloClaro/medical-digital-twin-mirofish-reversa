# QA Report — 0.1.0

Data da validação: 2026-07-23

## Resultados

- `compileall`: aprovado;
- `pytest`: 9 aprovados;
- cobertura: 84% total;
- build wheel: aprovado;
- smoke CLI: aprovado;
- entrada real/identificável: recusada por teste;
- prescrição e uso clínico: bloqueados por contrato.

## Artefato construído

`dist/opencode_medical_digital_twin_mirofish_reversa-0.1.0-py3-none-any.whl`

## Limitações da validação

- MiroFish upstream não foi iniciado;
- nenhuma API de LLM ou Zep foi chamada;
- nenhum dado real de paciente foi usado;
- o adaptador externo foi testado apenas com subprocesso fake JSON;
- lint Ruff e mypy permanecem definidos no CI, mas não foram executados neste ambiente por indisponibilidade local dos pacotes.
