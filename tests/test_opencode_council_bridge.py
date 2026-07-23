import json
from pathlib import Path

import pytest

from opencode_medical_digital_twin_mirofish_reversa.opencode_bridge import (
    OpenCodeBridgeError,
    execute_opencode_request,
)


def write_case(root: Path) -> None:
    (root / "cases").mkdir()
    (root / "cases" / "case.json").write_text(
        json.dumps({
            "case_id": "bridge-council-001",
            "request": "Caso fictício para conselho",
            "synthetic": True,
            "profile": {"age_group": "adulto", "sex_at_birth": "F"},
            "clinical_data": {
                "history": ["histórico simulado"],
                "vital_signs": {"temperature_c": 37.8},
                "lab_results": [],
            },
            "hypotheses": [],
            "scenario_actions": ["observação sintética"],
        }),
        encoding="utf-8",
    )


def test_opencode_bridge_runs_hermetic_council(tmp_path: Path):
    write_case(tmp_path)
    result = execute_opencode_request({
        "operation": "council",
        "case_file": "cases/case.json",
        "adapter": "deterministic",
        "specialists": ["internal_medicine", "radiology", "methodology"],
        "horizon": 3,
        "seed": 11,
    }, worktree=tmp_path)
    artifact = tmp_path / result["artifact_path"]
    assert artifact.is_file()
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["council_id"] == result["council_id"]
    assert data["digital_twin"]["simulation_only"] is True
    assert result["specialist_count"] == 3


def test_opencode_bridge_blocks_litert_without_operator_configuration(
    tmp_path: Path, monkeypatch
):
    write_case(tmp_path)
    monkeypatch.delenv("LITERT_LM_COMMAND", raising=False)
    with pytest.raises(OpenCodeBridgeError, match="LITERT_LM_COMMAND"):
        execute_opencode_request({
            "operation": "council",
            "case_file": "cases/case.json",
            "adapter": "litert_lm",
        }, worktree=tmp_path)


def test_opencode_bridge_rejects_image_path_escape(tmp_path: Path):
    write_case(tmp_path)
    with pytest.raises(OpenCodeBridgeError, match="worktree"):
        execute_opencode_request({
            "operation": "council",
            "case_file": "cases/case.json",
            "image_files": ["../outside.png"],
        }, worktree=tmp_path)
