"""Endpoints de santé et monitoring"""
from fastapi import APIRouter
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Vérification de santé de l'API"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment
    }


@router.get("/readiness")
async def readiness_check():
    """Vérification de disponibilité"""
    # Ici on peut ajouter des vérifications de services externes
    return {"status": "ready"}
