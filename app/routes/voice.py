"""Endpoints pour le traitement vocal"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
from pathlib import Path
import shutil
from loguru import logger

from app.models.requests import AnalyzeRequest, ProcessVoiceRequest, BafokaActionRequest
from app.models.responses import (
    TranscriptionResponse,
    NLUAnalysisResponse,
    VoiceProcessingResponse,
    ErrorResponse
)
from app.services import (
    SpeechService,
    NLUService,
    BlockchainService,
    ConversationService
)
from app.utils.validators import Validator

router = APIRouter(prefix="/voice", tags=["Voice Processing"])

# Initialisation des services (singleton)
speech_service = SpeechService()
nlu_service = NLUService()
blockchain_service = BlockchainService()
conversation_service = ConversationService()


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcription audio vers texte",
    description="Convertit un fichier audio en texte avec Whisper"
)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Fichier audio à transcrire"),
    user_id: str = None,
    language: Optional[str] = "fr"
):
    """
    **Transcription Speech-to-Text**
    
    Convertit un fichier audio (vocal WhatsApp) en texte.
    
    - **audio_file**: Fichier audio (mp3, wav, ogg, m4a, webm)
    - **user_id**: ID de l'utilisateur (numéro WhatsApp)
    - **language**: Code langue (fr, en, auto)
    """
    try:
        # Créer le dossier temporaire
        audio_dir = Path("data/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier temporairement
        temp_path = audio_dir / f"temp_{user_id or 'unknown'}_{audio_file.filename}"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Transcription
        result = await speech_service.transcribe_audio(str(temp_path), language)
        
        # Nettoyer le fichier temporaire
        temp_path.unlink()
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return TranscriptionResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze",
    response_model=NLUAnalysisResponse,
    summary="Analyse NLU du texte",
    description="Analyse le texte pour extraire l'intention et les paramètres"
)
async def analyze_text(request: AnalyzeRequest):
    """
    **Analyse du langage naturel**
    
    Analyse le texte transcrit pour identifier:
    - L'intention de l'utilisateur (transfert, solde, etc.)
    - Les paramètres extraits (montant, destinataire, etc.)
    - Les informations manquantes
    - L'action à réaliser sur la blockchain
    
    Supporte la gestion du contexte conversationnel.
    """
    try:
        # Récupérer le contexte si disponible
        session = conversation_service.get_session(request.user_id)
        context = session.get("data") if session else None
        
        # Analyse NLU
        result = await nlu_service.analyze_text(request.text, context)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        # Si des paramètres manquent, sauvegarder le contexte
        validation = result.get("validation", {})
        if not validation.get("complete", False):
            conversation_service.add_pending_info(
                request.user_id,
                result["intent"],
                result.get("parameters", {}),
                validation.get("missing_params", [])
            )
        
        return NLUAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur analyse NLU: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/blockchain/execute",
    summary="Exécution directe d'une action blockchain",
    description="Exécute directement une action sur la blockchain Bafoka"
)
async def execute_blockchain_action(request: BafokaActionRequest):
    """
    **Exécution directe sur la blockchain**
    
    Permet d'exécuter manuellement une action sur l'API Bafoka.
    Utile pour les tests ou les intégrations spécifiques.
    """
    try:
        result = await blockchain_service.execute_action(
            request.intent,
            "POST",
            request.parameters
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur exécution blockchain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/session/{user_id}",
    summary="Récupérer la session utilisateur",
    description="Récupère le contexte conversationnel d'un utilisateur"
)
async def get_user_session(user_id: str):
    """
    **Consultation du contexte conversationnel**
    
    Récupère les données de session d'un utilisateur:
    - Informations en attente de complétion
    - Historique des interactions
    - Paramètres déjà collectés
    """
    session = conversation_service.get_session(user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou expirée")
    
    return session


@router.delete(
    "/session/{user_id}",
    summary="Supprimer la session utilisateur",
    description="Efface le contexte conversationnel d'un utilisateur"
)
async def clear_user_session(user_id: str):
    """
    **Réinitialisation de session**
    
    Efface toutes les données de session d'un utilisateur.
    """
    conversation_service.clear_session(user_id)
    return {"message": f"Session supprimée pour {user_id}"}
