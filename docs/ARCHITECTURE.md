# Arquitetura

```text
SimulationCase sintético
        │
        ▼
Validação de identidade e escopo
        │
        ▼
MedicalDigitalTwinEngine
   ├── cálculo determinístico de completude/sinal
   ├── SwarmAdapter
   │     ├── DeterministicSwarmAdapter (padrão/CI)
   │     └── MiroFishExternalAdapter (opt-in)
   ├── geração T0..Tn
   └── ReversaMedicalReviewer
        │
        ▼
DigitalTwinResult fail-closed + SHA-256
```

## Fronteiras

- O núcleo não contém dados ou algoritmos de diagnóstico clínico.
- Ações são cenários contrafactuais, não tratamentos.
- O adaptador MiroFish é externo e normalizado por contrato JSON.
- Reversa não recomenda conduta; apenas bloqueia, questiona e documenta fragilidades.
