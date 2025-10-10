# WelFore Health - Testing Guide

## Prerequisites

Before testing, ensure the following environment variables are configured:

### Required Environment Variables

```bash
# GHL (GoHighLevel) API Configuration
GHL_API_KEY=your_actual_ghl_api_key
GHL_LOCATION_ID=your_actual_ghl_location_id

# Email/SMTP Configuration
ADMIN_EMAIL=admin@welforehealth.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Note**: Without these credentials, the webhook will fail when attempting to connect to GHL or send emails.

## Test Scenarios

### Scenario 1: New User (Not in GHL)
**Expected Behavior**: Create contact, add "Freemium-Used" tag, send free plan, notify admin

**Test Payload**:
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "name": "John Smith"
  }'
```

**Expected Response**:
```json
{
  "status": "delivered",
  "type": "free",
  "message": "3-day meal plan sent",
  "user_status": "new"
}
```

**Expected Actions**:
- ✅ New contact created in GHL
- ✅ "Freemium-Used" tag added
- ✅ Free 3-day meal plan email sent to user
- ✅ Admin notification email sent

---

### Scenario 2: Returning User (In GHL, No Freemium Tag)
**Expected Behavior**: Add "Freemium-Used" tag, send free plan, notify admin

**Test Payload**:
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "returning@test.com",
    "name": "Jane O'\''Connor"
  }'
```

**Expected Response**:
```json
{
  "status": "delivered",
  "type": "free",
  "message": "3-day meal plan sent",
  "user_status": "returning"
}
```

**Expected Actions**:
- ✅ Contact found in GHL
- ✅ "Freemium-Used" tag added
- ✅ Free 3-day meal plan email sent to user
- ✅ Admin notification email sent

---

### Scenario 3: Repeat User (In GHL, Has Freemium Tag)
**Expected Behavior**: Send upsell email with Stripe payment links

**Test Payload**:
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "repeat@test.com",
    "name": "Bob Johnson"
  }'
```

**Expected Response**:
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

**Expected Actions**:
- ✅ Contact found in GHL with "Freemium-Used" tag
- ✅ Upsell email sent to user with Stripe payment links
- ❌ No free plan delivered
- ❌ No admin notification sent

---

## Edge Cases & Special Tests

### Test 4: Name with Apostrophe (PII Masking Test)
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "oconnor@test.com",
    "name": "Mary O'\''Connor"
  }'
```

**Purpose**: Verify that PII masking correctly handles names with apostrophes in logs

**Check Logs**: Verify that the name appears as `'name': '[REDACTED]'` in logs, not as `Mary O'Connor`

---

### Test 5: Missing Name Field
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "noname@test.com"
  }'
```

**Expected**: Should work with default name "there" in email templates

---

### Test 6: Missing Email (Error Case)
```bash
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "name": "No Email User"
  }'
```

**Expected Response**:
```json
{
  "status": "error",
  "message": "Email is required"
}
```

---

## Log Verification

After testing, check the logs for PII masking:

```bash
# View today's logs
cat logs/welfor_health_$(date +%Y%m%d).log
```

**Verify**:
- ✅ Email addresses are masked: `j***n@test.com`
- ✅ Names are redacted: `'name': '[REDACTED]'`
- ✅ Phone numbers (if any) are masked: `***-***-****`

---

## Testing Without External Services

If you need to test the logic without GHL/Email configured, you can:

1. **Mock Mode**: Temporarily modify the functions to return mock data
2. **Test Endpoint**: Use `/test/webhook` to see payload processing without external calls
3. **Unit Tests**: Create unit tests that mock the GHL and email services

---

## Quick Test Script

Save this as `test_all_scenarios.sh`:

```bash
#!/bin/bash

echo "Testing Scenario 1: New User"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","name":"John Smith"}'
echo -e "\n"

echo "Testing Scenario 2: Returning User"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"returning@test.com","name":"Jane Doe"}'
echo -e "\n"

echo "Testing Scenario 3: Repeat User"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"repeat@test.com","name":"Bob Johnson"}'
echo -e "\n"
```

Make it executable: `chmod +x test_all_scenarios.sh`
Run it: `./test_all_scenarios.sh`

---

## Integration Testing with GHL

To properly test the GHL integration:

1. **Set up a test contact** in GHL without the "Freemium-Used" tag
2. **Run Scenario 2** with that contact's email
3. **Verify** in GHL that the tag was added
4. **Run Scenario 3** with the same email
5. **Verify** you receive the upsell response

---

## Expected Email Templates

### Free Plan Email
- Subject: "Your FREE 3-Day Meal Plan"
- Contains: 3-day plan details, upsell links for 7-day and 14-day plans

### Upsell Email
- Subject: "Upgrade Your Meal Plan"
- Contains: Stripe payment links, benefits of premium plans

### Admin Notification
- Subject: "WelFore Health - 3-Day Free Plan Delivered to {status} User"
- Contains: User email, plan type, user status, timestamp
