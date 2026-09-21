"""Local-only review launcher. No paid requests or legacy app imports."""
import os
import secrets
from fastapi import FastAPI
from coach_web import Settings, create_coach_app

# A fresh code per process; never written to disk or committed.
code = secrets.token_urlsafe(32)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/coach", create_coach_app(Settings(
    access_code=code, origin="http://127.0.0.1:8765", secure_cookie=False,
    ai_enabled=False,
)))

if __name__ == "__main__":
    import uvicorn
    print("LOCAL REVIEW ONLY — AI replies are disabled.", flush=True)
    print("Open http://127.0.0.1:8765/coach/", flush=True)
    print("Temporary collaborator code: " + code, flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8765, access_log=False)
