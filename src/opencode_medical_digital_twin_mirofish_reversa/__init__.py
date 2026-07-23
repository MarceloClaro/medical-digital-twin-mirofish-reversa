"""OpenCode Medical Digital Twin — MiroFish + Reversa + Specialist Council."""

from .council import MedicalCouncilResult, MedicalSpecialistCouncil
from .engine import MedicalDigitalTwinEngine
from .model_fabric import DeterministicMultimodalAdapter, LiteRTLMExternalAdapter
from .models import DigitalTwinResult, SimulationCase, TwinState
from .reversa import ReversaMedicalReviewer
from .specialists import DEFAULT_SPECIALISTS, SpecialistOpinion, SpecialistProfile

__all__ = [
    "DEFAULT_SPECIALISTS",
    "DeterministicMultimodalAdapter",
    "DigitalTwinResult",
    "LiteRTLMExternalAdapter",
    "MedicalCouncilResult",
    "MedicalDigitalTwinEngine",
    "MedicalSpecialistCouncil",
    "ReversaMedicalReviewer",
    "SimulationCase",
    "SpecialistOpinion",
    "SpecialistProfile",
    "TwinState",
]

__version__ = "0.2.0"
