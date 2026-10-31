import hashlib
import hmac
import json
import logging
import os

from fastapi import FastAPI, HTTPException, Request

app = FastAPI()
logger = logging.getLogger(__name__)
SUPPORTED_PULL_REQUEST_ACTIONS = {
    "opened",
    "reopened",
    "synchronize",
    "ready_for_review",
}


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

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from error

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be an object")

    event = request.headers.get("x-github-event")
    if event != "pull_request":
        logger.info("Ignoring unsupported GitHub webhook event=%s", event)
        return {"status": "ignored", "reason": "unsupported_event"}

    action = payload.get("action")
    repository = payload.get("repository")
    pull_request = payload.get("pull_request")
    if (
        action not in SUPPORTED_PULL_REQUEST_ACTIONS
        or not isinstance(repository, dict)
        or not repository.get("full_name")
        or not isinstance(pull_request, dict)
        or not pull_request.get("number")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid pull_request webhook payload",
        )

    logger.info(
        "GitHub webhook received delivery_id=%s event=%s action=%s repository=%s",
        request.headers.get("x-github-delivery"),
        event,
        action,
        repository["full_name"],
    )

    return {
        "status": "accepted",
        "event": event,
        "action": action,
    }
