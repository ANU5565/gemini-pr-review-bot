from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/")
async def home():
    return {
        "status": "online",
        "bot": "Gemini PR Review Bot",
        "message": "GitHub PR reviewer is running!"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()

    print("GitHub webhook received:")
    print(payload)

    return {
        "status": "received"
    }
