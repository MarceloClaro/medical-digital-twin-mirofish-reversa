"""Orquestração reproduzível do conselho multimodal de especialistas."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .engine import MedicalDigitalTwinEngine
from .model_fabric import DeterministicMultimodalAdapter, MultimodalModelAdapter
from .models import SimulationCase
from .specialists import (
    DEFAULT_SPECIALISTS,
    SpecialistOpinion,
    SpecialistProfile,
    nash_product_weights,
)

Clock = Callable[[], datetime]
_ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_IMAGES = 10
_MAX_IMAGE_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class MedicalCouncilResult:
    council_id: str
    created_at_utc: str
    contract_version: str
    case_id: str
    model_adapter: str
    opinions: list[SpecialistOpinion]
    cross_validation: dict[str, Any]
    game_theory: dict[str, Any]
    synthesis: dict[str, Any]
    digital_twin: dict[str, Any]
    safety_review: dict[str, Any]
    safety: dict[str, Any]
    reproducibility: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MedicalSpecialistCouncil:
    """Executa especialistas independentes e vincula o resultado ao twin."""

    CONTRACT_VERSION = "medical-specialist-council/1.0"

    def __init__(
        self,
        *,
        adapter: MultimodalModelAdapter | None = None,
        seed: int = 42,
        clock: Clock | None = None,
    ) -> None:
        self.adapter = adapter or DeterministicMultimodalAdapter()
        self.seed = seed
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run(
        self,
        case: SimulationCase,
        *,
        image_files: Iterable[Path] | None = None,
        selected_specialists: Iterable[str] | None = None,
        horizon_steps: int = 4,
    ) -> MedicalCouncilResult:
        case.validate()
        images = self._validate_images(list(image_files or []))
        profiles = self._select_profiles(selected_specialists)
        image_manifest = [self._image_manifest(path) for path in images]
        canonical = {
            "case": case.to_dict(),
            "images": image_manifest,
            "specialists": [profile.specialist_id for profile in profiles],
            "adapter": self.adapter.name,
            "seed": self.seed,
            "horizon_steps": horizon_steps,
            "contract_version": self.CONTRACT_VERSION,
        }
        canonical_json = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        source_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        council_id = "msc-" + uuid.uuid5(uuid.NAMESPACE_URL, source_hash).hex[:16]

        opinions: list[SpecialistOpinion] = []
        for index, profile in enumerate(profiles):
            payload = self.adapter.analyze(
                specialist=profile,
                case=case,
                image_files=images,
                seed=self.seed + index,
            )
            opinions.append(
                SpecialistOpinion.from_payload(
                    profile,
                    payload,
                    adapter_name=self.adapter.name,
                )
            )

        weights = nash_product_weights(profiles, opinions)
        cross_validation, synthesis = _cross_validate(opinions, weights)
        safety_review = _review_council(opinions, cross_validation, self.adapter.name)
        twin = MedicalDigitalTwinEngine(seed=self.seed, clock=self.clock).simulate(
            case,
            horizon_steps=horizon_steps,
            run_id=council_id,
        )
        return MedicalCouncilResult(
            council_id=council_id,
            created_at_utc=self.clock().astimezone(timezone.utc).isoformat(),
            contract_version=self.CONTRACT_VERSION,
            case_id=case.case_id,
            model_adapter=self.adapter.name,
            opinions=opinions,
            cross_validation=cross_validation,
            game_theory={
                "method": "nash-product-inspired",
                "interpretation": (
                    "pesos de síntese por utilidade geométrica; não representam verdade clínica"
                ),
                "weights": weights,
            },
            synthesis=synthesis,
            digital_twin=twin.to_dict(),
            safety_review=safety_review,
            safety={
                "simulation_only": True,
                "clinical_use_allowed": False,
                "diagnostic_claim_allowed": False,
                "prognostic_claim_allowed": False,
                "prescription_allowed": False,
                "treatment_recommendation_allowed": False,
                "procedure_selection_allowed": False,
                "real_patient_data_allowed": False,
                "human_review_required": True,
                "warning": (
                    "Conselho educacional para caso sintético. "
                    "Não usar para decisão sobre pessoa real."
                ),
            },
            reproducibility={
                "canonical_sha256": source_hash,
                "seed": self.seed,
                "horizon_steps": horizon_steps,
                "adapter": self.adapter.name,
                "image_manifest": image_manifest,
                "specialists": [profile.specialist_id for profile in profiles],
            },
        )

    @staticmethod
    def _select_profiles(selected: Iterable[str] | None) -> list[SpecialistProfile]:
        identifiers = list(selected) if selected is not None else list(DEFAULT_SPECIALISTS)
        if not identifiers:
            raise ValueError("ao menos um especialista é obrigatório")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("especialistas duplicados não são permitidos")
        unknown = sorted(set(identifiers).difference(DEFAULT_SPECIALISTS))
        if unknown:
            raise ValueError(f"especialistas desconhecidos: {unknown}")
        return [DEFAULT_SPECIALISTS[identifier] for identifier in identifiers]

    @staticmethod
    def _validate_images(images: list[Path]) -> list[Path]:
        if len(images) > _MAX_IMAGES:
            raise ValueError(f"no máximo {_MAX_IMAGES} imagens são permitidas")
        validated: list[Path] = []
        for path in images:
            resolved = path.resolve()
            if resolved.suffix.lower() not in _ALLOWED_IMAGE_SUFFIXES:
                raise ValueError("somente imagens PNG, JPEG ou WEBP são permitidas")
            if not resolved.is_file():
                raise ValueError(f"imagem não encontrada: {resolved}")
            if resolved.stat().st_size > _MAX_IMAGE_BYTES:
                raise ValueError("imagem excede o limite de 20 MiB")
            validated.append(resolved)
        return validated

    @staticmethod
    def _image_manifest(path: Path) -> dict[str, Any]:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "filename": path.name,
            "sha256": digest,
            "size_bytes": path.stat().st_size,
            "suffix": path.suffix.lower(),
        }


def _cross_validate(
    opinions: list[SpecialistOpinion],
    weights: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    stance_maps: dict[str, dict[str, str]] = {}
    for opinion in opinions:
        stance_maps[opinion.specialist_id] = {}
        for claim in opinion.claims:
            claim_id = str(claim["claim_id"])
            stance = str(claim["stance"])
            confidence = float(claim["confidence"])
            stance_maps[opinion.specialist_id][claim_id] = stance
            record = claims.setdefault(
                claim_id,
                {
                    "claim_id": claim_id,
                    "label": str(claim["label"]),
                    "positions": [],
                    "support_weight": 0.0,
                    "oppose_weight": 0.0,
                    "uncertain_weight": 0.0,
                },
            )
            contribution = weights[opinion.specialist_id] * confidence
            record[f"{stance}_weight"] += contribution
            record["positions"].append(
                {
                    "specialist_id": opinion.specialist_id,
                    "stance": stance,
                    "confidence": confidence,
                }
            )

    supported: list[dict[str, Any]] = []
    contested: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    uncertain: list[dict[str, Any]] = []
    for record in claims.values():
        has_support = record["support_weight"] > 0.0
        has_oppose = record["oppose_weight"] > 0.0
        compact = {
            "claim_id": record["claim_id"],
            "label": record["label"],
            "support_weight": round(record["support_weight"], 6),
            "oppose_weight": round(record["oppose_weight"], 6),
            "uncertain_weight": round(record["uncertain_weight"], 6),
            "positions": record["positions"],
        }
        if has_support and has_oppose:
            contested.append(compact)
        elif has_support:
            supported.append(compact)
        elif has_oppose:
            rejected.append(compact)
        else:
            uncertain.append(compact)

    pairwise: list[dict[str, Any]] = []
    identifiers = [opinion.specialist_id for opinion in opinions]
    for left_index, left_id in enumerate(identifiers):
        for right_id in identifiers[left_index + 1 :]:
            left = stance_maps[left_id]
            right = stance_maps[right_id]
            shared = sorted(set(left).intersection(right))
            agreement = (
                sum(left[claim_id] == right[claim_id] for claim_id in shared) / len(shared)
                if shared
                else None
            )
            pairwise.append(
                {
                    "left": left_id,
                    "right": right_id,
                    "shared_claims": shared,
                    "agreement": agreement,
                }
            )

    cross_validation = {
        "method": "independent-claims-cross-validation/1.0",
        "claim_count": len(claims),
        "pairwise_agreement": pairwise,
        "conflicts": contested,
        "dissent_preserved": True,
    }
    synthesis = {
        "supported_claims": supported,
        "contested_claims": contested,
        "rejected_claims": rejected,
        "uncertain_claims": uncertain,
        "must_not_miss": sorted(
            {item for opinion in opinions for item in opinion.must_not_miss}
        ),
        "missing_information": sorted(
            {item for opinion in opinions for item in opinion.missing_information}
        ),
        "intervention_questions": sorted(
            {item for opinion in opinions for item in opinion.intervention_questions}
        ),
        "limitations": sorted({item for opinion in opinions for item in opinion.limitations}),
    }
    return cross_validation, synthesis


def _review_council(
    opinions: list[SpecialistOpinion],
    cross_validation: dict[str, Any],
    adapter_name: str,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for opinion in opinions:
        if opinion.confidence > 0.90 and opinion.evidence_strength < 0.30:
            findings.append(
                {
                    "severity": "high",
                    "code": "COUNCIL-CAL-001",
                    "message": (
                        f"{opinion.specialist_id}: confiança alta com evidência estrutural baixa"
                    ),
                }
            )
    if cross_validation.get("conflicts"):
        findings.append(
            {
                "severity": "medium",
                "code": "COUNCIL-DISSENT-001",
                "message": "Há claims contestados; o dissenso deve permanecer visível.",
            }
        )
    if adapter_name == "deterministic-multimodal-scaffold":
        findings.append(
            {
                "severity": "info",
                "code": "COUNCIL-VISION-001",
                "message": "O adapter hermético não interpreta pixels de imagens.",
            }
        )
    if len({opinion.model_adapter for opinion in opinions}) == 1:
        findings.append(
            {
                "severity": "medium",
                "code": "COUNCIL-INDEP-001",
                "message": (
                    "Especialistas compartilham o mesmo adapter/modelo; "
                    "independência epistêmica é limitada."
                ),
            }
        )
    blocked = any(item["severity"] == "high" for item in findings)
    return {
        "reviewer": "reversa-council-adversarial/1.0",
        "decision": "block_clinical_use" if blocked else "simulation_only",
        "findings": findings,
        "counterfactual_questions": [
            "Qual variável omitida poderia inverter a síntese?",
            "O mesmo resultado aparece com outro modelo ou fonte independente?",
            "A concordância decorre do mesmo modelo-base?",
            "Qual hipótese nula explica os mesmos dados?",
        ],
    }
