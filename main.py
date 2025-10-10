from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional
import os
from datetime import datetime
import importlib.util

# Import logger utilities (no external dependencies)
from logger_utils import logger, purge_old_logs

# Defer imports that require external packages until after safety checks
# These will be imported conditionally based on package availability
ghl_integration = None
email_service = None

# ---- SAFETY PATCH START ----
# Check for required packages and warn if missing (prevents crashes)
required_packages = ["fastapi", "jinja2", "requests", "pydantic", "multipart"]
missing = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

# Check if python-multipart is available for Form handling
HAS_MULTIPART = importlib.util.find_spec("multipart") is not None
HAS_REQUESTS = importlib.util.find_spec("requests") is not None

if missing:
    print(f"⚠️ Warning: Missing packages detected: {', '.join(missing)}. "
          "App will continue running, but some features may not work properly.")
    logger.warning(f"Missing packages: {', '.join(missing)}")
    if not HAS_MULTIPART:
        print("⚠️ Form submission endpoint will be disabled until python-multipart is installed")
    if not HAS_REQUESTS:
        print("⚠️ GHL integration and email features will be disabled until requests is installed")
else:
    print("✅ All required packages are installed")
    logger.info("All required packages verified")

# Conditionally import Form if multipart is available
if HAS_MULTIPART:
    from fastapi import Form
    print("✅ Form handling enabled")
else:
    # Create a dummy Form for type hints
    def Form(*args, **kwargs):
        raise RuntimeError("python-multipart not installed")

# Conditionally import GHL and email services if requests is available
if HAS_REQUESTS:
    try:
        from ghl_integration import lookup_contact, has_freemium_tag, add_tag_to_contact, create_contact
        from email_service import send_admin_notification, get_free_plan_email, get_upsell_email, send_email
        print("✅ GHL integration and email services loaded")
    except Exception as e:
        print(f"⚠️ Warning: Could not load GHL/email services: {e}")
        HAS_REQUESTS = False
else:
    # Create stub functions that return appropriate errors (synchronous to match real functions)
    def lookup_contact(email): return None
    def has_freemium_tag(contact): return False
    def add_tag_to_contact(contact_id, tag): pass
    def create_contact(email, name): return None
    def send_admin_notification(email, plan_type, user_status): pass
    def get_free_plan_email(name): return ""
    def get_upsell_email(name): return ""
    def send_email(to, subject, body): pass
    print("⚠️ GHL/email functions stubbed (requests not available)")

app = FastAPI()

# Global exception handler to prevent crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "The request could not be processed"}
    )

print("✅ Safety patch loaded successfully")
logger.info("Safety patch and global exception handler active")
# ---- SAFETY PATCH END ----

# Mount static files and setup templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Static files mounted")
except Exception as e:
    print(f"⚠️ Warning: Could not mount static files: {e}")
    
templates = Jinja2Templates(directory="templates")
print("✅ Templates configured")

STRIPE_7DAY_LINK = os.getenv('STRIPE_7DAY_LINK', "https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a")
STRIPE_14DAY_LINK = os.getenv('STRIPE_14DAY_LINK', "https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b")

@app.on_event("startup")
async def startup_event():
    purge_old_logs()
    logger.info("WelFore Health App started")

@app.get("/", response_class=HTMLResponse)
async def show_quiz(request: Request):
    """Serve the sequential questionnaire quiz page"""
    if not HAS_MULTIPART:
        # If multipart is missing, show a message
        return HTMLResponse(content=f"""
        <html>
        <head><title>WelFore Health - Setup Required</title></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🏆 WelFore Health - Award-Winning Wellness Platform</h1>
            <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0;">
                <h3>⚠️ Package Installation Required</h3>
                <p>The quiz form requires the <code>python-multipart</code> package to be installed.</p>
                <p>To use the full quiz experience, please install the required package:</p>
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">pip install python-multipart</pre>
                <p>Meanwhile, you can use our JSON webhook endpoint at <code>POST /webhook/quiz</code></p>
            </div>
            <h3>Available Endpoints:</h3>
            <ul>
                <li>✅ <strong>POST /webhook/quiz</strong> - Freemium lock & upsell (JSON payload)</li>
                <li>✅ <strong>GET /health</strong> - Health check</li>
                <li>⚠️ <strong>GET /</strong> - Quiz form (requires python-multipart)</li>
            </ul>
        </body>
        </html>
        """, status_code=200)
    return templates.TemplateResponse("quiz.html", {"request": request})

