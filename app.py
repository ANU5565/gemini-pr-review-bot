from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Gemini PR Review Bot is working!"
    }
