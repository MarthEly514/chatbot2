# webhook.py
from fastapi import Request, Response
from app.config import Config
from app.sender import send_text_message
import json

async def verify_get(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == Config.VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Forbidden", status_code=403)


async def handle_post(data: dict):
    """
    data = payload envoyé par Meta (webhook)
    Voir la structure: entry -> changes -> value -> messages
    """
    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                # messages présents quand un user envoie un message
                messages = value.get("messages", [])
                if not messages:
                    continue
                for message in messages:
                    from_number = message.get("from")  # ex: "229XXXXXXXX"
                    text_obj = message.get("text", {})
                    text = text_obj.get("body", "")
                    # Ici: logique simple d'echo ou appeler AI
                    # Ex: si l'utilisateur écrit "ping" -> reply "pong"
                    if text.strip().lower() == "ping":
                        await send_text_message(from_number, "pong")
                    else:
                        # echo simple
                        await send_text_message(from_number, f"Reçu: {text}")
    except Exception as e:
        print("Webhook handling error:", e)
