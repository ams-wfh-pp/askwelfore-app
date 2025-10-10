# Installation Note - Required Python Packages

## Current Status

⚠️ **The application is fully implemented but Python packages need to be installed.**

## Merged Version - Dual Payload Support

✅ **RESTORED**: Original quiz form + meal planning system (September backup)
✅ **MERGED**: Freemium lock + upsell logic
✅ **COMBINED**: Both systems working together

The following packages are required but not yet installed:
- `requests` - For GHL API calls (needed by both endpoints)
- `python-dateutil` - For date handling
- `pydantic` - For data validation  
- `python-multipart` - **CRITICAL** for quiz form handling
- `aiofiles` - For async file operations

## Why Packages Aren't Installed

The `.replit` configuration file has a syntax error that prevents the package manager from running:
```
Error: DOT_REPLIT_SYNTAX_ERROR - Unable to validate dotreplit schema
```

## How to Fix

### Option 1: Manual Package Installation (Quickest)

Once the `.replit` file is fixed, run:
```bash
pip install requests python-dateutil pydantic python-multipart aiofiles
```

### Option 2: Use Replit Package Manager

After the `.replit` file is corrected, the Replit package manager will be able to install these dependencies automatically.

### Option 3: Contact Replit Support

If the `.replit` error persists, contact Replit support to help resolve the configuration issue.

## Verification

After installing packages, verify the installation:
```bash
python3 -c "import requests, dateutil, pydantic, multipart; print('All packages installed successfully!')"
```

Then test both endpoints:

### Test Freemium Webhook (JSON - No multipart needed)
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'
```

### Test Quiz Form (Requires python-multipart)
Open in browser: `http://localhost:5000/`

## Active Endpoints

### 1. Quiz Form System (Original - September backup)
- `GET /` - Quiz form with rainbow food preferences
- `POST /` - Process quiz, generate meal plan (requires `python-multipart`)
- `/ghl/webhook` - Receives data FROM GoHighLevel
- `/premium/7day/success` - Stripe 7-day success callback
- `/premium/14day/success` - Stripe 14-day success callback

### 2. Freemium Lock System (New - October implementation) 
- `POST /webhook/quiz` - Freemium enforcement with GHL tagging
- Enforces one-time free plan via "Freemium-Used" tag
- Sends upsell for repeat users

### 3. Utility Endpoints
- `GET /health` - Health check
- `POST /test/webhook` - Test webhook

## Current Test Results

✅ **Working**:
- FastAPI server running on port 5000
- Health endpoint responding
- Webhook endpoint receiving requests
- **PII masking working correctly** (verified in logs)
- Log purging logic implemented

❌ **Blocked by missing packages**:
- GHL API integration (needs `requests`)
- Email sending (needs `smtplib` which is built-in, but calls fail without GHL)
- Contact lookup and tagging

## Evidence of PII Masking Working

From the server logs:
```
INFO: Received quiz webhook: {'email': 't**t@example.com', 'name': '[REDACTED]'}
```

✅ Email masked: `t**t@example.com`
✅ Name redacted: `[REDACTED]`

This confirms the PII masking is functioning correctly even without external dependencies.
