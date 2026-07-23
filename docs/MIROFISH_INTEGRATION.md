# Integração externa com MiroFish

O projeto upstream `666ghj/MiroFish` é uma aplicação multiagente completa, com frontend,
backend e dependências de LLM/Zep. Ele não é incorporado nem modificado aqui.

A integração usa um comando controlado pelo operador:

```bash
medical-twin examples/synthetic_case.json \
  --mirofish-command "python3 scripts/mirofish_bridge_example.py"
```

## Entrada JSON em stdin

```json
{"question":"...", "signal":0.5, "seed":42, "domain":"medical_simulation"}
```

## Saída JSON obrigatória

```json
{
  "aggregate": 0.61,
  "consensus": 0.82,
  "dispersion": 0.09,
  "n_agents": 25,
  "trace": {"simulation_id":"..."}
}
```

O bridge específico deve ser implementado contra a versão instalada do MiroFish, sem
presumir rotas internas não documentadas. O operador é responsável pela conformidade
com a licença AGPL-3.0 do MiroFish e com as licenças de modelos/serviços utilizados.
