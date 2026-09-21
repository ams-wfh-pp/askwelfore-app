"""Isolated collaborator sub-application. Single process, ephemeral sessions."""
import asyncio
import copy
import hmac
import os
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from kitchen_coach import KitchenCoach, ContextFull, OpenAIResponses
from kitchen_context import KitchenContext

ROOT = Path(__file__).parent
COOKIE = "askwelfore_coach"
FIELDS = {
    "household": ("Who is sharing the meal?", 500),
    "culture": ("Cultural and flavor preferences", 600),
    "restrictions": ("Allergies and dietary restrictions (or none)", 800),
    "guidance": ("Nutrition guidance or goal", 1200),
    "source": ("Where did this guidance come from?", 400),
    "ingredients": ("Available ingredients and familiar foods", 800),
    "constraints": ("Time, equipment, budget and cooking confidence", 800),
}


def _output_budget(value):
    try:
        return int(value)
    except ValueError:
        return 0  # Invalid configuration fails closed, not a startup traceback.


@dataclass(frozen=True)
class Settings:
    access_code: str = ""
    origin: str = ""
    secure_cookie: bool = True
    ai_enabled: bool = False
    api_key: str = ""
    model: str = ""
    reasoning_effort: str = ""
    max_output_tokens: int = 700
    ttl: int = 14400
    max_calls: int = 100

    @classmethod
    def from_env(cls):
        return cls(
            access_code=os.getenv("COACH_ACCESS_CODE", ""),
            origin=os.getenv("COACH_ORIGIN", "").rstrip("/"),
            secure_cookie=os.getenv("COACH_LOCAL_HTTP", "") != "1",
            ai_enabled=os.getenv("COACH_AI_ENABLED", "") == "1",
            api_key=os.getenv("COACH_OPENAI_API_KEY", ""),
            model=os.getenv("COACH_MODEL", ""),
            reasoning_effort=os.getenv("COACH_REASONING_EFFORT", ""),
            max_output_tokens=_output_budget(os.getenv("COACH_MAX_OUTPUT_TOKENS", "700")),
        )

    def valid(self):
        try:
            url = urlsplit(self.origin)
            local = url.hostname in ("localhost", "127.0.0.1", "::1")
            return (128 <= self.max_output_tokens <= 2048
                    and self.reasoning_effort in ('', 'minimal', 'low', 'medium', 'high')
                    and 32 <= len(self.access_code) <= 256 and bool(url.netloc)
                    and url.path in ("", "/") and not url.username and not url.password
                    and not url.query and not url.fragment
                    and ((url.scheme == "https" and self.secure_cookie)
                         or (url.scheme == "http" and local and not self.secure_cookie)))
        except ValueError:
            return False


@dataclass
class Session:
    expires: float
    csrf: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    profile: dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    kitchen: KitchenContext = field(default_factory=KitchenContext)
    calls: int = 0
    last_call: float = -100
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    expiry_handle: object = None


