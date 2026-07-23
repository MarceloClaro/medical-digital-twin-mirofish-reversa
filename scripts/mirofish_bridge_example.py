"""Bridge demonstrativo. Não conecta ao MiroFish upstream; apenas documenta o contrato."""
import json
import sys

payload = json.load(sys.stdin)
json.dump(
    {
        "aggregate": float(payload.get("signal", 0.5)),
        "consensus": 0.5,
        "dispersion": 0.25,
        "n_agents": 0,
        "trace": {"mode": "contract-example-only", "seed": payload.get("seed")},
    },
    sys.stdout,
)
