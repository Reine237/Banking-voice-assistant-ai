"""Utilitaires de nettoyage de texte"""
import re
import spacy
from spellchecker import SpellChecker
from typing import Set
from loguru import logger


class TextCleaner:
    """Nettoyage et normalisation du texte transcrit"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            logger.warning("Modèle spaCy non trouvé, téléchargement...")
            import os
            os.system("python -m spacy download fr_core_news_sm")
            self.nlp = spacy.load("fr_core_news_sm")
        
        self.spell_checker = SpellChecker(language='fr')
        self.banking_terms = self._load_banking_terms()
    
    def clean_transcription(self, text: str) -> str:
        """Nettoyage complet du texte transcrit"""
        # 1. Correction orthographique contextuelle
        text = self._contextual_spell_correction(text)
        
        # 2. Normalisation des nombres
        text = self._normalize_numbers(text)
        
        # 3. Suppression des hésitations
        text = self._remove_hesitations(text)
        
        # 4. Normalisation des entités bancaires
        text = self._normalize_banking_entities(text)
        
        return text.strip()
    
    def _contextual_spell_correction(self, text: str) -> str:
        """Correction orthographique avec priorité aux termes bancaires"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            if word.lower() not in self.banking_terms and self.spell_checker.unknown([word]):
                candidates = self.spell_checker.candidates(word)
                if candidates:
                    best = max(candidates, key=lambda x: self._banking_priority(x))
                    corrected_words.append(best)
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        return " ".join(corrected_words)
    
    def _banking_priority(self, word: str) -> int:
        """Priorité aux termes bancaires"""
        return 2 if word.lower() in self.banking_terms else 1
    
    def _normalize_numbers(self, text: str) -> str:
        """Normalisation des nombres en lettres vers chiffres"""
        number_words = {
            'un': '1', 'deux': '2', 'trois': '3', 'quatre': '4', 'cinq': '5',
            'six': '6', 'sept': '7', 'huit': '8', 'neuf': '9', 'dix': '10',
            'vingt': '20', 'trente': '30', 'quarante': '40', 'cinquante': '50',
            'cent': '100', 'mille': '1000', 'million': '1000000'
        }
        
        for word, number in number_words.items():
            text = re.sub(rf'\b{word}\b', number, text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_hesitations(self, text: str) -> str:
        """Suppression des hésitations"""
        hesitations = {'euh', 'ah', 'hem', 'alors', 'donc', 'voilà', 'bon'}
        words = [w for w in text.split() if w.lower() not in hesitations]
        return " ".join(words)
    
    def _normalize_banking_entities(self, text: str) -> str:
        """Normalisation des entités bancaires"""
        # Devises
        text = re.sub(r'\b(euros?|eur)\b', 'EUR', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(francs?|fcfa|cfa)\b', 'FCFA', text, flags=re.IGNORECASE)
        
        return text
    
    def _load_banking_terms(self) -> Set[str]:
        """Charge les termes bancaires"""
        return {
            "virement", "transfert", "solde", "compte", "carte", "banque",
            "payer", "facture", "bénéficiaire", "rib", "iban", "plafond",
            "retrait", "dépôt", "prélèvement", "agios", "découvert",
            "créer", "ouvrir", "consulter", "envoyer", "recevoir"
        }
