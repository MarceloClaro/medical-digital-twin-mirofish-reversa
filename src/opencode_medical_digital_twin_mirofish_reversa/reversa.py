"""Revisão adversarial Reversa para simulações médicas."""
from __future__ import annotations

from typing import Any

from .models import SimulationCase, TwinState


class ReversaMedicalReviewer:
    """Audita completude, excesso de confiança e inferências causais indevidas."""

    def review(
        self,
        *,
        case: SimulationCase,
        trajectories: list[TwinState],
        swarm: dict[str, Any],
        completeness: float,
    ) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        consensus = float(swarm.get("consensus", 0.0))
        dispersion = float(swarm.get("dispersion", 1.0))

        if completeness < 0.60:
            findings.append({
                "severity": "high",
                "code": "REV-DATA-001",
                "message": "Caso sintético incompleto; trajetórias não podem ser interpretadas como prognóstico.",
            })
        if consensus > 0.90 and dispersion < 0.08:
            findings.append({
                "severity": "medium",
                "code": "REV-CONS-001",
                "message": "Convergência interna alta não demonstra validade clínica externa.",
            })
        if any(state.uncertainty < 0.10 for state in trajectories):
            findings.append({
                "severity": "high",
                "code": "REV-UNC-001",
                "message": "Incerteza artificialmente baixa em pelo menos uma trajetória.",
            })
        if any(_looks_prescriptive(action) for action in case.scenario_actions):
            findings.append({
                "severity": "high",
                "code": "REV-RX-001",
                "message": "Ação de cenário contém linguagem prescritiva incompatível com simulação educacional.",
            })
        if not findings:
            findings.append({
                "severity": "info",
                "code": "REV-OK-001",
                "message": "Nenhum desvio estrutural crítico; revisão humana permanece obrigatória.",
            })

        blocked = any(item["severity"] == "high" for item in findings)
        return {
            "reviewer": "reversa-medical-adversarial/1.0",
            "decision": "block_clinical_use" if blocked else "simulation_only",
            "findings": findings,
            "counterfactual_questions": [
                "Qual variável omitida poderia inverter a trajetória?",
                "A direção causal foi confundida com associação?",
                "Quais premissas são frágeis ou não observáveis?",
                "O resultado se mantém sob um cenário pessimista e um cenário nulo?",
            ],
        }


def _looks_prescriptive(text: str) -> bool:
    lowered = text.lower()
    terms = ("prescrever", "receitar", "dose de", "suspender medicamento", "iniciar tratamento")
    return any(term in lowered for term in terms)
