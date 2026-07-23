import json
from pathlib import Path

import pytest

from opencode_medical_digital_twin_mirofish_reversa.opencode_bridge import (
    OpenCodeBridgeError,
    execute_opencode_request,
)


def write_case(root: Path) -> Path:
    path = root / "cases" / "synthetic.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({
            "case_id": "opencode-synthetic-001",
            "request": "Caso educacional inteiramente fictício",
            "synthetic": True,
            "profile": {"age_group": "adulto", "sex_at_birth": "F"},
            "clinical_data": {
                "history": ["histórico simulado"],
                "vital_signs": {"temperature_c": 37.8},
                "lab_results": [{"name": "CRP", "value": 4.0}],
            },
            "hypotheses": [{"name": "hipótese educacional", "status": "possible"}],
            "scenario_actions": ["observação sintética"],
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_bridge_validates_without_simulating(tmp_path: Path):
    write_case(tmp_path)
    result = execute_opencode_request(
        {"operation": "validate", "case_file": "cases/synthetic.json"}, worktree=tmp_path
    )
    assert result["ok"] is True
    assert result["operation"] == "validate"
    assert "artifact_path" not in result


def test_bridge_simulates_and_writes_auditable_artifact(tmp_path: Path):
    write_case(tmp_path)
    result = execute_opencode_request(
        {
            "operation": "simulate",
            "case_file": "cases/synthetic.json",
            "horizon": 3,
            "seed": 7,
            "adapter": "deterministic",
        },
        worktree=tmp_path,
    )
    artifact = tmp_path / result["artifact_path"]
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["twin_id"] == result["twin_id"]
    assert payload["safety"]["clinical_use_allowed"] is False
    assert result["trajectory_count"] == 3


def test_bridge_rejects_paths_outside_worktree(tmp_path: Path):
    with pytest.raises(OpenCodeBridgeError, match="worktree"):
        execute_opencode_request(
            {"operation": "validate", "case_file": "../outside.json"}, worktree=tmp_path
        )


def test_bridge_blocks_mirofish_without_operator_configuration(tmp_path: Path, monkeypatch):
    write_case(tmp_path)
    monkeypatch.delenv("MIROFISH_COMMAND", raising=False)
    with pytest.raises(OpenCodeBridgeError, match="MIROFISH_COMMAND"):
        execute_opencode_request(
            {
                "operation": "simulate",
                "case_file": "cases/synthetic.json",
                "adapter": "mirofish",
            },
            worktree=tmp_path,
        )
