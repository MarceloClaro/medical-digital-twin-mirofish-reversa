# Integração com OpenCode CLI

## Componentes

- `.opencode/tools/medical_twin.ts`: ferramentas tipadas carregadas pelo OpenCode;
- `.opencode/tools/medical_twin_runner.py`: processo JSON que inicializa o layout `src/`;
- `.opencode/agents/medical-twin.md`: agente de mínimo privilégio;
- `.opencode/commands/`: comandos TUI;
- `.opencode/skills/medical-digital-twin/SKILL.md`: procedimento reutilizável;
- `opencode.json`: instruções e exclusões do watcher.

## Execução no TUI

```bash
opencode .
```

Dentro do OpenCode:

```text
/medical-twin examples/synthetic_case.json 4 42
/medical-twin-validate examples/synthetic_case.json
```

O resultado completo é gravado por padrão em:

```text
.opencode/artifacts/medical-twin/<twin_id>.json
```

## Execução headless

```bash
opencode run --agent medical-twin \
  "Valide e simule examples/synthetic_case.json com medical_twin_simulate, horizonte 4 e seed 42."
```

## MiroFish externo

Configure o bridge fora do prompt:

```bash
export MIROFISH_COMMAND="python3 scripts/mirofish_bridge_example.py"
opencode .
```

Depois use:

```text
/medical-twin-mirofish examples/synthetic_case.json 4 42
```

A ferramenta MiroFish está marcada como `ask`. O prompt não pode fornecer ou alterar o comando externo.

## Segurança

O agente não possui permissão para `bash`, edição ou escrita genérica. Os artefatos são gravados pelo bridge tipado dentro do worktree. Caminhos externos ou com escape por `..` são recusados.
