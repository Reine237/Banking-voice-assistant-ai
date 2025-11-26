"""Modèles de données de l'application"""
from .requests import (
    TranscribeRequest,
    AnalyzeRequest,
    ProcessVoiceRequest,
    BafokaActionRequest
)
from .responses import (
    TranscriptionResponse,
    NLUAnalysisResponse,
    VoiceProcessingResponse,
    ErrorResponse
)

__all__ = [
    "TranscribeRequest",
    "AnalyzeRequest",
    "ProcessVoiceRequest",
    "BafokaActionRequest",
    "TranscriptionResponse",
    "NLUAnalysisResponse",
    "VoiceProcessingResponse",
    "ErrorResponse",
]
