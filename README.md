# opencode_medical-digital-twin-mirofish-reversa

Projeto standalone para criar **gêmeos digitais de casos médicos inteiramente sintéticos**,
com simulação de enxame MiroFish opcional e auditoria adversarial Reversa.

> **Não é dispositivo médico, não diagnostica, não prescreve e não aceita dados reais de pacientes.**

## Estado

Alpha experimental. O modo padrão é hermético, local e reproduzível.

## Recursos

- casos exclusivamente sintéticos;
- rejeição de campos identificáveis;
- trajetórias T0..Tn com incerteza explícita;
- adapter de enxame local determinístico;
- adapter externo para MiroFish por JSON stdin/stdout;
- revisão Reversa para completude, excesso de confiança e linguagem prescritiva;
- hash SHA-256 e `twin_id` estável;
- zero dependências obrigatórias em runtime;
- testes e CI para Python 3.11/3.12.

## Instalação

```bash
git clone https://github.com/MarceloClaro/medical-digital-twin-mirofish-reversa.git
cd opencode_medical-digital-twin-mirofish-reversa
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## Simulação hermética

```bash
medical-twin examples/synthetic_case.json --seed 42 --horizon 4 --output result.json
```

## Integração MiroFish

O upstream pode ser clonado separadamente:

```bash
./scripts/bootstrap_mirofish.sh
```

A integração real deve expor o contrato descrito em `docs/MIROFISH_INTEGRATION.md`.
O repositório MiroFish upstream usa AGPL-3.0 e requer configuração própria de LLM/Zep.

## Estrutura

```text
src/.../engine.py            motor do gêmeo
src/.../models.py            contratos imutáveis
src/.../adapters/            enxame hermético e bridge externo
src/.../reversa.py           auditor adversarial
tests/                       testes herméticos
schemas/                     contratos JSON
docs/                        arquitetura, segurança e SPEC
examples/                    apenas fixtures sintéticas
```

## Gates de segurança

Todos os resultados fixam:

```json
{
  "clinical_use_allowed": false,
  "prescription_allowed": false,
  "diagnostic_claim_allowed": false,
  "prognostic_claim_allowed": false,
  "real_patient_data_allowed": false,
  "human_review_required": true
}
```

Leia `docs/SAFETY.md`, `docs/REPRODUCIBILITY.md` e `THIRD_PARTY_NOTICES.md`.
