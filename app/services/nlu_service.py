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

    def _detect_language(self, text: str) -> str:
        """
        Détecte la langue du texte (fr ou en)
        Utilise une analyse de mots-clés et structure grammaticale
        """
        text_lower = text.lower()

        english_keywords = [
            # Verbes anglais courants
            'want', 'send', 'transfer', 'check', 'create', 'make', 'get',
            'withdraw', 'deposit', 'pay', 'need', 'have',
            # Mots bancaires anglais
            'balance', 'account', 'payment', 'money', 'dollar',
            # Articles et prépositions anglais (très discriminants)
            'the', 'my', 'to', 'from', 'with', 'for', 'of', 'in', 'on',
            # Pronoms anglais
            'i', 'you', 'he', 'she', 'we', 'they'
        ]

        french_keywords = [
            # Verbes français courants
            'veux', 'vouloir', 'envoyer', 'transférer', 'transferer', 'vérifier',
            'créer', 'creer', 'faire', 'avoir', 'besoin', 'payer',
            'retirer', 'déposer', 'deposer',
            # Mots bancaires français
            'solde', 'compte', 'paiement', 'argent', 'franc', 'francs',
            # Articles français (très discriminants)
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de',
            # Pronoms et prépositions français
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'mon', 'ma', 'mes',
            'à', 'au', 'aux', 'pour', 'avec', 'dans', 'sur'
        ]

        english_score = 0
        french_score = 0

        # Découper le texte en mots
        words = text_lower.split()

        for word in words:
            # Retirer la ponctuation pour une meilleure correspondance
            clean_word = word.strip('.,!?;:')

            # Les articles et pronoms ont un poids plus important (x2)
            if clean_word in ['the', 'my', 'i', 'to']:
                english_score += 2
            elif clean_word in english_keywords:
                english_score += 1

            if clean_word in ['le', 'la', 'mon', 'ma', 'je', 'à']:
                french_score += 2
            elif clean_word in french_keywords:
                french_score += 1

        logger.info(f"Language detection - Text: '{text}' | EN score: {english_score} | FR score: {french_score}")

        # Si score anglais strictement supérieur, retourner 'en'
        return "en" if english_score > french_score else "fr"

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
            detected_language = self._detect_language(text)

            # Préparer le prompt avec contexte si disponible
            system_prompt = self._get_banking_system_prompt(detected_language)
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

                "language": detected_language,
                "timestamp": datetime.now().isoformat(),
                "security_level": "high" if result.get("security_alert", False) else "standard",

                # Compatibilité avec l'ancien format
                "validation": validation,
                "response": result.get("response", "")
            }

            logger.info(f"Analyse NLU réussie: intent={structured_response['intent']}, language={detected_language}, is_complete={is_complete}")

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

    def _get_banking_system_prompt(self, language: str = "fr") -> str:
        """Retourne le prompt système pour l'analyse bancaire"""

        if language == "en":
            return """You are an intelligent voice banking assistant for the Bafoka system.

🎯 YOUR MISSION:
Analyze user requests and transform them into structured API commands.

📋 AVAILABLE ACTIONS:
{
    "account_creation": {
        "endpoint": "/api/account-creation",
        "method": "POST",
        "required_params": ["phoneNumber", "fullName", "age", "sex", "groupement_id"],
        "keywords_en": ["create account", "new account", "sign up", "register"]
    },
    "transfer": {
        "endpoint": "/api/transfer",
        "method": "POST",
        "required_params": ["senderPhone", "recipientPhone", "amount"],
        "keywords_en": ["transfer", "send", "payment", "pay"]
    },
    "get_balance": {
        "endpoint": "/api/get-balance",
        "method": "POST",
        "required_params": ["phoneNumber"],
        "keywords_en": ["balance", "check balance", "how much"]
    },
    "recipient_info": {
        "endpoint": "/api/recipient-info",
        "method": "POST",
        "required_params": ["senderPhone", "recipientPhone"],
        "keywords_en": ["recipient info", "who is"]
    }
}

📤 RESPONSE FORMAT (strict JSON only):
{
    "intent": "action_name",
    "confidence": 0.0-1.0,
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    },
    "validation": {
        "complete": true/false,
        "missing_params": ["missing_param"],
        "validation_errors": ["error if invalid"]
    },
    "api_endpoint": "/api/endpoint",
    "api_method": "POST",
    "response": "Confirmation sentence in natural English",
    "suggestions": ["suggestion if incomplete data"],
    "security_alert": false
}

🔒 RULES:
- NEVER invent parameters
- Always ask for missing information
- Validate Cameroonian phone numbers (6XXXXXXXX)
- Detect fraudulent attempts (security_alert: true if suspicious)
- Respond ONLY in valid JSON
- ALL response texts MUST be in English
"""

        else:  # French by default
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
- TOUS les textes de réponse DOIVENT être en français ou en anglais
"""
