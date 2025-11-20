# ai.py (optionnel)
import httpx
from app.config import Config

HF_URL_TEMPLATE = "https://api-inference.huggingface.co/models/{}"

async def ask_hf(prompt: str):
    if not Config.HF_API_KEY or not Config.HF_MODEL:
        return "AI non configurée."
    url = HF_URL_TEMPLATE.format(Config.HF_MODEL)
    headers = {"Authorization": f"Bearer {Config.HF_API_KEY}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            data = r.json()
            # format selon réponse : many models renvoient list[0]['generated_text']
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"]
            if isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            return str(data)
        else:
            print("HF error:", r.status_code, r.text)
            return "Erreur IA."
