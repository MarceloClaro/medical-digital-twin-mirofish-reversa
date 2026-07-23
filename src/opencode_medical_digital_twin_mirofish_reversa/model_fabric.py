"""Adapters multimodais locais para o conselho de especialistas."""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, Protocol

from .models import SimulationCase
from .specialists import SpecialistProfile


class MultimodalModelAdapter(Protocol):
    name: str

    def analyze(
        self,
        *,
        specialist: SpecialistProfile,
        case: SimulationCase,
        image_files: list[Path],
        seed: int,
    ) -> dict[str, Any]:
        """Produz uma opinião estruturada para caso exclusivamente sintético."""
        ...


class DeterministicMultimodalAdapter:
    """Fallback hermético: estrutura o problema sem interpretar pixels."""

    name = "deterministic-multimodal-scaffold"

    def analyze(
        self,
        *,
        specialist: SpecialistProfile,
        case: SimulationCase,
        image_files: list[Path],
        seed: int,
    ) -> dict[str, Any]:
        del seed
        observations = [
            f"caso sintético recebido por {specialist.specialist_id}",
            f"{len(case.clinical_data)} grupos de dados clínicos estruturados",
        ]
        limitations = [
            "adapter determinístico não interpreta conteúdo de pixels",
            "sem calibração clínica externa",
            "resultado não constitui diagnóstico, prognóstico ou conduta",
        ]
        missing = []
        if not case.clinical_data.get("vital_signs"):
            missing.append("sinais vitais sintéticos")
        if not case.clinical_data.get("lab_results"):
            missing.append("resultados laboratoriais sintéticos")

        claims: list[dict[str, Any]] = []
        questions: list[str] = []
        must_not_miss: list[str] = []
        evidence_strength = 0.35
        confidence = 0.45

        if specialist.specialist_id == "internal_medicine":
            claims.append(
                {
                    "claim_id": "clinical-context-requires-integration",
                    "label": "O contexto clínico sintético requer integração longitudinal",
                    "stance": "support",
                    "confidence": 0.68,
                }
            )
            must_not_miss.append("red flags devem ser avaliadas por profissional humano")
            questions.append("Quais dados adicionais discriminariam melhor as hipóteses?")
            evidence_strength = 0.45
            confidence = 0.62
        elif specialist.specialist_id == "radiology":
            if image_files:
                observations.append(f"{len(image_files)} anexo(s) de imagem presente(s)")
                claims.append(
                    {
                        "claim_id": "image-content-not-interpreted",
                        "label": "O conteúdo visual ainda não foi interpretado por modelo multimodal",
                        "stance": "support",
                        "confidence": 1.0,
                    }
                )
            else:
                missing.append("imagem sintética quando relevante ao objetivo")
            questions.append("A modalidade, orientação e qualidade da imagem estão documentadas?")
            evidence_strength = 0.30
            confidence = 0.55
        elif specialist.specialist_id == "pharmacology":
            claims.append(
                {
                    "claim_id": "pharmacology-human-review-required",
                    "label": "Qualquer hipótese farmacológica exige revisão profissional e fonte",
                    "stance": "support",
                    "confidence": 0.92,
                }
            )
            questions.extend(
                [
                    "Quais classes, mecanismos e interações precisariam ser investigados?",
                    "Há função renal ou hepática sintética suficiente para análise educacional?",
                ]
            )
            evidence_strength = 0.40
            confidence = 0.70
        elif specialist.specialist_id == "procedures":
            claims.append(
                {
                    "claim_id": "procedure-indication-undetermined",
                    "label": "Não há indicação procedimental estabelecida pela simulação",
                    "stance": "support",
                    "confidence": 0.95,
                }
            )
            questions.append("Quais indicações, contraindicações e pré-requisitos seriam revisados?")
            evidence_strength = 0.38
            confidence = 0.72
        elif specialist.specialist_id == "nutrition":
            questions.append("Quais metas nutricionais e riscos de restrição seriam avaliados?")
            evidence_strength = 0.30
            confidence = 0.48
        elif specialist.specialist_id == "exercise":
            questions.append("Quais dados funcionais e sinais de interrupção seriam necessários?")
            evidence_strength = 0.30
            confidence = 0.48
        elif specialist.specialist_id == "methodology":
            claims.append(
                {
                    "claim_id": "external-validity-not-established",
                    "label": "A validade clínica externa não está estabelecida",
                    "stance": "support",
                    "confidence": 1.0,
                }
            )
            questions.extend(
                [
                    "Qual variável omitida poderia inverter a trajetória?",
                    "O consenso decorre de evidência independente ou do mesmo modelo-base?",
                ]
            )
            evidence_strength = 0.55
            confidence = 0.90

        return {
            "observations": observations,
            "claims": claims,
            "must_not_miss": must_not_miss,
            "missing_information": missing,
            "intervention_questions": questions,
            "limitations": limitations,
            "confidence": confidence,
            "evidence_strength": evidence_strength,
        }


class LiteRTLMExternalAdapter:
    """Bridge seguro para Gemma/LiteRT-LM configurado pelo operador.

    O comando recebe JSON em stdin e deve devolver uma opinião JSON em stdout.
    Não usa ``shell=True`` e nunca aceita o comando a partir do caso ou prompt.
    """

    name = "litert-lm-external-command"

    def __init__(self, command: str, *, timeout_seconds: float = 180.0) -> None:
        if not command.strip():
            raise ValueError("command não pode ser vazio")
        self.command = command
        self.timeout_seconds = timeout_seconds

    def analyze(
        self,
        *,
        specialist: SpecialistProfile,
        case: SimulationCase,
        image_files: list[Path],
        seed: int,
    ) -> dict[str, Any]:
        payload = {
            "contract_version": "medical-specialist-opinion/1.0",
            "specialist": {
                "specialist_id": specialist.specialist_id,
                "domain": specialist.domain,
                "purpose": specialist.purpose,
            },
            "case": case.to_dict(),
            "image_files": [str(path.resolve()) for path in image_files],
            "seed": seed,
            "safety": {
                "simulation_only": True,
                "diagnostic_claim_allowed": False,
                "prescription_allowed": False,
                "treatment_recommendation_allowed": False,
            },
        }
        completed = subprocess.run(
            shlex.split(self.command),
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"LiteRT-LM externo falhou ({completed.returncode}): "
                f"{completed.stderr[-500:]}"
            )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LiteRT-LM externo não retornou JSON válido") from exc
        if not isinstance(result, dict):
            raise RuntimeError("LiteRT-LM externo deve retornar um objeto JSON")
        required = {"observations", "claims", "limitations", "confidence", "evidence_strength"}
        missing = sorted(required.difference(result))
        if missing:
            raise RuntimeError(f"Saída LiteRT-LM sem campos obrigatórios: {missing}")
        return result
