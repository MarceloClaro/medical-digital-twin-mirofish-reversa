# Publicação em um repositório GitHub separado

Nome recomendado:

`opencode_medical-digital-twin-mirofish-reversa`

## Com GitHub CLI

```bash
git init
git add .
git commit -m "feat(core): iniciar gêmeo digital médico simulado"
gh repo create MarceloClaro/opencode_medical-digital-twin-mirofish-reversa \
  --public --source=. --remote=origin --push
```

## Sem GitHub CLI

1. Crie um repositório vazio no GitHub com o nome indicado.
2. Execute:

```bash
git remote add origin https://github.com/MarceloClaro/opencode_medical-digital-twin-mirofish-reversa.git
git branch -M main
git push -u origin main
```

Não marque a versão como produção clínica. Use `v0.1.0-alpha` enquanto não houver
validação externa, governança regulatória e avaliação independente.
