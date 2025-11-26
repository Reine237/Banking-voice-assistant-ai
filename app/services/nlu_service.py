"""Service d'analyse NLU avec Groq"""
import json
from groq import Groq
from typing import Dict, Optional
from datetime import datetime
from loguru import logger
from app.config import get_settings

settings = get_settings()


class NLUService:
    """Service d'analyse du langage naturel avec Groq"""

    def __init__(self):
        self.groq_client = Groq(api_key=settings.groq_api_key)
        self.intent_mapping = {
            "transfer": "faire_virement",
            "balance": "consulter_solde",
            "payment": "payer_facture",
            "add_beneficiary": "ajouter_beneficiaire",
            "account_creation": "creer_compte"
        }

    # -------------------------------------------------------------------------
    # 🔥 NOUVELLE DÉTECTION DE LANGUE — Basée sur Groq uniquement
    # -------------------------------------------------------------------------
    def _detect_language(self, text: str) -> str:
        """
        Détection de la langue via Groq (très fiable)
        Retourne uniquement 'fr' ou 'en'
        """
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Detect the language of this text. "
                            "Respond ONLY with 'fr' for French or 'en' for English. "
                            "No other output."
                        )
                    },
                    {"role": "user", "content": text}
                ],
            )

            lang = response.choices[0].message.content.strip().lower()
            if lang not in ["fr", "en"]:
                logger.warning(f"Langue inattendue détectée: {lang}. Fallback -> fr")
                return "fr"

            logger.info(f"Langue détectée: {lang} pour le texte: {text}")
            return lang

        except Exception as e:
            logger.error(f"Erreur détecteur de langue: {e}")
            return "fr"

    # -------------------------------------------------------------------------
    # 🔥 Analyse complète avec Groq
    # -------------------------------------------------------------------------
    async def analyze_text(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyse le texte pour extraire l'intention et les paramètres"""

        try:
            # Détection automatique de langue
            detected_language = self._detect_language(text)

            # Construction des prompts
            system_prompt = self._get_banking_system_prompt(detected_language)
            user_prompt = self._build_user_prompt(text, context)

            # Appel Groq NLU
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # JSON strict
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # Mapping d'intention bancaires
            if "intent" in result:
                result["intent"] = self.intent_mapping.get(
                    result["intent"],
                    result["intent"]
                )

            # Extraction des champs
            validation = result.get("validation", {})
            missing_params = validation.get("missing_params", [])
            validation_errors = validation.get("validation_errors", [])

            is_complete = len(missing_params) == 0 and len(validation_errors) == 0
            execution_ready = is_complete and not result.get("security_alert", False)

            structured_response = {
                "success": True,

                "intent": result.get("intent", "unknown"),
                "parameters": result.get("parameters", {}),
                "missing_parameters": missing_params,
                "api_endpoint": result.get("api_endpoint", ""),
                "api_method": result.get("api_method", "POST"),

                "transcription_text": text,
                "response_text": result.get("response", ""),

                "confidence": result.get("confidence", 0.0),
                "security_alert": result.get("security_alert", False),
                "validation_errors": validation_errors,
                "suggestions": result.get("suggestions", []),

                "is_complete": is_complete,
                "execution_ready": execution_ready,

                "language": detected_language,
                "timestamp": datetime.now().isoformat(),
                "security_level": "high" if result.get("security_alert", False) else "standard",

                "validation": validation,
                "response": result.get("response", "")
            }

            logger.info(
                f"Analyse NLU OK — intent={structured_response['intent']}, "
                f"lang={detected_language}, complete={is_complete}"
            )

            return structured_response

        except Exception as e:
            logger.error(f"Erreur analyse NLU: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # -------------------------------------------------------------------------
    def _build_user_prompt(self, text: str, context: Optional[Dict]) -> str:
        """Construit le prompt utilisateur avec contexte"""
        prompt = f"Demande: {text}"

        if context and context.get("pending_info"):
            prompt += (
                f"\n\nContexte conversationnel précédent: "
                f"{json.dumps(context.get('pending_info'), ensure_ascii=False)}"
            )

        return prompt

    # -------------------------------------------------------------------------
    # 🔥 Prompts bancaires FR / EN
    # -------------------------------------------------------------------------
    def _get_banking_system_prompt(self, language: str = "fr") -> str:

        # ---------------------- ENGLISH PROMPT --------------------------------
        if language == "en":
            return """
You are an intelligent banking voice assistant for the Bafoka system.

🎯 YOUR MISSION:
Analyze user requests and convert them into structured API instructions.

📤 OUTPUT FORMAT (STRICT JSON only):
{
    "intent": "action",
    "confidence": 0.0-1.0,
    "parameters": {},
    "validation": {
        "complete": true/false,
        "missing_params": [],
        "validation_errors": []
    },
    "api_endpoint": "",
    "api_method": "POST",
    "response": "Natural English response",
    "suggestions": [],
    "security_alert": false
}

🔒 RULES:
- NEVER invent missing parameters
- Ask for missing data
- Validate Cameroonian phone numbers (6XXXXXXXX)
- Flag suspicious actions (security_alert: true)
- Respond ONLY in valid JSON
- Response text MUST be in English
"""

        # ---------------------- FRENCH PROMPT --------------------------------
        return """
Tu es un assistant vocal bancaire intelligent pour le système Bafoka.

🎯 TA MISSION :
Analyser les demandes des utilisateurs et les transformer en commandes API structurées.

📤 FORMAT DE RÉPONSE (JSON strict uniquement) :
{
    "intent": "action",
    "confidence": 0.0-1.0,
    "parameters": {},
    "validation": {
        "complete": true/false,
        "missing_params": [],
        "validation_errors": []
    },
    "api_endpoint": "",
    "api_method": "POST",
    "response": "Réponse naturelle en français",
    "suggestions": [],
    "security_alert": false
}

🔒 RÈGLES :
- Ne JAMAIS inventer de paramètres
- Toujours demander les informations manquantes
- Valider les numéros camerounais (6XXXXXXXX)
- Détecter les tentatives frauduleuses
- Répondre UNIQUEMENT en JSON valide
- Les textes doivent être en français
"""
