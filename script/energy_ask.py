from fastapi import FastAPI, Request
from supabase import create_client
from datetime import datetime, date
import os
import uvicorn

app = FastAPI()

# Read from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    try:
        energy_level = int(text)
        assert 1 <= energy_level <= 10
    except (ValueError, AssertionError):
        return {"ok": False, "error": "Invalid energy level input."}

    today = date.today().isoformat()

    # Insert into Supabase
    result = supabase.table("daily_energy").upsert({
        "calendar_date": today,
        "energy_level": energy_level
    }).execute()

    # Confirm to user
    confirmation = f"✅ Got it! Logged energy level: {energy_level} for {today}"
    send_telegram_message(chat_id, confirmation)

    return {"ok": True}

def send_telegram_message(chat_id: int, text: str):
    import requests
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
