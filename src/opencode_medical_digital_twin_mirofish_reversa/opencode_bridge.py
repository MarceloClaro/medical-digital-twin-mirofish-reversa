"""Bridge seguro entre OpenCode e o motor de simulação sintética."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .adapters import MiroFishExternalAdapter
from .engine import MedicalDigitalTwinEngine
from .models import SimulationCase


class OpenCodeBridgeError(RuntimeError):
    """Erro de contrato ou segurança apresentado ao OpenCode."""


def execute_opencode_request(payload: dict[str, Any], *, worktree: Path) -> dict[str, Any]:
    root = worktree.resolve()
    operation = str(payload.get("operation", "simulate")).strip().lower()
    if operation not in {"validate", "simulate"}:
        raise OpenCodeBridgeError("operation deve ser 'validate' ou 'simulate'")

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

    return _simulate(payload, root=root, case=case)


def _simulate(payload: dict[str, Any], *, root: Path, case: SimulationCase) -> dict[str, Any]:
    try:
        seed = int(payload.get("seed", 42))
        horizon = int(payload.get("horizon", 4))
    except (TypeError, ValueError) as exc:
        raise OpenCodeBridgeError("seed e horizon devem ser inteiros") from exc

    adapter_name = str(payload.get("adapter", "deterministic")).strip().lower()
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
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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


def _resolve_inside(root: Path, raw_path: str, *, field: str) -> Path:
    value = raw_path.strip()
    if not value:
        raise OpenCodeBridgeError(f"{field} é obrigatório")
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if candidate != root and root not in candidate.parents:
        raise OpenCodeBridgeError(f"{field} deve permanecer dentro do worktree")
    return candidate
