"""Contrato estável para motores de enxame."""
from __future__ import annotations

from typing import Any, Protocol


class SwarmAdapter(Protocol):
    name: str

    def simulate(self, *, question: str, signal: float, seed: int) -> dict[str, Any]:
        """Retorna aggregate, consensus, dispersion, n_agents e trace."""
        ...
