# Reprodutibilidade

Uma execução é definida por:

- JSON canônico do caso sintético;
- versão do contrato;
- seed;
- horizonte;
- versão/identidade do adaptador;
- ambiente Python.

O `source_hash` é SHA-256 do payload canônico. Com o adaptador hermético, o mesmo
payload e seed produzem o mesmo `twin_id` e as mesmas trajetórias.

## Execução reproduzível

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
medical-twin examples/synthetic_case.json --seed 42 --horizon 4 --output result.json
sha256sum result.json
```

O timestamp não participa do hash canônico. Para testes, injete um relógio fixo.
