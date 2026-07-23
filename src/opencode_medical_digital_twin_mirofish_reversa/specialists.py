"""Contratos e ponderação do conselho de especialistas sintéticos."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class SpecialistProfile:
    """Perfil versionável de um especialista virtual."""

    specialist_id: str
    domain: str
    relevance: float
    calibration: float
    independence_group: str
    image_capable: bool = False
    purpose: str = "análise educacional de caso sintético"


@dataclass(frozen=True)
class SpecialistOpinion:
    """Opinião estruturada; nunca representa diagnóstico ou prescrição."""

    specialist_id: str
    observations: list[str] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    must_not_miss: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    intervention_questions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence_strength: float = 0.0
    model_adapter: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def minimal(
        cls,
        specialist_id: str,
        *,
        evidence_strength: float,
        confidence: float,
    ) -> "SpecialistOpinion":
        return cls(
            specialist_id=specialist_id,
            observations=["opinião sintética mínima"],
            claims=[],
            limitations=["sem validação clínica externa"],
            confidence=_bounded(confidence),
            evidence_strength=_bounded(evidence_strength),
            model_adapter="test",
        )

    @classmethod
    def from_payload(
        cls,
        profile: SpecialistProfile,
        payload: dict[str, Any],
        *,
        adapter_name: str,
    ) -> "SpecialistOpinion":
        claims = _normalize_claims(payload.get("claims", []))
        return cls(
            specialist_id=profile.specialist_id,
            observations=_string_list(payload.get("observations", [])),
            claims=claims,
            must_not_miss=_string_list(payload.get("must_not_miss", [])),
            missing_information=_string_list(payload.get("missing_information", [])),
            intervention_questions=_string_list(payload.get("intervention_questions", [])),
            limitations=_string_list(payload.get("limitations", [])),
            confidence=_bounded(_as_float(payload.get("confidence", 0.0))),
            evidence_strength=_bounded(_as_float(payload.get("evidence_strength", 0.0))),
            model_adapter=adapter_name,
        )


DEFAULT_SPECIALISTS: dict[str, SpecialistProfile] = {
    "internal_medicine": SpecialistProfile(
        specialist_id="internal_medicine",
        domain="clinical_integration",
        relevance=0.95,
        calibration=0.78,
        independence_group="clinical-general",
        purpose="integração de história, sinais e hipóteses sintéticas",
    ),
    "radiology": SpecialistProfile(
        specialist_id="radiology",
        domain="medical_imaging",
        relevance=0.90,
        calibration=0.76,
        independence_group="imaging",
        image_capable=True,
        purpose="descrição visual não diagnóstica e controle de qualidade",
    ),
    "pharmacology": SpecialistProfile(
        specialist_id="pharmacology",
        domain="pharmacology",
        relevance=0.78,
        calibration=0.75,
        independence_group="therapeutics",
        purpose="questões de mecanismo, interação e segurança farmacológica",
    ),
    "procedures": SpecialistProfile(
        specialist_id="procedures",
        domain="procedural_reasoning",
        relevance=0.76,
        calibration=0.73,
        independence_group="procedures",
        purpose="questões de indicação, contraindicação e pré-requisitos",
    ),
    "nutrition": SpecialistProfile(
        specialist_id="nutrition",
        domain="nutrition",
        relevance=0.64,
        calibration=0.70,
        independence_group="lifestyle",
        purpose="questões nutricionais educacionais e riscos de restrição",
    ),
    "exercise": SpecialistProfile(
        specialist_id="exercise",
        domain="exercise_physiology",
        relevance=0.62,
        calibration=0.70,
        independence_group="lifestyle",
        purpose="questões funcionais, progressão e sinais de interrupção",
    ),
    "methodology": SpecialistProfile(
        specialist_id="methodology",
        domain="clinical_methodology",
        relevance=0.72,
        calibration=0.88,
        independence_group="methodology",
        purpose="auditoria de validade, causalidade, vieses e extrapolação",
    ),
}


def nash_product_weights(
    profiles: Iterable[SpecialistProfile],
    opinions: Iterable[SpecialistOpinion],
) -> dict[str, float]:
    """Calcula pesos pela média geométrica de utilidades independentes.

    O nome é deliberadamente ``nash-product-inspired``: não representa um
    equilíbrio clínico nem prova de verdade. A média geométrica impede que uma
    dimensão muito fraca seja escondida por outra muito alta.
    """

    profile_list = list(profiles)
    opinion_by_id = {item.specialist_id: item for item in opinions}
    group_counts: dict[str, int] = {}
    for profile in profile_list:
        group_counts[profile.independence_group] = (
            group_counts.get(profile.independence_group, 0) + 1
        )

    raw: dict[str, float] = {}
    for profile in profile_list:
        opinion = opinion_by_id[profile.specialist_id]
        completeness = _opinion_completeness(opinion)
        independence = 1.0 / group_counts[profile.independence_group]
        components = (
            _positive(profile.calibration),
            _positive(profile.relevance),
            _positive(opinion.evidence_strength),
            _positive(opinion.confidence),
            _positive(completeness),
            _positive(independence),
        )
        raw[profile.specialist_id] = math.exp(
            sum(math.log(value) for value in components) / len(components)
        )

    total = sum(raw.values())
    if total <= 0.0:
        equal = 1.0 / max(len(raw), 1)
        return {key: equal for key in raw}
    normalized = {key: value / total for key, value in raw.items()}
    correction = 1.0 - sum(normalized.values())
    if normalized:
        first = next(iter(normalized))
        normalized[first] += correction
    return normalized


def _opinion_completeness(opinion: SpecialistOpinion) -> float:
    sections = (
        opinion.observations,
        opinion.limitations,
        opinion.missing_information,
        opinion.intervention_questions,
    )
    present = sum(bool(section) for section in sections)
    return max(0.2, present / len(sections))


def _normalize_claims(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("claims deve ser uma lista")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("cada claim deve ser um objeto")
        claim_id = str(item.get("claim_id", "")).strip()
        label = str(item.get("label", "")).strip()
        stance = str(item.get("stance", "uncertain")).strip().lower()
        if not claim_id or not label:
            raise ValueError("claim_id e label são obrigatórios")
        if stance not in {"support", "oppose", "uncertain"}:
            raise ValueError("stance deve ser support, oppose ou uncertain")
        normalized.append(
            {
                "claim_id": claim_id,
                "label": label,
                "stance": stance,
                "confidence": _bounded(_as_float(item.get("confidence", 0.0))),
            }
        )
    return normalized


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("campo estruturado deve ser uma lista")
    return [str(item).strip() for item in value if str(item).strip()]


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("valor numérico inválido") from exc


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _positive(value: float) -> float:
    return max(1e-6, _bounded(value))
