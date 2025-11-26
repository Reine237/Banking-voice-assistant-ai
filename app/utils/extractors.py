"""Extracteurs de données structurées"""
import json
from typing import Dict, Any
from loguru import logger


class JSONExtractor:
    """Extraction et structuration de JSON depuis les résultats du pipeline"""
    
    @staticmethod
    def extract_from_pipeline(result_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrait les champs principaux d'un résultat de pipeline complet
        
        Args:
            result_json: Résultat complet du pipeline
        
        Returns:
            JSON structuré avec les champs essentiels
        """
        try:
            pipeline_steps = result_json.get("pipeline_steps", {})
            nlu = pipeline_steps.get("nlu_analysis", {})
            transcription = pipeline_steps.get("transcription", {})
            validation = nlu.get("validation", {})
            
            extracted = {
                "intent": nlu.get("intent"),
                "parameters": nlu.get("parameters", {}),
                "missing_parameters": validation.get("missing_params", []),
                "api_endpoint": nlu.get("api_endpoint"),
                "api_method": nlu.get("api_method"),
                "transcription_text": transcription.get("text"),
                "response_text": nlu.get("response"),
                "confidence": nlu.get("confidence", 0.0),
                "security_alert": nlu.get("security_alert", False),
                "validation_errors": validation.get("validation_errors", []),
                "suggestions": nlu.get("suggestions", []),
                "is_complete": not validation.get("missing_params"),
                "success": result_json.get("success", False) and nlu.get("success", False),
                "execution_ready": result_json.get("execution_ready", False),
                "language": transcription.get("language"),
                "timestamp": pipeline_steps.get("structured_output", {}).get("timestamp"),
                "security_level": pipeline_steps.get("orchestration", {}).get("security_level")
            }
            
            return extracted
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction JSON: {e}")
            return {"error": str(e)}
