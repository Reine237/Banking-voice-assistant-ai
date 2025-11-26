"""Gestionnaire d'erreurs global"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from datetime import datetime


async def global_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Erreur non gérée: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Erreur interne du serveur",
            "details": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
