import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from opencode_medical_digital_twin_mirofish_reversa import SimulationCase
from opencode_medical_digital_twin_mirofish_reversa.council import MedicalSpecialistCouncil
from opencode_medical_digital_twin_mirofish_reversa.model_fabric import (
    DeterministicMultimodalAdapter,
    LiteRTLMExternalAdapter,
)
from opencode_medical_digital_twin_mirofish_reversa.specialists import (
    DEFAULT_SPECIALISTS,
    SpecialistOpinion,
    nash_product_weights,
)

FIXED = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def synthetic_case() -> SimulationCase:
    return SimulationCase(
        case_id="council-synthetic-001",
        request="Caso educacional fictício com febre e tosse",
        synthetic=True,
        profile={"age_group": "adulto", "sex_at_birth": "F"},
        clinical_data={
            "history": ["asma simulada"],
            "vital_signs": {"temperature_c": 38.1},
            "lab_results": [{"name": "CRP", "value": 8.0}],
        },
        hypotheses=[{"name": "síndrome respiratória simulada", "status": "possible"}],
        scenario_actions=["observação sintética", "coleta simulada de dados"],
    )


def test_deterministic_council_is_reproducible_and_links_twin(tmp_path: Path):
    image = tmp_path / "synthetic.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
    council = MedicalSpecialistCouncil(
        adapter=DeterministicMultimodalAdapter(),
        seed=42,
        clock=lambda: FIXED,
    )
    first = council.run(synthetic_case(), image_files=[image], horizon_steps=3).to_dict()
    second = council.run(synthetic_case(), image_files=[image], horizon_steps=3).to_dict()
    assert first["council_id"] == second["council_id"]
    assert first["opinions"] == second["opinions"]
    assert first["digital_twin"]["simulation_only"] is True
    assert first["safety"]["diagnostic_claim_allowed"] is False
    assert abs(sum(first["game_theory"]["weights"].values()) - 1.0) < 1e-9


def test_game_theory_weight_rewards_stronger_evidence():
    profiles = [DEFAULT_SPECIALISTS["internal_medicine"], DEFAULT_SPECIALISTS["methodology"]]
    opinions = [
        SpecialistOpinion.minimal("internal_medicine", evidence_strength=0.9, confidence=0.8),
        SpecialistOpinion.minimal("methodology", evidence_strength=0.2, confidence=0.8),
    ]
    weights = nash_product_weights(profiles, opinions)
    assert weights["internal_medicine"] > weights["methodology"]
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_cross_validation_preserves_conflict():
    class ConflictingAdapter(DeterministicMultimodalAdapter):
        def analyze(self, *, specialist, case, image_files, seed):
            payload = super().analyze(
                specialist=specialist, case=case, image_files=image_files, seed=seed
            )
            if specialist.specialist_id == "internal_medicine":
                payload["claims"] = [{
                    "claim_id": "claim-x",
                    "label": "Hipótese X",
                    "stance": "support",
                    "confidence": 0.8,
                }]
            if specialist.specialist_id == "methodology":
                payload["claims"] = [{
                    "claim_id": "claim-x",
                    "label": "Hipótese X",
                    "stance": "oppose",
                    "confidence": 0.8,
                }]
            return payload

    result = MedicalSpecialistCouncil(adapter=ConflictingAdapter(), seed=7).run(
        synthetic_case(),
        selected_specialists=["internal_medicine", "methodology"],
    )
    contested = result.to_dict()["synthesis"]["contested_claims"]
    assert any(item["claim_id"] == "claim-x" for item in contested)


def test_image_validation_rejects_unsupported_extension(tmp_path: Path):
    bad = tmp_path / "scan.dcm"
    bad.write_bytes(b"synthetic")
    with pytest.raises(ValueError, match="PNG, JPEG ou WEBP"):
        MedicalSpecialistCouncil().run(synthetic_case(), image_files=[bad])


def test_litert_adapter_rejects_invalid_output(tmp_path: Path):
    script = tmp_path / "fake.py"
    script.write_text("print('not-json')", encoding="utf-8")
    adapter = LiteRTLMExternalAdapter(f"python3 {script}")
    with pytest.raises(RuntimeError, match="JSON"):
        adapter.analyze(
            specialist=DEFAULT_SPECIALISTS["radiology"],
            case=synthetic_case(),
            image_files=[],
            seed=42,
        )
