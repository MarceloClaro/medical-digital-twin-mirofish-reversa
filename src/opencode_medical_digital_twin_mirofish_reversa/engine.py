"""Motor reproduzível do gêmeo digital médico exclusivamente simulado."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from .adapters import DeterministicSwarmAdapter, SwarmAdapter
from .models import DigitalTwinResult, SimulationCase, TwinState
from .reversa import ReversaMedicalReviewer

Clock = Callable[[], datetime]


class MedicalDigitalTwinEngine:
    CONTRACT_VERSION = "medical-digital-twin/1.0"

    def __init__(
        self,
        *,
        swarm: SwarmAdapter | None = None,
        reversa: ReversaMedicalReviewer | None = None,
        seed: int = 42,
        clock: Clock | None = None,
    ) -> None:
        self.swarm = swarm or DeterministicSwarmAdapter()
        self.reversa = reversa or ReversaMedicalReviewer()
        self.seed = seed
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def simulate(self, case: SimulationCase, *, horizon_steps: int = 4, run_id: str | None = None) -> DigitalTwinResult:
        case.validate()
        if horizon_steps < 2 or horizon_steps > 12:
            raise ValueError("horizon_steps deve estar entre 2 e 12")

        canonical = {
            "case": case.to_dict(),
            "horizon_steps": horizon_steps,
            "seed": self.seed,
            "contract_version": self.CONTRACT_VERSION,
        }
        canonical_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        source_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        stable_twin_id = "mdt-" + uuid.uuid5(uuid.NAMESPACE_URL, source_hash).hex[:16]
        run_id = run_id or stable_twin_id

        completeness = self._completeness(case)
        base_signal = self._base_signal(case.hypotheses, completeness)
        swarm = self.swarm.simulate(
            question=f"trajetória sintética {source_hash[:16]}", signal=base_signal, seed=self.seed
        )
        aggregate = _bounded(float(swarm["aggregate"]))
        consensus = _bounded(float(swarm["consensus"]))
        actions = case.scenario_actions or ["observação sintética", "coleta simulada de dados"]

        trajectories: list[TwinState] = []
        for step in range(horizon_steps):
            progress = step / max(horizon_steps - 1, 1)
            drift = progress * (aggregate - 0.5) * 0.35
            outcome = _bounded(base_signal + drift)
            uncertainty = _bounded(max(0.12, 1.0 - completeness * 0.55 - consensus * 0.25 + step * 0.03))
            trajectories.append(TwinState(
                step=step,
                label=f"T{step}",
                state_vector={
                    "stability_index": round(outcome, 6),
                    "data_completeness": round(completeness, 6),
                    "swarm_consensus": round(consensus, 6),
                },
                scenario_action=actions[min(step, len(actions) - 1)],
                outcome_index=round(outcome, 6),
                uncertainty=round(uncertainty, 6),
                assumptions=[
                    "caso inteiramente sintético",
                    "sem calibração clínica externa",
                    "sem atribuição causal à ação de cenário",
                    "não representa uma pessoa real",
                ],
            ))

        review = self.reversa.review(
            case=case, trajectories=trajectories, swarm=swarm, completeness=completeness
        )
        return DigitalTwinResult(
            twin_id=stable_twin_id,
            run_id=run_id,
            created_at_utc=self.clock().astimezone(timezone.utc).isoformat(),
            simulation_only=True,
            source_hash=source_hash,
            contract_version=self.CONTRACT_VERSION,
            trajectories=trajectories,
            swarm={
                "engine": swarm.get("adapter", getattr(self.swarm, "name", "unknown")),
                "aggregate": round(aggregate, 6),
                "consensus": round(consensus, 6),
                "dispersion": round(float(swarm.get("dispersion", 0.0)), 6),
                "n_agents": int(swarm.get("n_agents", 0)),
                "interpretation": "dispersão de cenários sintéticos; não é probabilidade clínica",
                "trace": swarm.get("trace", {}),
            },
            reversa_review=review,
            safety={
                "clinical_use_allowed": False,
                "prescription_allowed": False,
                "diagnostic_claim_allowed": False,
                "prognostic_claim_allowed": False,
                "real_patient_data_allowed": False,
                "human_review_required": True,
                "warning": "Uso educacional/metodológico. Não usar para decisões sobre pacientes reais.",
            },
            reproducibility={
                "canonical_sha256": source_hash,
                "seed": self.seed,
                "horizon_steps": horizon_steps,
                "adapter": swarm.get("adapter", getattr(self.swarm, "name", "unknown")),
            },
        )

    @staticmethod
    def _completeness(case: SimulationCase) -> float:
        values: list[Any] = [
            case.profile.get("age_group") or case.profile.get("age_years"),
            case.profile.get("sex_at_birth"),
            case.clinical_data.get("history"),
            case.clinical_data.get("vital_signs"),
            case.clinical_data.get("lab_results"),
        ]
        return sum(value not in (None, "", [], {}) for value in values) / len(values)

    @staticmethod
    def _base_signal(hypotheses: list[dict[str, Any]], completeness: float) -> float:
        severe = sum(item.get("status") in {"grave_não_perder", "must_not_miss"} for item in hypotheses)
        return _bounded(0.55 + completeness * 0.15 - min(severe, 2) * 0.12)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