# Only register form submission endpoint if multipart is available
if HAS_MULTIPART:
    @app.post("/submit", response_class=HTMLResponse)
    async def submit_quiz(
        request: Request,
        name: str = Form(...),
        goal: str = Form(...),
        cuisine: List[str] = Form([]),
        meals_per_day: str = Form(...),
        challenge: str = Form(...)
    ):
        """Handle quiz form submission and display personalized plan"""
        logger.info(f"Quiz submitted: {{'name': '{name}', 'goal': '{goal}', 'meals_per_day': '{meals_per_day}'}}")
        
        # Create a simple meal plan summary
        cuisines_text = ", ".join(cuisine) if cuisine else "Various"
        plan_items = [
            f"Health Goal: {goal}",
            f"Preferred Cuisines: {cuisines_text}",
            f"Daily Meal Structure: {meals_per_day} meals",
            f"Main Challenge Addressed: {challenge}",
            "✨ Your personalized Flavor-First meal plan is being prepared!",
            "🌈 Includes rainbow nutrition tracking",
            "💪 Tailored to your health goals"
        ]
        
        return templates.TemplateResponse("plan.html", {
            "request": request,
            "result": {
                "name": name,
                "goal": goal
            },
            "plan": plan_items,
            "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p")
        })
    print("✅ Form submission endpoint registered")
else:
    print("⚠️ Form submission endpoint skipped (python-multipart not installed)")

@app.post("/webhook/quiz")
async def quiz_webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Received quiz webhook: {payload}")
        
        email = payload.get('email')
        name = payload.get('name', '')
        
        if not email:
            logger.error("No email provided in webhook payload")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Email is required"}
            )
        
        # Check if requests package is available for GHL integration
        if not HAS_REQUESTS:
            logger.warning("Webhook received but requests package not available - returning setup message")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "message": "GHL integration requires the 'requests' package to be installed",
                    "setup_required": "pip install requests python-dateutil pydantic",
                    "note": "The app is running in limited mode. Install dependencies for full functionality."
                }
            )
        
        contact = lookup_contact(email)
        
        if contact is None:
            contact = create_contact(email, name)
            if contact:
                user_status = "new"
            else:
                logger.error(f"Failed to create contact for {email}")
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Failed to process request"}
                )
        else:
            has_tag = has_freemium_tag(contact)
            if has_tag:
                user_status = "repeat"
            else:
                user_status = "returning"
        
        logger.info(f"User status: {user_status} for email: {email}")
        
        if user_status in ["new", "returning"]:
            contact_id = contact.get('id')
            if contact_id:
                add_tag_to_contact(contact_id, "Freemium-Used")
            
            email_body = get_free_plan_email(name or 'there')
            send_email(email, "Your FREE 3-Day Meal Plan", email_body)
            
            send_admin_notification(email, "3-Day Free", user_status)
            
            logger.info(f"Free plan delivered to {user_status} user: {email}")
            return JSONResponse(
                content={
                    "status": "delivered",
                    "type": "free",
                    "message": "3-day meal plan sent",
                    "user_status": user_status
                }
            )
        
        else:
            email_body = get_upsell_email(name or 'there')
            send_email(email, "Upgrade Your Meal Plan", email_body)
            
            logger.info(f"Upsell sent to repeat user: {email}")
            return JSONResponse(
                content={
                    "status": "blocked",
                    "type": "upsell",
                    "message": "Free plan already used. Upgrade options sent.",
                    "upgrade_links": {
                        "7_day": STRIPE_7DAY_LINK,
                        "14_day": STRIPE_14DAY_LINK
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal server error"}
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/test/webhook")
async def test_webhook(request: Request):
    payload = await request.json()
    logger.info(f"Test webhook received: {payload}")
    return {"status": "test_received", "payload": payload}
