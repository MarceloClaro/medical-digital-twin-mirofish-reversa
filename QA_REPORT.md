# QA Report — integração OpenCode CLI

Data da validação: 2026-07-23

## Resultados

- `compileall`: aprovado;
- `pytest`: 16 aprovados;
- runner JSON OpenCode: smoke test aprovado;
- confinamento de caminhos: aprovado;
- criação de artefato auditável: aprovada;
- MiroFish sem configuração administrativa: bloqueado por teste;
- entrada real/identificável: recusada por teste;
- uso clínico e linguagem prescritiva: bloqueados por contrato.

## Validações não executadas neste ambiente

- runtime real do OpenCode/Bun, ausente no container;
- MiroFish upstream;
- APIs de LLM ou Zep;
- Ruff e mypy, que permanecem definidos no CI;
- cobertura total recalculada após os novos módulos.

## Observação

A integração segue o formato oficial de custom tools, comandos, agents, skills e permissões do OpenCode. O GitHub Actions deve validar instalação, lint, tipagem, testes e build após a abertura do PR.
