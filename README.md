# 🌈 WelFore Health - AskWelFore App

## About the AskWelFore App

The **AskWelFore App** is an AI-enabled digital nutrition platform designed to make **Flavor-First, Family-Centered wellness** accessible to everyone. Built by WelFore Health, it personalizes meal plans, flavor preferences, and behavior change journeys through an interactive, evidence-based questionnaire powered by the principles of **Food as Medicine** and **Eat the Rainbow**.

**Recognized globally as a Finalist in the 2025 Digital Health Hub Awards for Wellness & Prevention**, AskWelFore combines clinical credibility with culturally attuned design — blending bold, salt-free flavors, portion-smart tools, and science-backed guidance to help families prevent diet-related chronic disease.

This release (**v1.1 – Global Finalist Edition**) strengthens reliability and engagement with:

- 🛡️ **Crash-proof backend** and /health endpoint for monitoring
- 🌈 **Sequential, guided onboarding** that personalizes each user journey
- 🏆 **Global finalist branding** for trust and credibility
- 📊 **Enhanced UI polish** aligned with WelFore Health's signature style

Together, these features make AskWelFore not just an app — but a movement to make **Flavor-Full Food-as-Medicine Wellness** the new standard of care.

---

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
├── templates/
│   ├── quiz.html          # Sequential questionnaire
│   └── plan.html          # Personalized plan results
├── static/
│   └── WELFORE.png        # Award finalist badge
├── backup_pre_award_patch/ # Backup of previous version
├── .env.example           # Environment variables template
└── README.md              # This file
```

---

## 🧾 Version Notes: AskWelFore App – Global Finalist Edition (v1.1)

**Release Date:** October 2025  
**Tag:** `v1.1_award_patch`  
**Maintained by:** WelFore Health Engineering Team  
**Recognition:** Finalist – Digital Health Hub Global Awards 2025 (Wellness & Prevention)

### 🔹 Overview

This release marks a major milestone for the AskWelFore App, following its recognition as a **Global Digital Health Innovation Finalist for Wellness & Prevention**. It introduces stability, design, and user experience upgrades aligned with production-level reliability and trust presentation for partners, funders, and pilot users.

### 🔹 Key Enhancements

| Category | Description |
|----------|-------------|
| **Stability & Safety** | Added a Python dependency safety check and global exception handler in `main.py` to prevent crashes caused by missing packages (e.g., `python-multipart`). |
| **Health Monitoring** | Added a `/health` endpoint that confirms uptime and backend readiness for remote monitoring. |
| **Sequential Questionnaire** | Replaced single long survey form with an animated, step-by-step UX to improve user engagement and completion rate. |
| **Progress Bar** | Added visual progress tracking for user motivation and improved onboarding flow. |
| **Award Branding** | Integrated WelFore Health's Digital Health Hub Finalist banner into both the `quiz.html` and `plan.html` templates for credibility and trust. |
| **Plan Page Polish** | Updated `plan.html` layout for a more structured presentation of the generated meal plan, maintaining brand consistency. |
| **Version Lock** | Established `/backup_pre_award_patch` protocol to safeguard all previous working versions. |
| **Crash Resistance** | App continues running even when dependencies are missing, with graceful degradation and helpful error messages. |

### 🔹 Testing Checklist

- ✅ `uvicorn main:app --reload` launches without dependency errors
- ✅ `/` displays guided question flow or setup instructions
- ✅ `/health` returns `{ "status": "healthy" }`
- ✅ Server does not crash if dependencies are missing (logs warnings only)
- ✅ PII masking active on all endpoints
- ✅ Global exception handler catches all errors gracefully

### 🔹 Commit Summary

**Commit:** Add robust safety patch, sequential questionnaire, progress bar, and award-winning branding elements to AskWelFore app — preserving last known working version and ensuring all updates are additive, not destructive.

### 🔹 Next Planned Enhancements

- Integration with GoHighLevel (GHL) API for tagging and lead management
- Optional email confirmation featuring the finalist badge and plan summary
- Data analytics dashboard for quiz completion and conversion tracking

### 📝 Maintainer Note

This release positions **AskWelFore as a production-grade, award-recognized digital health platform** ready for institutional pilots and wellness program integrations.
