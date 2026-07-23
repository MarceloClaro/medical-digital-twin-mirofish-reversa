from datetime import datetime, timezone

import pytest

from opencode_medical_digital_twin_mirofish_reversa import MedicalDigitalTwinEngine, SimulationCase

FIXED = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def case(**overrides):
    data = {
        "case_id": "synthetic-001",
        "request": "Caso fictício com febre e tosse há dois dias",
        "synthetic": True,
        "profile": {"age_group": "adulto", "sex_at_birth": "F"},
        "clinical_data": {
            "history": ["asma simulada"],
            "vital_signs": {"temperature_c": 38.1},
            "lab_results": [{"name": "CRP", "value": 8.0}],
        },
        "hypotheses": [{"name": "infecção respiratória", "status": "possible"}],
        "scenario_actions": ["observação sintética", "coleta simulada de dados"],
    }
    data.update(overrides)
    return SimulationCase(**data)


def engine(seed=42):
    return MedicalDigitalTwinEngine(seed=seed, clock=lambda: FIXED)


def test_result_is_simulation_only_and_fail_closed():
    result = engine().simulate(case())
    assert result.simulation_only is True
    assert result.safety["clinical_use_allowed"] is False
    assert result.safety["prescription_allowed"] is False
    assert result.safety["human_review_required"] is True


def test_same_input_and_seed_produce_same_hash_id_and_trajectories():
    first = engine().simulate(case()).to_dict()
    second = engine().simulate(case()).to_dict()
    assert first["source_hash"] == second["source_hash"]
    assert first["twin_id"] == second["twin_id"]
    assert first["trajectories"] == second["trajectories"]


def test_different_seed_changes_reproducibility_and_trajectory():
    first = engine(seed=1).simulate(case()).to_dict()
    second = engine(seed=2).simulate(case()).to_dict()
    assert first["source_hash"] != second["source_hash"]
    assert first["trajectories"] != second["trajectories"]


def test_rejects_real_or_identifiable_patient_data():
    with pytest.raises(ValueError, match="Somente casos sintéticos"):
        engine().simulate(case(synthetic=False))
    with pytest.raises(ValueError, match="Identificadores pessoais"):
        engine().simulate(case(profile={"name": "Pessoa Real"}))


def test_horizon_is_bounded():
    with pytest.raises(ValueError):
        engine().simulate(case(), horizon_steps=1)
    with pytest.raises(ValueError):
        engine().simulate(case(), horizon_steps=13)


def test_reversa_blocks_low_completeness():
    sparse = case(profile={}, clinical_data={})
    result = engine().simulate(sparse)
    assert result.reversa_review["decision"] == "block_clinical_use"
    assert any(item["code"] == "REV-DATA-001" for item in result.reversa_review["findings"])


def test_reversa_blocks_prescriptive_scenario_language():
    unsafe = case(scenario_actions=["prescrever dose de medicamento"])
    result = engine().simulate(unsafe)
    assert any(item["code"] == "REV-RX-001" for item in result.reversa_review["findings"])
