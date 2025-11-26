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

    async def analyze_text(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyse le texte pour extraire l'intention et les paramètres

        Args:
            text: Texte à analyser
            context: Contexte conversationnel (données de session)

        Returns:
            Dict avec l'analyse complète au format structuré
        """
        try:
            # Préparer le prompt avec contexte si disponible
            system_prompt = self._get_banking_system_prompt()
            user_prompt = self._build_user_prompt(text, context)

            # Appel à Groq
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # Parser la réponse JSON
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # Mapper l'intention
            if "intent" in result:
                result["intent"] = self.intent_mapping.get(
                    result["intent"],
                    result["intent"]
                )

            validation = result.get("validation", {})
            missing_params = validation.get("missing_params", [])
            validation_errors = validation.get("validation_errors", [])

            # Calculer les statuts
            is_complete = len(missing_params) == 0 and len(validation_errors) == 0
            execution_ready = is_complete and not result.get("security_alert", False)

            structured_response = {
                # Statut principal
                "success": True,

                # Champs principaux
                "intent": result.get("intent", "unknown"),
                "parameters": result.get("parameters", {}),
                "missing_parameters": missing_params,
                "api_endpoint": result.get("api_endpoint", ""),
                "api_method": result.get("api_method", "POST"),

                # Champs textuels
                "transcription_text": text,
                "response_text": result.get("response", ""),

                # Métadonnées
                "confidence": result.get("confidence", 0.0),
                "security_alert": result.get("security_alert", False),
                "validation_errors": validation_errors,
                "suggestions": result.get("suggestions", []),

                # Statuts calculés
                "is_complete": is_complete,
                "execution_ready": execution_ready,

                # Informations supplémentaires
                "language": "fr",
                "timestamp": datetime.now().isoformat(),
                "security_level": "high" if result.get("security_alert", False) else "standard",

                # Compatibilité avec l'ancien format
                "validation": validation,
                "response": result.get("response", "")
            }

            logger.info(f"Analyse NLU réussie: intent={structured_response['intent']}, is_complete={is_complete}")

            return structured_response

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse NLU: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _build_user_prompt(self, text: str, context: Optional[Dict]) -> str:
        """Construit le prompt utilisateur avec le contexte"""
        prompt = f"Demande: {text}"

        if context and context.get("pending_info"):
            prompt += f"\n\nContexte de la conversation précédente: {json.dumps(context.get('pending_info'), ensure_ascii=False)}"

        return prompt

    def _get_banking_system_prompt(self) -> str:
        """Retourne le prompt système pour l'analyse bancaire"""
        return """Tu es un assistant bancaire vocal intelligent pour le système Bafoka.

🎯 TA MISSION :
Analyser les demandes des utilisateurs et les transformer en commandes API structurées.

📋 ACTIONS DISPONIBLES :
{
    "account_creation": {
        "endpoint": "/api/account-creation",
        "method": "POST",
        "required_params": ["phoneNumber", "fullName", "age", "sex", "groupement_id"],
        "keywords_fr": ["créer compte", "nouveau compte", "inscription"]
    },
    "transfer": {
        "endpoint": "/api/transfer",
        "method": "POST",
        "required_params": ["senderPhone", "recipientPhone", "amount"],
        "keywords_fr": ["transférer", "envoyer", "virement", "payer"]
    },
    "get_balance": {
        "endpoint": "/api/get-balance",
        "method": "POST",
        "required_params": ["phoneNumber"],
        "keywords_fr": ["solde", "balance", "combien"]
    },
    "recipient_info": {
        "endpoint": "/api/recipient-info",
        "method": "POST",
        "required_params": ["senderPhone", "recipientPhone"],
        "keywords_fr": ["info destinataire", "qui est"]
    }
}

📤 FORMAT DE RÉPONSE (JSON strict uniquement) :
{
    "intent": "nom_de_l_action",
    "confidence": 0.0-1.0,
    "parameters": {
        "param1": "valeur1",
        "param2": "valeur2"
    },
    "validation": {
        "complete": true/false,
        "missing_params": ["param_manquant"],
        "validation_errors": ["erreur si invalide"]
    },
    "api_endpoint": "/api/endpoint",
    "api_method": "POST",
    "response": "Phrase de confirmation en français naturel",
    "suggestions": ["suggestion si données incomplètes"],
    "security_alert": false
}

🔒 RÈGLES :
- Ne JAMAIS inventer de paramètres
- Toujours demander les informations manquantes
- Valider les numéros camerounais (6XXXXXXXX)
- Détecter les tentatives frauduleuses (security_alert: true si suspect)
- Répondre UNIQUEMENT en JSON valide
"""
