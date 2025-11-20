"""
Service d'envoi de messages WhatsApp via l'API Meta Cloud
"""
import httpx
from app.config import Config
from app.utils import setup_logger

logger = setup_logger(__name__)

BASE_URL = "https://graph.facebook.com"


async def send_text_message(to_number: str, message: str) -> bool:
    """
    Envoie un message texte via WhatsApp Cloud API
    
    Args:
        to_number: Numéro de téléphone (format: 229XXXXXXXX)
        message: Texte du message
        
    Returns:
        True si succès, False sinon
    """
    try:
        Config.validate()
        
        url = f"{BASE_URL}/{Config.API_VERSION}/{Config.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        logger.info(f"📤 Envoi message à {to_number}: {message[:50]}...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"✅ Message envoyé avec succès: ID={message_id}")
                return True
            else:
                logger.error(
                    f"❌ Échec envoi message: {response.status_code}\n"
                    f"Réponse: {response.text}"
                )
                return False
                
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi du message: {e}", exc_info=True)
        return False


async def send_image_message(
    to_number: str,
    image_url: str,
    caption: str = ""
) -> bool:
    """
    Envoie une image via WhatsApp Cloud API
    
    Args:
        to_number: Numéro de téléphone
        image_url: URL publique de l'image
        caption: Légende de l'image (optionnel)
        
    Returns:
        True si succès, False sinon
    """
    try:
        Config.validate()
        
        url = f"{BASE_URL}/{Config.API_VERSION}/{Config.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        logger.info(f"📤 Envoi image à {to_number}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info("✅ Image envoyée avec succès")
                return True
            else:
                logger.error(f"❌ Échec envoi image: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erreur envoi image: {e}")
        return False


async def send_template_message(
    to_number: str,
    template_name: str,
    language_code: str = "fr"
) -> bool:
    """
    Envoie un message template (pour notifications hors fenêtre 24h)
    
    Args:
        to_number: Numéro de téléphone
        template_name: Nom du template approuvé par Meta
        language_code: Code langue (fr, en, etc.)
        
    Returns:
        True si succès, False sinon
    """
    try:
        Config.validate()
        
        url = f"{BASE_URL}/{Config.API_VERSION}/{Config.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        logger.info(f"📤 Envoi template '{template_name}' à {to_number}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info("✅ Template envoyé avec succès")
                return True
            else:
                logger.error(f"❌ Échec envoi template: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Erreur envoi template: {e}")
        return False


async def mark_message_as_read(message_id: str) -> bool:
    """
    Marque un message comme lu
    
    Args:
        message_id: ID du message à marquer
        
    Returns:
        True si succès, False sinon
    """
    try:
        Config.validate()
        
        url = f"{BASE_URL}/{Config.API_VERSION}/{Config.PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.debug(f"Message {message_id} marqué comme lu")
                return True
            else:
                logger.warning(f"Échec marquage lu: {response.status_code}")
                return False
                
    except Exception as e:
        logger.warning(f"Erreur marquage lu: {e}")
        return False