"""Contratos de dados imutáveis do gêmeo digital médico simulado."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

GLOBAL_FORBIDDEN_IDENTIFIERS = {
    "cpf", "cns", "email", "phone", "telefone", "address", "endereco",
    "birth_date", "data_nascimento", "medical_record_number",
}
PROFILE_NAME_IDENTIFIERS = {"name", "full_name", "nome"}


@dataclass(frozen=True)
class SimulationCase:
    """Caso obrigatoriamente fictício e não identificável."""

    case_id: str
    request: str
    synthetic: bool = True
    profile: dict[str, Any] = field(default_factory=dict)
    clinical_data: dict[str, Any] = field(default_factory=dict)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    scenario_actions: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if not self.synthetic:
            raise ValueError("Somente casos sintéticos são permitidos")
        if not self.case_id.strip() or not self.request.strip():
            raise ValueError("case_id e request são obrigatórios")
        found = _find_forbidden_keys(self.profile, in_profile=True)
        found.update(_find_forbidden_keys(self.clinical_data, in_profile=False))
        if found:
            raise ValueError(f"Identificadores pessoais proibidos no caso simulado: {sorted(found)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TwinState:
    step: int
    label: str
    state_vector: dict[str, float]
    scenario_action: str
    outcome_index: float
    uncertainty: float
    assumptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DigitalTwinResult:
    twin_id: str
    run_id: str
    created_at_utc: str
    simulation_only: bool
    source_hash: str
    contract_version: str
    trajectories: list[TwinState]
    swarm: dict[str, Any]
    reversa_review: dict[str, Any]
    safety: dict[str, Any]
    reproducibility: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _find_forbidden_keys(value: Any, *, in_profile: bool) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in GLOBAL_FORBIDDEN_IDENTIFIERS:
                found.add(normalized)
            if in_profile and normalized in PROFILE_NAME_IDENTIFIERS:
                found.add(normalized)
            found.update(_find_forbidden_keys(nested, in_profile=in_profile))
    elif isinstance(value, list):
        for nested in value:
            found.update(_find_forbidden_keys(nested, in_profile=in_profile))
    return found
