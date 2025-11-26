"""Validateurs de données"""
import re
from typing import Dict, List, Any


class Validator:
    """Validation des données métier"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Valide un numéro de téléphone camerounais"""
        # Format: 6XXXXXXXX (9 chiffres commençant par 6)
        pattern = r'^6\d{8}$'
        return bool(re.match(pattern, phone.replace("+237", "").replace(" ", "")))
    
    @staticmethod
    def validate_amount(amount: str) -> bool:
        """Valide un montant"""
        try:
            value = float(amount)
            return value > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_age(age: Any) -> bool:
        """Valide un âge"""
        try:
            age_int = int(age)
            return 18 <= age_int <= 120
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_sex(sex: str) -> bool:
        """Valide le sexe"""
        return sex.upper() in ["M", "F", "MALE", "FEMALE", "HOMME", "FEMME"]
    
    @staticmethod
    def check_missing_params(
        required_params: List[str],
        provided_params: Dict[str, Any]
    ) -> List[str]:
        """Vérifie les paramètres manquants"""
        return [
            param for param in required_params
            if param not in provided_params or not provided_params[param]
        ]
