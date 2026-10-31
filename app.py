import hashlib
import hmac
import os

from fastapi import FastAPI, HTTPException, Request

app = FastAPI()


@app.get("/")
async def root():
    return {
        "status": "online",
        "bot": "Gemini PR Review Bot"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/api/webhook")
async def github_webhook(request: Request):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret is not configured",
        )

    body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not signature or not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    print("GitHub webhook received")
    print(payload)

    return {
        "status": "received"
    }
