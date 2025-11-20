"""
Fonctions utilitaires pour le bot
"""
import logging
import os
import sys
from datetime import datetime


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Configure et retourne un logger
    
    Args:
        name: Nom du logger
        
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def format_confidence(score: float) -> str:
    """
    Formate un score de confiance en pourcentage
    
    Args:
        score: Score entre 0 et 1
        
    Returns:
        String formaté (ex: "85%")
    """
    return f"{int(score * 100)}%"


def get_confidence_emoji(score: float) -> str:
    """
    Retourne un emoji selon le score de confiance
    
    Args:
        score: Score entre 0 et 1
        
    Returns:
        Emoji approprié
    """
    if score >= 0.8:
        return "✅"
    elif score >= 0.6:
        return "⚠️"
    elif score >= 0.4:
        return "⚡"
    else:
        return "❌"


def format_analysis_result(
    content_type: str,
    is_fake: bool,
    confidence: float,
    details: str = ""
) -> str:
    """
    Formate le résultat d'analyse pour l'utilisateur
    
    Args:
        content_type: Type de contenu (texte, image, vidéo, audio)
        is_fake: True si détecté comme fake
        confidence: Score de confiance
        details: Détails supplémentaires
        
    Returns:
        Message formaté
    """
    emoji = "🚨" if is_fake else "✅"
    confidence_str = format_confidence(confidence)
    confidence_emoji = get_confidence_emoji(confidence)
    
    # Verdict
    if is_fake:
        verdict = "CONTENU SUSPECT"
        recommendation = (
            "⚠️ Ce contenu présente des signes de manipulation ou de désinformation.\n\n"
            "**Recommandations :**\n"
            "• Vérifiez les sources originales\n"
            "• Consultez des fact-checkers reconnus\n"
            "• Soyez prudent avant de partager"
        )
    else:
        verdict = "CONTENU PROBABLEMENT AUTHENTIQUE"
        recommendation = (
            "✅ Ce contenu semble authentique selon notre analyse.\n\n"
            "**Rappel :**\n"
            "• Restez vigilant même pour du contenu authentique\n"
            "• Le contexte peut changer la signification\n"
            "• Vérifiez toujours les sources importantes"
        )
    
    # Construction du message
    message = f"""{emoji} **RÉSULTAT D'ANALYSE**

📊 **Type :** {content_type.title()}
🎯 **Verdict :** {verdict}
📈 **Confiance :** {confidence_emoji} {confidence_str}

{recommendation}"""
    
    if details:
        message += f"\n\n🔍 **Détails :**\n{details}"
    
    message += (
        "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ Cette analyse automatique n'est pas infaillible.\n"
        "Utilisez toujours votre jugement critique !"
    )
    
    return message


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les problèmes
    
    Args:
        filename: Nom de fichier original
        
    Returns:
        Nom de fichier sécurisé
    """
    # Supprimer les caractères dangereux
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    filename = "".join(c for c in filename if c in safe_chars)
    
    # Limiter la longueur
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:90] + ext
    
    # Ajouter timestamp si vide
    if not filename:
        filename = f"media_{int(datetime.now().timestamp())}"
    
    return filename


def get_media_type_from_mime(mime_type: str) -> str:
    """
    Détermine le type de média à partir du MIME type
    
    Args:
        mime_type: MIME type (ex: "image/jpeg")
        
    Returns:
        Type simplifié (image, video, audio, document)
    """
    mime_type = mime_type.lower()
    
    if mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    elif mime_type in ["application/pdf", "application/msword"]:
        return "document"
    else:
        return "unknown"


def estimate_file_size_mb(file_path: str) -> float:
    """
    Estime la taille d'un fichier en MB
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        Taille en MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except:
        return 0.0