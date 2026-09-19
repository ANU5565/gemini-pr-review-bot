from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/api")
async def home():
    return {
        "status": "online",
        "bot": "Gemini PR Review Bot"
    }


@app.post("/api/webhook")
async def github_webhook(request: Request):
    payload = await request.json()

    print("GitHub webhook received:")
    print(payload)

    return {
        "status": "received"
    }