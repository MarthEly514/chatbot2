"""
Configuration du bot de détection de fake news et deepfakes
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Meta / WhatsApp Cloud API
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "verify_me_fakenews_2025")
    
    # Version API Meta
    API_VERSION = os.getenv("API_VERSION", "v21.0")
    
    # Hugging Face Models
    # Modèle pour la détection de fake news (texte)
    FAKE_NEWS_MODEL = os.getenv(
        "FAKE_NEWS_MODEL",
        "hamzab/roberta-fake-news-classification"  # Modèle léger et performant
    )
    
    # Modèle pour la détection de deepfakes (images)
    DEEPFAKE_IMAGE_MODEL = os.getenv(
        "DEEPFAKE_IMAGE_MODEL",
        "dima806/deepfake_vs_real_image_detection"
    )
    
    # API Hugging Face (optionnel, pour Inference API)
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    
    # Serveur
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Seuils de détection
    FAKE_NEWS_THRESHOLD = float(os.getenv("FAKE_NEWS_THRESHOLD", "0.6"))
    DEEPFAKE_THRESHOLD = float(os.getenv("DEEPFAKE_THRESHOLD", "0.7"))
    
    # Taille maximale des médias (en MB)
    MAX_MEDIA_SIZE_MB = int(os.getenv("MAX_MEDIA_SIZE_MB", "16"))
    
    # Dossier temporaire pour les médias
    TEMP_MEDIA_DIR = os.getenv("TEMP_MEDIA_DIR", "/tmp/whatsapp_media")
    
    # Timeout pour les analyses
    ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", "30"))
    
    # Messages du bot
    WELCOME_MESSAGE = """👋 Bienvenue sur le Bot de Vérification !

🔍 Je peux vous aider à analyser :
• 📝 Textes (fake news)
• 🖼️ Images (deepfakes)
• 🎥 Vidéos (manipulations)
• 🎤 Audios (voix synthétiques)

Envoyez-moi simplement le contenu à vérifier !

⚠️ Note : Cette analyse automatique n'est pas infaillible. Utilisez votre jugement critique !"""

    HELP_MESSAGE = """ℹ️ Comment utiliser ce bot :

1️⃣ Envoyez un texte à vérifier
   → Je l'analyserai pour détecter des fake news

2️⃣ Envoyez une image, vidéo ou audio
   → Je rechercherai des signes de manipulation

3️⃣ Tapez 'info' pour plus de détails
   
🔒 Vos données sont analysées localement et ne sont pas conservées."""

    INFO_MESSAGE = """🔬 Détails Techniques :

**Analyse de Texte :**
• Modèle : RoBERTa finetuné
• Détecte : Désinformation, clickbait
• Précision : ~85%

**Analyse Média :**
• Images : Détection artefacts GAN
• Vidéos : Analyse frame par frame
• Audio : Détection voix synthétique

⚠️ **Limitations :**
• Nouveaux deepfakes sophistiqués
• Contenus satiriques mal classés
• Dépend de la qualité du média

💡 Toujours vérifier les sources !"""

    @classmethod
    def validate(cls):
        """Valide que les variables essentielles sont présentes"""
        missing = []
        if not cls.WHATSAPP_TOKEN:
            missing.append("WHATSAPP_TOKEN")
        if not cls.PHONE_NUMBER_ID:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if missing:
            raise RuntimeError(
                f"❌ Variables d'environnement manquantes : {', '.join(missing)}\n"
                "Créez un fichier .env avec ces variables."
            )
    
    @classmethod
    def create_temp_dir(cls):
        """Crée le dossier temporaire pour les médias"""
        os.makedirs(cls.TEMP_MEDIA_DIR, exist_ok=True)