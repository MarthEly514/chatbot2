"""
Point d'entrée principal de l'application
Bot WhatsApp de détection de fake news et deepfakes
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.webhook import verify_get, handle_post
from app.config import Config
from app.utils import setup_logger
import sys

# Configuration du logger
logger = setup_logger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="WhatsApp Fake News & Deepfake Detector",
    description="Bot de détection de fake news et deepfakes via WhatsApp",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'application"""
    logger.info("=" * 60)
    logger.info("🚀 Démarrage du Bot de Détection Fake News & Deepfakes")
    logger.info("=" * 60)
    
    try:
        # Valider la configuration
        Config.validate()
        logger.info("✅ Configuration validée")
        
        # Créer le dossier temporaire
        Config.create_temp_dir()
        logger.info("✅ Dossier temporaire créé")
        
        # Infos de configuration
        logger.info(f"📱 Phone Number ID: {Config.PHONE_NUMBER_ID}")
        logger.info(f"🔧 API Version: {Config.API_VERSION}")
        logger.info(f"🤖 Modèle Fake News: {Config.FAKE_NEWS_MODEL}")
        logger.info(f"🎭 Modèle Deepfake: {Config.DEEPFAKE_IMAGE_MODEL}")
        logger.info(f"🌐 Host: {Config.HOST}:{Config.PORT}")
        logger.info("=" * 60)
        logger.info("✅ Application prête à recevoir des webhooks")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        logger.error("Vérifiez votre fichier .env et vos variables d'environnement")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_event():
    """Événement à l'arrêt de l'application"""
    logger.info("🛑 Arrêt du bot...")
    
    # Nettoyage des fichiers temporaires
    try:
        from app.media_handler import MediaHandler
        handler = MediaHandler()
        handler.cleanup_old_files(max_age_hours=0)  # Tout nettoyer
        logger.info("✅ Fichiers temporaires nettoyés")
    except Exception as e:
        logger.warning(f"⚠️ Erreur nettoyage: {e}")
    
    logger.info("👋 Bot arrêté proprement")


@app.get("/")
async def root():
    """
    Route racine - Informations sur le service
    """
    return {
        "ok": True,
        "service": "WhatsApp Fake News & Deepfake Detector",
        "version": "1.0.0",
        "status": "running",
        "capabilities": [
            "Détection de fake news (texte)",
            "Détection de deepfakes (images)",
            "Analyse de vidéos",
            "Analyse d'audios"
        ],
        "endpoints": {
            "webhook_verify": "GET /webhook",
            "webhook_receive": "POST /webhook",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint pour Railway et monitoring
    """
    try:
        # Vérifier que la configuration est OK
        Config.validate()
        
        # Vérifier que les dossiers existent
        import os
        temp_dir_exists = os.path.exists(Config.TEMP_MEDIA_DIR)
        
        return {
            "status": "healthy",
            "config": "valid",
            "temp_dir": "ok" if temp_dir_exists else "missing",
            "models": {
                "fake_news": Config.FAKE_NEWS_MODEL,
                "deepfake": Config.DEEPFAKE_IMAGE_MODEL
            }
        }
    except Exception as e:
        logger.error(f"Health check échoué: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/webhook")
async def webhook_verify(request: Request):
    """
    Endpoint de vérification du webhook (GET)
    Appelé par Meta lors de la configuration du webhook
    """
    return await verify_get(request)


@app.post("/webhook")
async def webhook_receive(request: Request):
    """
    Endpoint de réception des événements (POST)
    Appelé par Meta quand un message arrive
    """
    try:
        data = await request.json()
        await handle_post(data)
        
        # Toujours retourner 200 pour que Meta ne réessaie pas
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook: {e}", exc_info=True)
        # Retourner 200 même en cas d'erreur pour éviter les retry
        return {"status": "error", "message": str(e)}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Gestionnaire d'erreur 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Route non trouvée",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Gestionnaire d'erreur 500"""
    logger.error(f"Erreur serveur: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "message": "Une erreur s'est produite. Veuillez réessayer."
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Lancer le serveur
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    )