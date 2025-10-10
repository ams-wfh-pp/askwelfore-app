# WelFore Health - Freemium Lock + Upsell System

## Overview
This application implements a freemium protection system that ensures users receive the free 3-day meal plan only once, enforced via GHL (GoHighLevel) tagging. Repeat users are automatically sent upsell offers for 7-day and 14-day premium plans.

## Features
- ✅ One-time free 3-day meal plan per user
- ✅ GHL contact lookup and tagging (Freemium-Used tag)
- ✅ Automatic upsell for repeat users
- ✅ Admin email notifications on every free plan delivery
- ✅ PII-masked logging with 7-day auto-purge
- ✅ Stripe payment integration

## Required Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# GHL Configuration
GHL_API_KEY=your_ghl_api_key_here
GHL_LOCATION_ID=your_ghl_location_id_here

# Email Configuration  
ADMIN_EMAIL=admin@welforehealth.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

## Required Python Packages

The following packages need to be installed:
- `requests` - For GHL API calls
- `python-dateutil` - For date handling
- `pydantic` - For data validation
- `python-multipart` - For form handling
- `aiofiles` - For async file operations

## API Endpoints

### POST /webhook/quiz
Main webhook endpoint for quiz submissions. Implements freemium logic.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**Response - New/Returning User (Free Plan):**
```json
{
  "status": "delivered",
  "type": "free",
  "message": "3-day meal plan sent",
  "user_status": "new"
}
```

**Response - Repeat User (Upsell):**
```json
{
  "status": "blocked",
  "type": "upsell",
  "message": "Free plan already used. Upgrade options sent.",
  "upgrade_links": {
    "7_day": "https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a",
    "14_day": "https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b"
  }
}
```

### GET /health
Health check endpoint

### POST /test/webhook
Test endpoint for webhook validation

## User Flow Logic

1. **New User** (not in GHL):
   - Create contact in GHL
   - Tag with "Freemium-Used"
   - Send free 3-day meal plan
   - Notify admin
   - Return: `{"status":"delivered","type":"free"}`

2. **Returning User** (in GHL, no Freemium-Used tag):
   - Add "Freemium-Used" tag
   - Send free 3-day meal plan
   - Notify admin
   - Return: `{"status":"delivered","type":"free"}`

3. **Repeat User** (in GHL, has Freemium-Used tag):
   - Send upsell email with Stripe links
   - Return: `{"status":"blocked","type":"upsell"}`

## Logging & Privacy
- All logs are PII-masked (emails, phone numbers, names)
- Logs auto-purge after 7 days
- Logs stored in `/logs` directory

## Stripe Payment Links
- **7-Day Plan**: https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a
- **14-Day Plan**: https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b

## Testing

Test with three scenarios:

### 1. New User
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","name":"New User"}'
```
Expected: `{"status":"delivered","type":"free"}`

### 2. Returning User (no tag)
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"returning@test.com","name":"Returning User"}'
```
Expected: `{"status":"delivered","type":"free"}`

### 3. Repeat User (with tag)
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"repeat@test.com","name":"Repeat User"}'
```
Expected: `{"status":"blocked","type":"upsell"}`

## File Structure
```
.
├── main.py                 # Main FastAPI application
├── logger_utils.py        # PII-masked logging utility
├── ghl_integration.py     # GHL API integration
├── email_service.py       # Email sending service
├── .env.example          # Environment variables template
└── README.md             # This file
```
