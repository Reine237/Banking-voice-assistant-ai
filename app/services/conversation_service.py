"""Service de gestion des conversations et du contexte utilisateur"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import json
from pathlib import Path


class ConversationService:
    """Gestion du contexte conversationnel et de la mémoire"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=30)
        self.sessions_dir = Path("data/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        """
        Récupère la session d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Données de session ou None
        """
        # Vérifier en mémoire
        if user_id in self.sessions:
            session = self.sessions[user_id]
            
            # Vérifier l'expiration
            if self._is_session_expired(session):
                logger.info(f"Session expirée pour {user_id}")
                self.clear_session(user_id)
                return None
            
            return session
        
        # Essayer de charger depuis le fichier
        return self._load_session_from_file(user_id)
    
    def create_or_update_session(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict:
        """
        Crée ou met à jour une session utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            data: Nouvelles données à ajouter
        
        Returns:
            Session mise à jour
        """
        session = self.get_session(user_id) or self._create_new_session(user_id)
        
        # Mettre à jour les données
        session["last_activity"] = datetime.now().isoformat()
        session["data"].update(data)
        session["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        # Sauvegarder en mémoire et sur disque
        self.sessions[user_id] = session
        self._save_session_to_file(user_id, session)
        
        logger.info(f"Session mise à jour pour {user_id}")
        
        return session
    
    def add_pending_info(
        self,
        user_id: str,
        intent: str,
        collected_params: Dict,
        missing_params: list
    ):
        """
        Enregistre les informations en attente de complétion
        
        Args:
            user_id: ID de l'utilisateur
            intent: Intention détectée
            collected_params: Paramètres déjà collectés
            missing_params: Paramètres manquants
        """
        session_data = {
            "pending_info": {
                "intent": intent,
                "collected_params": collected_params,
                "missing_params": missing_params,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        self.create_or_update_session(user_id, session_data)
    
    def get_pending_info(self, user_id: str) -> Optional[Dict]:
        """Récupère les informations en attente"""
        session = self.get_session(user_id)
        if session and "pending_info" in session.get("data", {}):
            return session["data"]["pending_info"]
        return None
    
    def clear_pending_info(self, user_id: str):
        """Efface les informations en attente"""
        session = self.get_session(user_id)
        if session and "pending_info" in session.get("data", {}):
            del session["data"]["pending_info"]
            self._save_session_to_file(user_id, session)
    
    def clear_session(self, user_id: str):
        """Supprime une session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
        
        session_file = self.sessions_dir / f"{user_id}.json"
        if session_file.exists():
            session_file.unlink()
        
        logger.info(f"Session supprimée pour {user_id}")
    
    def _create_new_session(self, user_id: str) -> Dict:
        """Crée une nouvelle session"""
        return {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "data": {},
            "conversation_history": []
        }
    
    def _is_session_expired(self, session: Dict) -> bool:
        """Vérifie si une session est expirée"""
        last_activity = datetime.fromisoformat(session["last_activity"])
        return datetime.now() - last_activity > self.session_timeout
    
    def _save_session_to_file(self, user_id: str, session: Dict):
        """Sauvegarde une session sur disque"""
        try:
            session_file = self.sessions_dir / f"{user_id}.json"
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la session: {e}")
    
    def _load_session_from_file(self, user_id: str) -> Optional[Dict]:
        """Charge une session depuis le disque"""
        try:
            session_file = self.sessions_dir / f"{user_id}.json"
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    session = json.load(f)
                
                if not self._is_session_expired(session):
                    self.sessions[user_id] = session
                    return session
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la session: {e}")
        
        return None
