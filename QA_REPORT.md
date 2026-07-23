# QA Report — 0.2.0

Data da validação: 2026-07-23

## Resultados locais

- `compileall`: aprovado;
- `pytest`: 28 aprovados;
- cobertura total: 87%;
- wheel 0.2.0: construído com `pip wheel --no-deps --no-build-isolation`;
- smoke OpenCode runner: aprovado;
- conselho hermético: aprovado;
- gêmeo vinculado ao conselho: aprovado;
- pesos somando 1: aprovado;
- conflito entre claims preservado: aprovado;
- imagem fora do formato: recusada;
- caminho fora do worktree: recusado;
- LiteRT-LM sem configuração: bloqueado;
- endpoint LiteRT-LM remoto: bloqueado por padrão;
- ordem imagem antes de texto: testada;
- dados reais/identificáveis: recusados pelos gates existentes;
- diagnóstico, prognóstico e prescrição: bloqueados por contrato.

## Cobertura

```text
TOTAL 652 statements, 87 missed, 87%
```

A CLI Python standalone permanece sem cobertura direta; motor, council, adapters, bridge e contratos possuem cobertura majoritária.

## Limitações da validação

- Gemma 4 e o servidor LiteRT-LM real não foram iniciados;
- MiroFish upstream não foi iniciado;
- nenhuma API externa foi chamada;
- nenhuma imagem clínica real foi usada;
- Ruff e mypy não estavam instalados no ambiente local;
- os gates Ruff/mypy permanecem no GitHub Actions;
- os runners GitHub Actions do repositório vinham falhando antes de registrar etapas, condição externa ao teste local.

## Artefato construído

```text
opencode_medical_digital_twin_mirofish_reversa-0.2.0-py3-none-any.whl
sha256: 22426ef91c1cda0993fa512bc35380e76f5bd03963c9a972f04241ea163a1ddb
```
