import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Meta / WhatsApp Cloud API
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")               # Access token
    PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")   # phone_number_id fourni par Meta
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "verify_me")  # token pour vérifier webhook

    # Optionnel: AI (Hugging Face / OpenAI)
    HF_API_KEY = os.getenv("HF_API_KEY", "")
    HF_MODEL = os.getenv("HF_MODEL", "")

    # Sécurité / logs
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    @classmethod
    def validate(cls):
        missing = []
        if not cls.WHATSAPP_TOKEN:
            missing.append("WHATSAPP_TOKEN")
        if not cls.PHONE_NUMBER_ID:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if missing:
            raise RuntimeError("Missing env vars: " + ", ".join(missing))
