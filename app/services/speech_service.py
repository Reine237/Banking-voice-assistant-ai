"""Service de transcription audio (Speech-to-Text)"""
import whisper
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from app.config import get_settings
from app.utils.text_cleaner import TextCleaner

settings = get_settings()


class SpeechService:
    """Service de transcription audio avec Whisper"""
    
    def __init__(self):
        self.model = None
        self.text_cleaner = TextCleaner()
        self.model_size = settings.whisper_model_size
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle Whisper"""
        try:
            logger.info(f"Chargement du modèle Whisper '{self.model_size}'...")
            self.model = whisper.load_model(self.model_size)
            logger.success(f"Modèle Whisper '{self.model_size}' chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle Whisper: {e}")
            raise
    
    async def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = "fr"
    ) -> Dict:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_path: Chemin vers le fichier audio
            language: Code langue (fr, en, auto)
        
        Returns:
            Dict avec le texte transcrit et métadonnées
        """
        try:
            # Vérifier que le fichier existe
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Fichier audio introuvable: {audio_path}")
            
            # Normalisation audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Transcription avec Whisper
            result = self.model.transcribe(
                audio_path,
                language=None if language == "auto" else language,
                fp16=False
            )
            
            # Calcul de la confiance
            confidences = [
                seg.get('confidence', 0.5)
                for seg in result.get('segments', [])
                if 'confidence' in seg
            ]
            confidence = np.mean(confidences) if confidences else 0.5
            
            # Nettoyage du texte transcrit
            cleaned_text = self.text_cleaner.clean_transcription(result["text"])
            
            logger.info(f"Transcription réussie: {cleaned_text[:50]}...")
            
            return {
                "success": True,
                "text": cleaned_text,
                "raw_text": result["text"],
                "language": result["language"],
                "confidence": float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict:
        """Retourne les informations sur le modèle chargé"""
        return {
            "model_size": self.model_size,
            "loaded": self.model is not None
        }
