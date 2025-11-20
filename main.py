from fastapi import FastAPI, Request
from app.webhook import verify_get, handle_post

app = FastAPI()

@app.get("/")
async def root():
    return {"ok": True, "service": "WhatsApp Meta Bot"}

# Endpoint pour la vérification webhook (GET) et pour recevoir events (POST)
@app.get("/webhook")
async def webhook_verify(request: Request):
    return await verify_get(request)

@app.post("/webhook")
async def webhook_receive(request: Request):
    data = await request.json()
    await handle_post(data)
    return {"status": "received"}
