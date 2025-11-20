"""
Gestionnaires de webhooks Meta pour WhatsApp
"""
from fastapi import Request, Response
from app.config import Config
from app.message_processor import MessageProcessor
from app.utils import setup_logger

logger = setup_logger(__name__)

# Instance globale du processeur de messages
message_processor = MessageProcessor()


async def verify_get(request: Request):
    """
    Vérifie le webhook lors de la configuration dans Meta
    
    Args:
        request: Requête FastAPI
        
    Returns:
        Response avec le challenge ou 403
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info(f"Vérification webhook - Mode: {mode}, Token: {token[:10]}...")
    
    if mode == "subscribe" and token == Config.VERIFY_TOKEN:
        logger.info("✅ Webhook vérifié avec succès!")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning("❌ Échec vérification webhook - Token invalide")
    return Response(content="Forbidden", status_code=403)


async def handle_post(data: dict):
    """
    Traite les événements entrants du webhook
    
    Args:
        data: Payload JSON envoyé par Meta
    """
    try:
        # Log des données reçues (debug)
        logger.debug(f"Webhook reçu: {data}")
        
        # Structure du webhook Meta:
        # {
        #   "object": "whatsapp_business_account",
        #   "entry": [{
        #     "id": "...",
        #     "changes": [{
        #       "value": {
        #         "messaging_product": "whatsapp",
        #         "metadata": {...},
        #         "contacts": [...],
        #         "messages": [...]
        #       },
        #       "field": "messages"
        #     }]
        #   }]
        # }
        
        entries = data.get("entry", [])
        
        if not entries:
            logger.warning("Webhook sans entries")
            return
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # Traiter les messages
                messages = value.get("messages", [])
                for message in messages:
                    await process_message(message, value)
                
                # Traiter les statuts (optionnel)
                statuses = value.get("statuses", [])
                for status in statuses:
                    await process_status(status)
                    
    except Exception as e:
        logger.error(f"❌ Erreur traitement webhook: {e}", exc_info=True)


async def process_message(message: dict, value: dict):
    """
    Traite un message individuel
    
    Args:
        message: Dict du message
        value: Dict value du webhook (contient contacts, metadata, etc.)
    """
    try:
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        message_type = message.get("type")
        
        logger.info(
            f"📨 Message reçu: ID={message_id}, "
            f"De={from_number}, Type={message_type}"
        )
        
        # Extraire le nom du contact si disponible
        contacts = value.get("contacts", [])
        profile_name = "Utilisateur"
        if contacts:
            profile_name = contacts[0].get("profile", {}).get("name", "Utilisateur")
        
        # Construire l'objet message complet
        message_data = {
            "id": message_id,
            "from": from_number,
            "timestamp": timestamp,
            "type": message_type,
            "profile_name": profile_name
        }
        
        # Ajouter le contenu selon le type
        if message_type == "text":
            message_data["text"] = message.get("text", {})
        
        elif message_type == "image":
            message_data["image"] = message.get("image", {})
        
        elif message_type == "video":
            message_data["video"] = message.get("video", {})
        
        elif message_type == "audio":
            message_data["audio"] = message.get("audio", {})
        
        elif message_type == "document":
            message_data["document"] = message.get("document", {})
        
        elif message_type == "interactive":
            # Réponses aux boutons interactifs
            message_data["interactive"] = message.get("interactive", {})
        
        elif message_type == "button":
            # Ancienne façon de gérer les boutons
            message_data["button"] = message.get("button", {})
        
        # Traiter le message via le processeur
        await message_processor.process_incoming_message(message_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement message: {e}", exc_info=True)


async def process_status(status: dict):
    """
    Traite une mise à jour de statut (message envoyé, délivré, lu, etc.)
    
    Args:
        status: Dict du statut
    """
    try:
        status_type = status.get("status")
        message_id = status.get("id")
        recipient_id = status.get("recipient_id")
        
        logger.debug(
            f"📊 Statut reçu: Type={status_type}, "
            f"MessageID={message_id}, To={recipient_id}"
        )
        
        # On peut logger ou stocker ces infos si nécessaire
        # Statuts possibles: sent, delivered, read, failed
        
        if status_type == "failed":
            errors = status.get("errors", [])
            logger.warning(f"⚠️ Message {message_id} échoué: {errors}")
        
    except Exception as e:
        logger.error(f"Erreur traitement statut: {e}")