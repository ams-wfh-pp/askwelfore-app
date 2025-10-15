from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional, Union
import os
from datetime import datetime
import importlib.util

# Import logger utilities (no external dependencies)
from logger_utils import logger, purge_old_logs

# Import master engine for meal plan generation
try:
    from master_engine import generate_enhanced_meal_plan, get_enhanced_recommended_pdfs, calculate_flavor_balance_index
    HAS_MASTER_ENGINE = True
    print("✅ Master Engine loaded successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not load master_engine: {e}")
    HAS_MASTER_ENGINE = False

# Defer imports that require external packages until after safety checks
# These will be imported conditionally based on package availability
ghl_integration = None
email_service = None

# ---- STARTUP LOG BANNER ----
from datetime import datetime, date

def calculate_age_from_birthday(birthday_str: str) -> int:
    """Convert birthday (string) into integer age with 18+ safety rule"""
    if not birthday_str:
        return None
    try:
        # Handles both ISO (YYYY-MM-DD) and US (MM/DD/YYYY) formats
        if "-" in birthday_str:
            dob = datetime.strptime(birthday_str, "%Y-%m-%d").date()
        else:
            dob = datetime.strptime(birthday_str, "%m/%d/%Y").date()
        age = (date.today() - dob).days // 365
        return max(age, 18)
    except Exception as e:
        print(f"⚠️  Birthday parsing error: {e}")
        return None

APP_NAME = "AskWelFore App"
APP_VERSION = "v1.1 – Global Finalist Edition"
APP_ORG = "WelFore Health"
APP_TAGLINE = "Flavor-Full Food-as-Medicine Wellness Starts Here"

startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("\n" + "="*70)
print(f"🚀  {APP_NAME} | {APP_VERSION}")
print(f"🏆  {APP_ORG} — Digital Health Hub Global Finalist (Wellness & Prevention 2025)")
print(f"✨  {APP_TAGLINE}")
print(f"🕒  Launched at: {startup_time}")
print("="*70 + "\n")
# ---- END STARTUP LOG BANNER ----

# ---- Dependency Diagnostic Check (Auto-run on startup) ----
import importlib

required_packages = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "requests",
    "python-multipart",
    "python-dateutil",
    "pydantic",
    "aiofiles"
]

missing = []
for pkg in required_packages:
    if importlib.util.find_spec(pkg) is None:
        missing.append(pkg)

if missing:
    print(f"⚠️  Warning: Missing packages detected — {', '.join(missing)}")
    print("   The app will continue running, but please reinstall the missing dependencies.")
else:
    print("✅ All core dependencies verified and ready to go.")
# ---- End Diagnostic ----

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
# --- BIRTHDAY → AGE AUTO-CONVERTER (for GHL quiz compatibility) ---
from datetime import datetime, date

def calculate_age_from_birthday(birthday_str: str) -> int:
    """Convert birthday (string) into integer age with 18+ safety rule"""
    if not birthday_str:
        return None
    try:
        # Handles both ISO (YYYY-MM-DD) and US (MM/DD/YYYY) formats
        if "-" in birthday_str:
            dob = datetime.strptime(birthday_str, "%Y-%m-%d").date()
        else:
            dob = datetime.strptime(birthday_str, "%m/%d/%Y").date()
        age = (date.today() - dob).days // 365
        return max(age, 18)
    except Exception as e:
        print(f"⚠️  Birthday parsing error: {e}")
        return None

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
# --- PREFILL HANDLER FOR GHL REDIRECT (Render) ---
from fastapi.responses import RedirectResponse

@app.get("/prefill", response_class=RedirectResponse)
async def prefill_to_quiz(first_name: str = None, email: str = None, phone: str = None, birthday: str = None):
    """Redirect from GHL quiz → AskWelFore form with prefilled fields"""
    # Convert birthday to age if present
    age = calculate_age_from_birthday(birthday)
    redirect_url = f"/?first_name={first_name or ''}&email={email or ''}&phone={phone or ''}&age={age or ''}"
    return RedirectResponse(url=redirect_url)


@app.get("/", response_class=HTMLResponse)
async def show_quiz(request: Request):
    """Serve the 6-step Eat-the-Rainbow questionnaire"""
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
    return templates.TemplateResponse("plan.html", {"request": request})

