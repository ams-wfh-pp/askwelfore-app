# WelFore Health - Setup Guide

## Quick Start

### 1. Configure Environment Variables

The application requires the following environment variables to function properly:

#### GHL (GoHighLevel) Integration
```bash
GHL_API_KEY=your_ghl_api_key_here
GHL_LOCATION_ID=your_ghl_location_id_here
```

**How to get these:**
1. Log into your GoHighLevel account
2. Go to Settings → API
3. Generate or copy your API key
4. Find your Location ID in the URL or settings

#### Email/SMTP Configuration
```bash
ADMIN_EMAIL=admin@welforehealth.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an "App Password" (not your regular password)
3. Use that app password for `SMTP_PASSWORD`

**Alternative SMTP Providers:**
- **SendGrid**: `SMTP_HOST=smtp.sendgrid.net`, `SMTP_PORT=587`
- **Mailgun**: `SMTP_HOST=smtp.mailgun.org`, `SMTP_PORT=587`
- **AWS SES**: `SMTP_HOST=email-smtp.us-east-1.amazonaws.com`, `SMTP_PORT=587`

#### Stripe Payment Links (Already Configured)
```bash
STRIPE_7DAY_LINK=https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a
STRIPE_14DAY_LINK=https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b
```

### 2. Set Environment Variables in Replit

**Method 1: Using Replit Secrets (Recommended)**
1. Click on "Secrets" in the left sidebar (🔒 icon)
2. Add each environment variable as a secret
3. Click "Add new secret" for each variable

**Method 2: Using .env file (Local Development)**
1. Copy `.env.example` to `.env`
2. Fill in your actual credentials
3. The app will load these automatically

### 3. Verify Installation

Run the health check:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-10-10T10:00:00.000000"}
```

### 4. Test the Webhook

Run a simple test:
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'
```

**Without credentials configured**, you'll see an error in the response or logs.
**With credentials configured**, you should see a proper response based on user status.

### 5. Run Full Test Suite

Execute the test script:
```bash
./test_all_scenarios.sh
```

This will test all three scenarios: new user, returning user, and repeat user.

---

## Required Python Packages

The following packages are required but may not be installed due to `.replit` configuration issues:

```
requests
python-dateutil
pydantic
python-multipart
aiofiles
```

**If you encounter import errors**, you may need to install these packages manually once the environment configuration is fixed.

---

## Troubleshooting

### Error: "Module 'requests' not found"
The Python packages need to be installed. This requires fixing the `.replit` configuration file first.

**Workaround**: The implementation is complete, but package installation is blocked by a `.replit` syntax error. This can be resolved by the Replit support team or by recreating the `.replit` file.

### Error: "Failed to connect to GHL"
- Verify `GHL_API_KEY` is correct
- Verify `GHL_LOCATION_ID` is correct
- Check that your GHL account has API access enabled

### Error: "Failed to send email"
- Verify SMTP credentials are correct
- For Gmail, ensure you're using an App Password, not your regular password
- Check that SMTP_HOST and SMTP_PORT are correct for your provider

### Logs show unmasked PII
This shouldn't happen with the current implementation, but if it does:
- Check that `logger_utils.py` is being imported correctly
- Verify the PIIMaskedFormatter is being used
- Report this as a bug

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  Quiz Webhook (/webhook/quiz)          │
│  - Receives email + name                │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  GHL Contact Lookup                     │
│  - Check if contact exists              │
│  - Check for "Freemium-Used" tag        │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌─────────────┐    ┌──────────────────┐
│  New/       │    │  Repeat User     │
│  Returning  │    │  (Has Tag)       │
└──────┬──────┘    └────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐    ┌──────────────────┐
│ Add Tag     │    │ Send Upsell      │
│ Send Free   │    │ Email            │
│ Plan        │    │ Return Blocked   │
│ Notify Admin│    └──────────────────┘
└─────────────┘
```

---

## File Structure

```
.
├── main.py                    # Main FastAPI application
├── logger_utils.py           # PII-masked logging
├── ghl_integration.py        # GHL API integration
├── email_service.py          # Email/SMTP service
├── .env.example             # Environment template
├── README.md                # Project documentation
├── SETUP.md                 # This file
├── TESTING.md               # Testing guide
├── test_all_scenarios.sh    # Automated test script
└── logs/                    # Log directory (auto-created)
    └── welfor_health_YYYYMMDD.log
```

---

## Next Steps

1. ✅ Configure environment variables (see section 1)
2. ✅ Verify health endpoint is responding
3. ✅ Run test suite: `./test_all_scenarios.sh`
4. ✅ Check logs for PII masking: `cat logs/welfor_health_$(date +%Y%m%d).log`
5. ✅ Verify GHL tagging in your GoHighLevel dashboard
6. ✅ Check admin email inbox for notifications
7. ✅ Test with real quiz submissions

---

## Support

For issues or questions:
- Check the logs: `logs/welfor_health_YYYYMMDD.log`
- Review TESTING.md for test scenarios
- Verify all environment variables are set correctly
