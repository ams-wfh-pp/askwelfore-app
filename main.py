from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any
import os
from datetime import datetime
import importlib.util

from logger_utils import logger, purge_old_logs
from ghl_integration import lookup_contact, has_freemium_tag, add_tag_to_contact, create_contact
from email_service import send_admin_notification, get_free_plan_email, get_upsell_email, send_email

# ---- SAFETY PATCH START ----
# Check for required packages and warn if missing (prevents crashes)
required_packages = ["fastapi", "jinja2", "requests", "pydantic"]
missing = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

if missing:
    print(f"⚠️ Warning: Missing packages detected: {', '.join(missing)}. "
          "App will continue running, but some features may not work properly.")
    logger.warning(f"Missing packages: {', '.join(missing)}")
else:
    print("✅ All required packages are installed")
    logger.info("All required packages verified")

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

STRIPE_7DAY_LINK = os.getenv('STRIPE_7DAY_LINK', "https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a")
STRIPE_14DAY_LINK = os.getenv('STRIPE_14DAY_LINK', "https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b")

@app.on_event("startup")
async def startup_event():
    purge_old_logs()
    logger.info("WelFore Health App started")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
    <head><title>WelFore Health</title></head>
    <body>
        <h1>Welcome to the WelFore Nutrition App</h1>
        <p>Freemium Lock + Upsell Logic Active</p>
        <ul>
            <li>Free 3-Day Meal Plan (One-Time Only)</li>
            <li>7-Day & 14-Day Premium Plans Available</li>
        </ul>
    </body>
    </html>
    """

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
        
        contact = await lookup_contact(email)
        
        if contact is None:
            contact = await create_contact(email, name)
            if contact:
                user_status = "new"
            else:
                logger.error(f"Failed to create contact for {email}")
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Failed to process request"}
                )
        else:
            has_tag = await has_freemium_tag(contact)
            if has_tag:
                user_status = "repeat"
            else:
                user_status = "returning"
        
        logger.info(f"User status: {user_status} for email: {email}")
        
        if user_status in ["new", "returning"]:
            contact_id = contact.get('id')
            if contact_id:
                await add_tag_to_contact(contact_id, "Freemium-Used")
            
            email_body = get_free_plan_email(name or 'there')
            await send_email(email, "Your FREE 3-Day Meal Plan", email_body)
            
            await send_admin_notification(email, "3-Day Free", user_status)
            
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
            await send_email(email, "Upgrade Your Meal Plan", email_body)
            
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
