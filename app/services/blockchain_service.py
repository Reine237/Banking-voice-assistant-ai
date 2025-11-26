"""Service d'intégration avec la blockchain Bafoka"""
import httpx
from typing import Dict, Any, Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class BlockchainService:
    """Service d'interaction avec l'API blockchain Bafoka"""
    
    def __init__(self):
        self.base_url = settings.bafoka_api_base_url
        self.api_key = settings.bafoka_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def execute_action(
        self,
        endpoint: str,
        method: str,
        parameters: Dict[str, Any]
    ) -> Dict:
        """
        Exécute une action sur la blockchain Bafoka
        
        Args:
            endpoint: Endpoint de l'API (ex: /api/transfer)
            method: Méthode HTTP (POST, GET)
            parameters: Paramètres de la requête
        
        Returns:
            Réponse de l'API Bafoka
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            logger.info(f"Appel API Bafoka: {method} {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "POST":
                    response = await client.post(
                        url,
                        json=parameters,
                        headers=self.headers
                    )
                elif method.upper() == "GET":
                    response = await client.get(
                        url,
                        params=parameters,
                        headers=self.headers
                    )
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                logger.success(f"Requête Bafoka réussie: {endpoint}")
                
                return {
                    "success": True,
                    "data": result,
                    "status_code": response.status_code
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP Bafoka: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Erreur API Bafoka: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'appel API Bafoka: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transfer(self, parameters: Dict[str, Any]) -> Dict:
        """Effectue un transfert"""
        return await self.execute_action("/api/transfer", "POST", parameters)
    
    async def get_balance(self, phone_number: str) -> Dict:
        """Consulte le solde"""
        return await self.execute_action(
            "/api/get-balance",
            "POST",
            {"phoneNumber": phone_number}
        )
    
    async def create_account(self, parameters: Dict[str, Any]) -> Dict:
        """Crée un nouveau compte"""
        return await self.execute_action("/api/account-creation", "POST", parameters)
    
    async def get_recipient_info(self, sender_phone: str, recipient_phone: str) -> Dict:
        """Récupère les infos d'un destinataire"""
        return await self.execute_action(
            "/api/recipient-info",
            "POST",
            {"senderPhone": sender_phone, "recipientPhone": recipient_phone}
        )
