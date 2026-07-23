"""Adaptador externo neutro para uma implantação MiroFish controlada pelo operador.

Não presume rotas HTTP do projeto upstream. O operador fornece um comando que recebe
JSON em stdin e devolve JSON em stdout segundo o contrato documentado em
``docs/MIROFISH_INTEGRATION.md``.
"""
from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any


class MiroFishExternalAdapter:
    name = "mirofish-external-command"

    def __init__(self, command: str, timeout_seconds: float = 120.0) -> None:
        if not command.strip():
            raise ValueError("command não pode ser vazio")
        self.command = command
        self.timeout_seconds = timeout_seconds

    def simulate(self, *, question: str, signal: float, seed: int) -> dict[str, Any]:
        payload = {"question": question, "signal": signal, "seed": seed, "domain": "medical_simulation"}
        completed = subprocess.run(
            shlex.split(self.command),
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"MiroFish externo falhou ({completed.returncode}): {completed.stderr[-500:]}")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("MiroFish externo não retornou JSON válido") from exc
        for key in ("aggregate", "consensus", "n_agents"):
            if key not in result:
                raise RuntimeError(f"Resposta MiroFish sem campo obrigatório: {key}")
        return {
            "adapter": self.name,
            "aggregate": float(result["aggregate"]),
            "consensus": float(result["consensus"]),
            "dispersion": float(result.get("dispersion", 1.0 - float(result["consensus"]))),
            "n_agents": int(result["n_agents"]),
            "trace": result.get("trace", {}),
        }
