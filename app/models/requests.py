"""Schémas de requêtes API"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class TranscribeRequest(BaseModel):
    """Requête de transcription audio"""
    user_id: str = Field(..., description="ID de l'utilisateur WhatsApp")
    language: Optional[str] = Field("fr", description="Code langue (fr, en, auto)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "+237653112616",
                "language": "fr"
            }
        }


class AnalyzeRequest(BaseModel):
    """Requête d'analyse NLU"""
    text: str = Field(..., description="Texte à analyser")
    user_id: str = Field(..., description="ID de l'utilisateur")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexte conversationnel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Je veux transférer 5000 francs à Marie",
                "user_id": "653112616",
                "context": {}
            }
        }


class ProcessVoiceRequest(BaseModel):
    """Requête de traitement vocal complet"""
    user_id: str = Field(..., description="ID de l'utilisateur WhatsApp")
    language: Optional[str] = Field("fr", description="Code langue")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "653112616",
                "language": "fr"
            }
        }


class BafokaActionRequest(BaseModel):
    """Requête d'action vers la blockchain Bafoka"""
    intent: str = Field(..., description="Action à exécuter")
    parameters: Dict[str, Any] = Field(..., description="Paramètres de l'action")
    user_phone: str = Field(..., description="Numéro de téléphone de l'utilisateur")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "transfer",
                "parameters": {
                    "senderPhone": "653112616",
                    "recipientPhone": "658835899",
                    "amount": "5000"
                },
                "user_phone": "+237653112616"
            }
        }