# Only register form submission endpoint if multipart is available
if HAS_MULTIPART:
    @app.post("/submit", response_class=HTMLResponse)
    async def submit_quiz(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        age: int = Form(...),
        gender: str = Form(...),
        who_eat_with: str = Form(...),
        family_size: str = Form(""),
        # Rainbow foods by color
        red_foods: List[str] = Form([]),
        red_foods_other: str = Form(None),
        orange_foods: List[str] = Form([]),
        orange_foods_other: str = Form(None),
        yellow_foods: List[str] = Form([]),
        yellow_foods_other: str = Form(None),
        green_foods: List[str] = Form([]),
        green_foods_other: str = Form(None),
        purple_foods: List[str] = Form([]),
        purple_foods_other: str = Form(None),
        white_foods: List[str] = Form([]),
        white_foods_other: str = Form(None),
        # Health goals
        health_goal: str = Form(...),
        dietary_restrictions: List[str] = Form([]),
        dietary_restrictions_other: str = Form(None),
        special_conditions: List[str] = Form([]),
        feel_best: str = Form(None),
        # Cuisines
        cuisines: List[str] = Form([]),
        cuisines_other: str = Form(None),
        flavor_story: str = Form(None),
        reinvent_dish: str = Form(None),
        # Lifestyle
        activity_level: str = Form(...),
        energy_levels: str = Form(None),
        snacking: str = Form(None),
        kitchen_tools: List[str] = Form([]),
        food_access: str = Form(...),
        food_budget: str = Form(...),
        meals_per_day: str = Form(...),
        cooking_time: str = Form(None),
        challenges: str = Form(None),
        plan_duration: int = Form(3)
    ):
        """Handle 6-step quiz form submission and display personalized meal plan"""
        try:
            logger.info(f"Quiz submitted: {{'name': '{name}', 'email': '{email}', 'plan_duration': {plan_duration}}}")
            
            # Convert family_size from string to int (handle empty string)
            family_size_int = int(family_size) if family_size and family_size.strip() else None
            
            # Build rainbow preferences dictionary
            rainbow_preferences = {
                "red": {"foods": red_foods, "other": red_foods_other},
                "orange": {"foods": orange_foods, "other": orange_foods_other},
                "yellow": {"foods": yellow_foods, "other": yellow_foods_other},
                "green": {"foods": green_foods, "other": green_foods_other},
                "purple": {"foods": purple_foods, "other": purple_foods_other},
                "white": {"foods": white_foods, "other": white_foods_other}
            }
            
            # Combine dietary restrictions
            all_dietary_restrictions = dietary_restrictions.copy()
            if dietary_restrictions_other:
                all_dietary_restrictions.append(dietary_restrictions_other)
            
            # Combine cuisines
            all_cuisines = cuisines.copy() if cuisines else ["Mediterranean"]
            
            # Build user profile
            user_profile = {
                "name": name,
                "email": email,
                "age": age,
                "gender": gender,
                "who_eat_with": who_eat_with,
                "family_size": family_size_int,
                "rainbow_preferences": rainbow_preferences,
                "health_goal": health_goal,
                "dietary_restrictions": all_dietary_restrictions,
                "special_conditions": special_conditions,
                "feel_best": feel_best,
                "cuisines": all_cuisines,
                "cuisines_other": cuisines_other,
                "flavor_story": flavor_story,
                "reinvent_dish": reinvent_dish,
                "activity_level": activity_level,
                "energy_levels": energy_levels,
                "snacking": snacking,
                "kitchen_tools": kitchen_tools,
                "food_access": food_access,
                "food_budget": food_budget,
                "meals_per_day": meals_per_day,
                "cooking_time": cooking_time,
                "challenges": challenges,
                "plan_duration": plan_duration
            }
            
            # Freemium control logic
            is_premium = plan_duration > 3
            
            # Generate meal plan using master engine
            if HAS_MASTER_ENGINE:
                meal_plan = generate_enhanced_meal_plan(user_profile)
                pdf_recommendations = get_enhanced_recommended_pdfs(user_profile)
                flavor_balance_index = calculate_flavor_balance_index(meal_plan)

                
                # Add freemium messaging
                if is_premium:
                    meal_plan["is_premium"] = True
                    meal_plan["premium_message"] = "✨ Unlock your full 7-day plan with WelFore Premium!"
                    meal_plan["stripe_link"] = STRIPE_7DAY_LINK if plan_duration == 7 else STRIPE_14DAY_LINK
                else:
                    meal_plan["is_premium"] = False
                
                return templates.TemplateResponse("results.html", {
    "request": request,
    "meal_plan": meal_plan,
    "pdf_recommendations": pdf_recommendations,
    "flavor_balance_index": flavor_balance_index,
    "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p")
})

            else:
                # Fallback if master engine not available
                return templates.TemplateResponse("results.html", {
                    "request": request,
                    "error": True,
                    "error_message": "Meal plan generation is temporarily unavailable. Please try again later.",
                    "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p")
                })
                
        except Exception as e:
            logger.error(f"Error processing quiz submission: {str(e)}", exc_info=True)
            return templates.TemplateResponse("results.html", {
                "request": request,
                "error": True,
                "error_message": "We encountered an issue processing your request. Please try again.",
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

# ---- SHUTDOWN LOG HANDLER ----
import atexit
from datetime import datetime

def log_shutdown_message():
    shutdown_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "-"*70)
    print(f"🛑  {APP_NAME} shutting down gracefully at {shutdown_time}")
    print(f"🧩  All services closed cleanly. See logs for details.")
    print("-"*70 + "\n")

# Register the shutdown handler
atexit.register(log_shutdown_message)
# ---- END SHUTDOWN LOG HANDLER ----
