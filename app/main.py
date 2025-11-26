"""Point d'entrée principal de l'application FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
from pathlib import Path

from app.config import get_settings
from app.routes import voice_router, health_router
from app.middleware.error_handler import global_exception_handler

# Configuration
settings = get_settings()

# Créer les dossiers nécessaires
Path("data/audio").mkdir(parents=True, exist_ok=True)
Path("data/sessions").mkdir(parents=True, exist_ok=True)

# Configuration du logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level=settings.log_level
)

# Initialisation FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    🎙️ **API d'Assistant Vocal Bancaire Bafoka**
    
    Cette API fournit un pipeline complet pour traiter des messages vocaux WhatsApp
    et exécuter des actions bancaires sur la blockchain Bafoka.
    
    ## Fonctionnalités principales
    
    * 🗣️ **Speech-to-Text**: Transcription audio avec Whisper
    * 🧠 **NLU**: Analyse du langage naturel avec Groq
    * 🔗 **Blockchain**: Intégration avec l'API Bafoka
    * 💬 **Conversations**: Gestion du contexte utilisateur
    * 🔄 **Pipeline complet**: Traitement end-to-end automatisé
    
    ## Workflow typique
    
    1. WhatsApp envoie un audio vocal
    2. `/voice/process` transcrit, analyse et exécute
    3. Si des infos manquent, le bot les demande
    4. Les données sont sauvegardées dans la session
    5. Quand tout est complet, l'action est exécutée sur Bafoka
    6. Réponse renvoyée à l'utilisateur
    
    ## Intégration WhatsApp
    
    Utilisez le webhook `/voice/process` pour traiter les messages vocaux.
    """,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire d'erreurs
app.add_exception_handler(Exception, global_exception_handler)

# Routes
app.include_router(health_router)
app.include_router(voice_router)


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage"""
    logger.info(f"🚀 Démarrage de {settings.app_name} v{settings.version}")
    logger.info(f"📝 Environment: {settings.environment}")
    logger.info(f"📚 Documentation: http://{settings.host}:{settings.port}/docs")

    # Check API keys configuration
    api_status = settings.validate_api_keys()
    logger.info("📋 Configuration des clés API:")
    for key, configured in api_status.items():
        status = "✅ Configurée" if configured else "⚠️  Manquante"
        logger.info(f"  {key}: {status}")

    if not all(api_status.values()):
        logger.warning("⚠️  Certaines clés API sont manquantes!")
        logger.warning("   Créez un fichier .env avec les clés requises pour activer toutes les fonctionnalités.")
        logger.warning("   Voir .env.example pour référence.")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt"""
    logger.info(f"🛑 Arrêt de {settings.app_name}")


@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
