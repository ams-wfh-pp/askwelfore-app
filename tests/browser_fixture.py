"""Offline browser fixture only: replies are test strings, never real advice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
import uvicorn
from coach_web import Settings, create_coach_app
from kitchen_coach import KitchenCoach, CoachUnavailable

def generate(instructions, messages, tokens):
    if "simulate failure" in messages[-1]["content"]:
        raise CoachUnavailable()
    return "OFFLINE UI TEST ONLY.\nThe conversation and household context reached the coach. <script>window.injected=true</script>"

app = FastAPI()
app.mount("/coach", create_coach_app(Settings(
    access_code="offline-browser-test-only-code-123456",
    origin="http://127.0.0.1:8766", secure_cookie=False, ai_enabled=True,
    api_key="not-a-key", model="offline-fixture",
), KitchenCoach(generate)))
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8766, access_log=False)
