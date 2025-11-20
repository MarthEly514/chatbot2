# sender.py
import httpx
import os
from app.config import Config

BASE_URL = "https://graph.facebook.com"

async def send_text_message(to_number: str, message: str):
    """
    to_number: string without 'whatsapp:' prefix, e.g. '229XXXXXXXX'
    message: text body
    """
    Config.validate()
    url = f"{BASE_URL}/v20.0/{Config.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            # Log détaillé pour debug
            print("Send message failed:", resp.status_code, resp.text)
        return resp.status_code, resp.text
