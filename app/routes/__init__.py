"""Routes API de l'application"""
from .voice import router as voice_router
from .health import router as health_router

__all__ = ["voice_router", "health_router"]
