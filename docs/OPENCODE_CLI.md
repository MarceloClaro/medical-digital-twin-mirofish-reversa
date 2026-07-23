# Integração com OpenCode CLI

## Componentes

- `.opencode/tools/medical_twin.ts`: ferramentas tipadas carregadas pelo OpenCode;
- `.opencode/tools/medical_twin_runner.py`: processo JSON que inicializa o layout `src/`;
- `.opencode/agents/medical-twin.md`: agente de mínimo privilégio;
- `.opencode/commands/`: comandos TUI;
- `.opencode/skills/medical-digital-twin/SKILL.md`: procedimento reutilizável;
- `opencode.json`: instruções e exclusões do watcher.

## Ferramentas

| Ferramenta | Função | Permissão |
|---|---|---|
| `medical_twin_validate` | valida caso sintético | allow |
| `medical_twin_simulate` | gêmeo hermético | allow |
| `medical_twin_council` | conselho hermético | allow |
| `medical_twin_mirofish` | simulação MiroFish externa | ask |
| `medical_twin_gemma` | conselho Gemma/LiteRT-LM | ask |

## Execução no TUI

```bash
opencode .
```

Dentro do OpenCode:

```text
/medical-twin examples/synthetic_case.json 4 42
/medical-twin-validate examples/synthetic_case.json
/medical-twin-council examples/synthetic_council_case.json 4 42
```

Artefatos:

```text
.opencode/artifacts/medical-twin/<twin_id>.json
.opencode/artifacts/medical-council/<council_id>.json
```

## Execução headless

```bash
opencode run --agent medical-twin \
  "Valide e execute um conselho hermético para examples/synthetic_council_case.json."
```

## Gemma 4 / LiteRT-LM

Configure fora do prompt:

```bash
export LITERT_LM_BASE_URL=http://127.0.0.1:8000/v1
export LITERT_LM_MODEL=gemma-4
export LITERT_LM_COMMAND="python3 scripts/litert_lm_openai_bridge.py"
opencode .
```

Depois use:

```text
/medical-twin-gemma examples/synthetic_council_case.json 4 42 caminho/imagem.png
```

A ferramenta está marcada como `ask`. O prompt não pode fornecer ou alterar o comando externo. O bridge bloqueia endpoint remoto por padrão.

## MiroFish externo

```bash
export MIROFISH_COMMAND="python3 scripts/mirofish_bridge_example.py"
opencode .
```

```text
/medical-twin-mirofish examples/synthetic_case.json 4 42
```

## Segurança

O agente não possui permissão para `bash`, edição ou escrita genérica. Os artefatos são gravados pelo bridge tipado dentro do worktree. Caminhos externos ou com escape por `..` são recusados. Conselho e modelos permanecem `simulation-only`.
