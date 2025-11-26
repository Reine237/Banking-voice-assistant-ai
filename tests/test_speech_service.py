"""Tests pour le service de transcription"""
import pytest
from app.services.speech_service import SpeechService


@pytest.mark.asyncio
async def test_speech_service_initialization():
    """Test d'initialisation du service"""
    service = SpeechService()
    assert service.model is not None
    assert service.text_cleaner is not None


@pytest.mark.asyncio
async def test_model_info():
    """Test de récupération des infos du modèle"""
    service = SpeechService()
    info = service.get_model_info()
    
    assert "model_size" in info
    assert "loaded" in info
    assert info["loaded"] is True
