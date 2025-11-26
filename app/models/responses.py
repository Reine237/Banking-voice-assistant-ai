"""Schémas de réponses API"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TranscriptionResponse(BaseModel):
    """Réponse de transcription audio"""
    success: bool
    text: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "text": "Je veux transférer cinq mille francs à Marie",
                "language": "fr",
                "confidence": 0.95
            }
        }


class NLUAnalysisResponse(BaseModel):
    """Réponse d'analyse NLU avec structure complète"""
    # Statut principal
    success: bool

    # Champs principaux
    intent: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    missing_parameters: Optional[List[str]] = None
    api_endpoint: Optional[str] = None
    api_method: Optional[str] = None

    # Champs textuels
    transcription_text: Optional[str] = None
    response_text: Optional[str] = None

    # Métadonnées
    confidence: Optional[float] = None
    security_alert: Optional[bool] = False
    validation_errors: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None

    # Statuts calculés
    is_complete: Optional[bool] = False
    execution_ready: Optional[bool] = False

    # Informations supplémentaires
    language: Optional[str] = None
    timestamp: Optional[str] = None
    security_level: Optional[str] = None

    # Champs compatibles avec l'ancien format
    validation: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "intent": "transfer",
                "parameters": {
                    "recipientPhone": "653112616",
                    "amount": "5000"
                },
                "missing_parameters": ["senderPhone"],
                "api_endpoint": "/api/transfer",
                "api_method": "POST",
                "transcription_text": "Je veux transférer cinq mille francs à Marie",
                "response_text": "Pour confirmer le transfert de 5000 FCFA, j'ai besoin de votre numéro.",
                "confidence": 0.92,
                "security_alert": False,
                "validation_errors": [],
                "suggestions": ["Merci de me communiquer votre numéro"],
                "is_complete": False,
                "execution_ready": False,
                "language": "fr",
                "timestamp": "2024-01-15T10:30:00",
                "security_level": "standard"
            }
        }


class VoiceProcessingResponse(BaseModel):
    """Réponse de traitement vocal complet"""
    success: bool
    user_id: str
    transcription: Optional[TranscriptionResponse] = None
    analysis: Optional[NLUAnalysisResponse] = None
    blockchain_response: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    requires_user_input: bool = False
    missing_information: Optional[List[str]] = None
    session_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "user_id": "+237653112616",
                "final_response": "Transfert de 5000 FCFA effectué avec succès vers Marie (653112616)",
                "requires_user_input": False,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