class Boundary:
    """Apply protections to the coach only, never to the legacy app."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        extra = [(b"cache-control", b"no-store"), (b"referrer-policy", b"no-referrer"),
                 (b"x-content-type-options", b"nosniff"), (b"x-frame-options", b"DENY"),
                 (b"permissions-policy", b"microphone=(), camera=()"),
                 (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'")]
        started = False

        async def safe_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                message["headers"] = list(message.get("headers", [])) + extra
            await send(message)

        body = bytearray()
        if scope["method"] == "POST":
            while True:
                part = await receive()
                if part["type"] == "http.disconnect":
                    return
                body.extend(part.get("body", b""))
                if len(body) > 16000:
                    response = JSONResponse({"error": "Please shorten your message."}, status_code=413)
                    return await response(scope, receive, safe_send)
                if not part.get("more_body"):
                    break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        try:
            await self.app(scope, replay if scope["method"] == "POST" else receive, safe_send)
        except Exception:
            if not started:
                response = JSONResponse({"error": "The coach is unavailable. Please try again."}, status_code=503)
                await response(scope, receive, safe_send)
            # Do not leak exceptions to the legacy global exception logger.


def create_coach_app(settings=None, coach=None, clock=time.monotonic):
    settings = settings or Settings.from_env()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(Boundary)
    app.mount("/assets", StaticFiles(directory=str(ROOT / "coach_assets")), name="coach_assets")
    templates = Jinja2Templates(directory=str(ROOT / "templates"))
    sessions, attempts, calls = {}, deque(), deque()
    capacity = asyncio.Semaphore(2)
    configured = settings.valid()
    ready = bool(settings.ai_enabled and settings.api_key and settings.model)
    service = coach or KitchenCoach(
        OpenAIResponses(settings.api_key, settings.model, settings.reasoning_effort),
        max_output_tokens=settings.max_output_tokens if configured else 700)
    app.state.sessions = sessions

    def error(message, status=400):
        return JSONResponse({"error": message}, status_code=status)

    def discard(token):
        session = sessions.pop(token, None)
        if session:
            session.expires = 0
            session.profile.clear()
            session.history.clear()
            session.kitchen.clear()
            if session.expiry_handle:
                session.expiry_handle.cancel()

    def active(request):
        now = clock()
        for key in list(sessions):
            if sessions[key].expires <= now:
                discard(key)
        return sessions.get(request.cookies.get(COOKIE, ""))

    def trusted(request):
        return request.headers.get("origin") == settings.origin

    def authorized(request):
        session = active(request)
        if not configured or not session or not trusted(request):
            return None
        if not hmac.compare_digest(request.headers.get("x-coach-csrf", ""), session.csrf):
            return None
        return session

    async def data(request):
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return None
        try:
            value = await request.json()
            return value if isinstance(value, dict) else None
        except (ValueError, UnicodeError):
            return None

    @app.get("/", response_class=HTMLResponse)
    async def page(request: Request):
        if not configured:
            return HTMLResponse("<h1>Kitchen Coach testing is not enabled.</h1>", status_code=503)
        session = active(request)
        return templates.TemplateResponse(request=request, name="coach.html", context={
            "signed_in": bool(session), "csrf": session.csrf if session else "",
            "ready": ready, "fields": FIELDS,
        })

    @app.post("/login")
    async def login(request: Request):
        if not configured or not trusted(request):
            return error("Collaborator access is unavailable.", 403)
        now = clock()
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= 10:
            return error("Too many sign-in attempts. Please wait one minute.", 429)
        attempts.append(now)
        value = await data(request)
        code = value.get("code") if value else None
        if not isinstance(code, str) or len(code) > 256 or not hmac.compare_digest(
                code.encode(), settings.access_code.encode()):
            return error("That access code was not accepted.", 401)
        active(request)
        discard(request.cookies.get(COOKIE, ""))
        if len(sessions) >= 40:
            return error("Testing is busy. Please try again later.", 429)
        token = secrets.token_urlsafe(32)
        sessions[token] = Session(expires=now + settings.ttl)
        sessions[token].expiry_handle = asyncio.get_running_loop().call_later(
            settings.ttl, discard, token)
        result = JSONResponse({"ok": True})
        result.set_cookie(COOKIE, token, max_age=settings.ttl, path="/coach",
                          httponly=True, secure=settings.secure_cookie, samesite="strict")
        return result

    @app.get("/state")
    async def state(request: Request):
        session = active(request)
        if not configured or not session:
            return error("Your session ended. Please sign in again.", 401)
        return {"profile": session.profile, "history": session.history, "kitchen_context": session.kitchen.summary(), "ready": ready}

    @app.post("/message")
    async def message(request: Request):
        session = authorized(request)
        if not session:
            return error("Your access expired or could not be verified. Reload and sign in again.", 401)
        value = await data(request)
        if not value:
            return error("Please enter your cooking question.")
        text = value.get("message")
        if not isinstance(text, str) or not text.strip() or len(text) > 1600:
            return error("Enter a cooking question of 1–1,600 characters.")
        raw = value.get("profile")
        if not isinstance(raw, dict) or set(raw) - set(FIELDS):
            return error("Please check your household context.")
        profile = {}
        for key, (_, limit) in FIELDS.items():
            item = raw.get(key, "")
            if not isinstance(item, str) or len(item) > limit:
                return error("Please shorten your context fields.")
            profile[key] = item.strip()
        if not profile["restrictions"] or not profile["guidance"]:
            return error("Enter your guidance or goal, and allergies/restrictions (or none).")
        if session.lock.locked():
            return error("Please wait for the current reply.", 409)
        async with session.lock:
            if session.history and profile != session.profile:
                return error("Start another situation before changing context, or explain the change in a follow-up.", 409)
            session.profile = profile
            if not ready:
                return error("AI replies are not connected yet. Your context is saved for this session; no paid request was made.", 503)
            if len(session.history) >= KitchenCoach.MAX_TURNS * 2:
                return error("This conversation is full. Start another situation and include any ongoing restrictions.", 409)
            now = clock()
            while calls and calls[0] <= now - 86400:
                calls.popleft()
            if session.calls >= 30 or len(calls) >= settings.max_calls or now - session.last_call < 2:
                return error("The testing request limit was reached. Wait briefly, or contact the test organizer.", 429)
            session.calls += 1
            session.last_call = now
            calls.append(now)
            try:
                async with capacity:
                    if session.expires <= clock():
                        return error("Your session ended. Reload and sign in again.", 401)
                    kitchen = copy.deepcopy(session.kitchen)
                    answer = await run_in_threadpool(service.respond, profile, list(session.history), text.strip(), kitchen=kitchen)
            except ContextFull:
                return error("This conversation is full. Start another situation; carry forward your restrictions and latest constraints.", 409)
            except Exception:
                return error("The AI coach could not reply. Your question is still here. Please try again; no meal-plan substitute was used.", 503)
            if session.expires <= clock() or active(request) is not session:
                return error("Your session ended. Reload and sign in again.", 401)
            session.kitchen = kitchen
            session.history.extend([{"role": "user", "content": text.strip()},
                                    {"role": "assistant", "content": answer.text}])
            return {"reply": answer.text}

    @app.post("/reset")
    async def reset(request: Request):
        session = authorized(request)
        if not session:
            return error("Your session ended. Reload and sign in again.", 401)
        if session.lock.locked():
            return error("Please wait for the current reply.", 409)
        session.history.clear()
        session.kitchen.reset_conversation()
        return {"ok": True}

    @app.post("/logout")
    async def logout(request: Request):
        if not authorized(request):
            return error("Your session ended. Reload and sign in again.", 401)
        discard(request.cookies.get(COOKIE, ""))
        response = JSONResponse({"ok": True})
        response.delete_cookie(COOKIE, path="/coach", secure=settings.secure_cookie,
                               httponly=True, samesite="strict")
        return response

    return app
