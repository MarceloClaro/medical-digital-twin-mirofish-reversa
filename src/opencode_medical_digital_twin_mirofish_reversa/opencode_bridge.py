"""Bridge seguro entre OpenCode e os motores de simulação sintética."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .adapters import MiroFishExternalAdapter, SwarmAdapter
from .council import MedicalSpecialistCouncil
from .engine import MedicalDigitalTwinEngine
from .model_fabric import LiteRTLMExternalAdapter, MultimodalModelAdapter
from .models import SimulationCase


class OpenCodeBridgeError(RuntimeError):
    """Erro de contrato ou segurança apresentado ao OpenCode."""


def execute_opencode_request(payload: dict[str, Any], *, worktree: Path) -> dict[str, Any]:
    root = worktree.resolve()
    operation = str(payload.get("operation", "simulate")).strip().lower()
    if operation not in {"validate", "simulate", "council"}:
        raise OpenCodeBridgeError("operation deve ser 'validate', 'simulate' ou 'council'")

    case_path = _resolve_inside(root, str(payload.get("case_file", "")), field="case_file")
    if not case_path.is_file():
        raise OpenCodeBridgeError(f"Arquivo não encontrado: {case_path.relative_to(root)}")

    try:
        raw_case = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OpenCodeBridgeError(f"JSON inválido: {exc}") from exc
    if not isinstance(raw_case, dict):
        raise OpenCodeBridgeError("O arquivo deve conter um objeto JSON")

    try:
        case = SimulationCase(**raw_case)
        case.validate()
    except (TypeError, ValueError) as exc:
        raise OpenCodeBridgeError(str(exc)) from exc

    if operation == "validate":
        return {
            "ok": True,
            "operation": "validate",
            "case_id": case.case_id,
            "synthetic": case.synthetic,
            "case_file": str(case_path.relative_to(root)),
        }
    if operation == "council":
        return _council(payload, root=root, case=case)
    return _simulate(payload, root=root, case=case)


def _simulate(payload: dict[str, Any], *, root: Path, case: SimulationCase) -> dict[str, Any]:
    seed, horizon = _seed_and_horizon(payload)
    adapter_name = str(payload.get("adapter", "deterministic")).strip().lower()
    adapter: SwarmAdapter | None
    if adapter_name == "deterministic":
        adapter = None
    elif adapter_name == "mirofish":
        command = os.environ.get("MIROFISH_COMMAND", "").strip()
        if not command:
            raise OpenCodeBridgeError("MIROFISH_COMMAND não está configurado pelo operador")
        adapter = MiroFishExternalAdapter(command)
    else:
        raise OpenCodeBridgeError("adapter deve ser 'deterministic' ou 'mirofish'")

    try:
        result = MedicalDigitalTwinEngine(swarm=adapter, seed=seed).simulate(
            case, horizon_steps=horizon
        )
    except (ValueError, RuntimeError) as exc:
        raise OpenCodeBridgeError(str(exc)) from exc

    data = result.to_dict()
    output_value = payload.get("output_file")
    artifact = (
        _resolve_inside(root, str(output_value), field="output_file")
        if output_value
        else root / ".opencode" / "artifacts" / "medical-twin" / f"{result.twin_id}.json"
    )
    _write_artifact(artifact, data)
    states = data.get("trajectories", [])
    return {
        "ok": True,
        "operation": "simulate",
        "adapter": adapter_name,
        "case_id": case.case_id,
        "twin_id": result.twin_id,
        "source_hash": result.source_hash,
        "artifact_path": str(artifact.relative_to(root)),
        "trajectory_count": len(states),
        "reversa_decision": result.reversa_review.get("decision"),
        "reversa_findings": result.reversa_review.get("findings", []),
        "safety": result.safety,
    }


def _council(payload: dict[str, Any], *, root: Path, case: SimulationCase) -> dict[str, Any]:
    seed, horizon = _seed_and_horizon(payload)
    adapter_name = str(payload.get("adapter", "deterministic")).strip().lower()
    adapter: MultimodalModelAdapter | None
    if adapter_name == "deterministic":
        adapter = None
    elif adapter_name == "litert_lm":
        command = os.environ.get("LITERT_LM_COMMAND", "").strip()
        if not command:
            raise OpenCodeBridgeError("LITERT_LM_COMMAND não está configurado pelo operador")
        adapter = LiteRTLMExternalAdapter(command)
    else:
        raise OpenCodeBridgeError("adapter do conselho deve ser 'deterministic' ou 'litert_lm'")

    image_values = payload.get("image_files", [])
    if image_values is None:
        image_values = []
    if not isinstance(image_values, list):
        raise OpenCodeBridgeError("image_files deve ser uma lista")
    images = [
        _resolve_inside(root, str(value), field="image_files") for value in image_values
    ]

    specialist_values = payload.get("specialists")
    if specialist_values is not None and not isinstance(specialist_values, list):
        raise OpenCodeBridgeError("specialists deve ser uma lista")
    specialists = (
        [str(value).strip() for value in specialist_values if str(value).strip()]
        if specialist_values is not None
        else None
    )

    try:
        result = MedicalSpecialistCouncil(adapter=adapter, seed=seed).run(
            case,
            image_files=images,
            selected_specialists=specialists,
            horizon_steps=horizon,
        )
    except (ValueError, RuntimeError) as exc:
        raise OpenCodeBridgeError(str(exc)) from exc

    data = result.to_dict()
    output_value = payload.get("output_file")
    artifact = (
        _resolve_inside(root, str(output_value), field="output_file")
        if output_value
        else root
        / ".opencode"
        / "artifacts"
        / "medical-council"
        / f"{result.council_id}.json"
    )
    _write_artifact(artifact, data)
    return {
        "ok": True,
        "operation": "council",
        "adapter": adapter_name,
        "case_id": case.case_id,
        "council_id": result.council_id,
        "twin_id": result.digital_twin.get("twin_id"),
        "artifact_path": str(artifact.relative_to(root)),
        "specialist_count": len(result.opinions),
        "specialists": [opinion.specialist_id for opinion in result.opinions],
        "contested_claim_count": len(result.synthesis.get("contested_claims", [])),
        "safety_decision": result.safety_review.get("decision"),
        "safety_findings": result.safety_review.get("findings", []),
        "safety": result.safety,
    }


def _seed_and_horizon(payload: dict[str, Any]) -> tuple[int, int]:
    try:
        seed = int(payload.get("seed", 42))
        horizon = int(payload.get("horizon", 4))
    except (TypeError, ValueError) as exc:
        raise OpenCodeBridgeError("seed e horizon devem ser inteiros") from exc
    return seed, horizon


def _write_artifact(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_inside(root: Path, raw_path: str, *, field: str) -> Path:
    value = raw_path.strip()
    if not value:
        raise OpenCodeBridgeError(f"{field} é obrigatório")
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if candidate != root and root not in candidate.parents:
        raise OpenCodeBridgeError(f"{field} deve permanecer dentro do worktree")
    return candidate
