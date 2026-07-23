"""Enxame hermético e reproduzível para desenvolvimento, testes e CI."""
from __future__ import annotations

import random
import statistics
from typing import Any


class DeterministicSwarmAdapter:
    name = "deterministic-local-swarm"

    def __init__(self, n_agents: int = 15, noise: float = 0.08) -> None:
        if n_agents < 3 or n_agents > 101:
            raise ValueError("n_agents deve estar entre 3 e 101")
        self.n_agents = n_agents
        self.noise = noise

    def simulate(self, *, question: str, signal: float, seed: int) -> dict[str, Any]:
        rng = random.Random(f"{seed}:{question}")
        biases = (-0.10, -0.05, 0.0, 0.05, 0.10)
        values = [
            max(0.0, min(1.0, signal + biases[i % len(biases)] + rng.gauss(0, self.noise)))
            for i in range(self.n_agents)
        ]
        aggregate = statistics.fmean(values)
        dispersion = statistics.pstdev(values)
        consensus = max(0.0, min(1.0, 1.0 - dispersion / 0.5))
        return {
            "adapter": self.name,
            "aggregate": round(aggregate, 6),
            "consensus": round(consensus, 6),
            "dispersion": round(dispersion, 6),
            "n_agents": self.n_agents,
            "trace": {"seed": seed, "question": question, "individual": [round(v, 6) for v in values]},
        }
