# opencode_medical-digital-twin-mirofish-reversa

Projeto local-first para criar **gêmeos digitais e conselhos multimodais de especialistas sobre casos médicos inteiramente sintéticos**, com MiroFish, Gemma 4/LiteRT-LM e auditoria Reversa opcionais.

> **Não é dispositivo médico, não diagnostica, não prescreve, não seleciona procedimentos e não aceita dados reais de pacientes.**

## Estado

Alpha experimental, versão 0.2.0. O modo padrão é hermético, local, sem LLM e reproduzível.

## Recursos

- casos exclusivamente sintéticos;
- rejeição de campos identificáveis;
- trajetórias T0..Tn com incerteza explícita;
- gêmeo digital ligado ao conselho de especialistas;
- especialistas de clínica, radiologia, farmacologia, procedimentos, nutrição, exercício e metodologia;
- rodada independente e validação cruzada por claims;
- dissenso preservado;
- ponderação `nash-product-inspired`, sem votação majoritária ingênua;
- adapter multimodal hermético que não interpreta pixels;
- adapter externo Gemma 4/LiteRT-LM;
- adapter MiroFish por JSON stdin/stdout;
- auditoria Reversa para completude, excesso de confiança, dependência e causalidade;
- SHA-256, IDs estáveis, schemas e artefatos auditáveis;
- integração direta com o OpenCode CLI;
- zero dependências obrigatórias em runtime Python.

## Instalação

```bash
git clone https://github.com/MarceloClaro/medical-digital-twin-mirofish-reversa.git
cd medical-digital-twin-mirofish-reversa
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## OpenCode CLI

```bash
opencode .
```

Comandos:

```text
/medical-twin-validate examples/synthetic_case.json
/medical-twin examples/synthetic_case.json 4 42
/medical-twin-council examples/synthetic_council_case.json 4 42
/medical-twin-gemma examples/synthetic_council_case.json 4 42 caminho/imagem.png
```

O modo Gemma exige aprovação e configuração administrativa:

```bash
export LITERT_LM_BASE_URL=http://127.0.0.1:8000/v1
export LITERT_LM_MODEL=gemma-4
export LITERT_LM_COMMAND="python3 scripts/litert_lm_openai_bridge.py"
```

O comando exato para iniciar o servidor OpenAI-compatible deve seguir a documentação da versão instalada do LiteRT-LM.

## Conselho de especialistas

```text
SimulationCase sintético
        ↓
Especialistas independentes
        ↓
Claims estruturados
        ↓
Validação cruzada
        ↓
Pesos nash-product-inspired
        ↓
Reversa adversarial
        ↓
Medical Digital Twin
        ↓
Artefato simulation-only
```

O consenso não é probabilidade diagnóstica. Especialistas que compartilham Gemma 4 continuam dependentes do mesmo modelo-base; essa limitação é registrada no artefato.

## Simulação Python

```bash
medical-twin examples/synthetic_case.json --seed 42 --horizon 4 --output result.json
```

## Integração MiroFish

```bash
./scripts/bootstrap_mirofish.sh
export MIROFISH_COMMAND="python3 scripts/mirofish_bridge_example.py"
```

O MiroFish upstream é externo, usa AGPL-3.0 e possui configuração própria.

## Estrutura

```text
src/.../engine.py             motor do gêmeo
src/.../council.py            conselho e validação cruzada
src/.../specialists.py        perfis, opiniões e pesos
src/.../model_fabric.py       adapters hermético e LiteRT-LM
src/.../opencode_bridge.py    operações seguras do OpenCode
src/.../reversa.py            auditoria adversarial do twin
.opencode/                    tools, comandos, agente e skill
scripts/                      bridges MiroFish e LiteRT-LM
schemas/                      contratos JSON
docs/                         SDD, segurança e reprodução
tests/                        TDD hermético
```

## Gates de segurança

Todos os resultados mantêm:

```json
{
  "simulation_only": true,
  "clinical_use_allowed": false,
  "prescription_allowed": false,
  "diagnostic_claim_allowed": false,
  "prognostic_claim_allowed": false,
  "procedure_selection_allowed": false,
  "real_patient_data_allowed": false,
  "human_review_required": true
}
```

Leia `docs/SAFETY.md`, `docs/REPRODUCIBILITY.md`, `docs/OPENCODE_CLI.md`, `docs/LITERT_LM_GEMMA4.md` e as SPECs.
