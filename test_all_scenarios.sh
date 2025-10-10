#!/bin/bash

echo "==============================================="
echo "WelFore Health - Freemium Lock Test Suite"
echo "==============================================="
echo ""

echo "📧 Scenario 1: New User (Not in GHL)"
echo "-------------------------------------------"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","name":"John Smith"}'
echo -e "\n"

sleep 1

echo "📧 Scenario 2: Returning User (In GHL, No Tag)"
echo "-------------------------------------------"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"returning@test.com","name":"Jane Doe"}'
echo -e "\n"

sleep 1

echo "🚫 Scenario 3: Repeat User (Has Freemium Tag)"
echo "-------------------------------------------"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"repeat@test.com","name":"Bob Johnson"}'
echo -e "\n"

sleep 1

echo "🔍 Edge Case: Name with Apostrophe"
echo "-------------------------------------------"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"oconnor@test.com","name":"Mary O'\''Connor"}'
echo -e "\n"

sleep 1

echo "⚠️  Error Case: Missing Email"
echo "-------------------------------------------"
curl -X POST http://localhost:5000/webhook/quiz \
  -H "Content-Type: application/json" \
  -d '{"name":"No Email User"}'
echo -e "\n"

echo "==============================================="
echo "✅ Test Suite Complete"
echo "==============================================="
echo ""
echo "Next Steps:"
echo "1. Check logs: cat logs/welfor_health_$(date +%Y%m%d).log"
echo "2. Verify PII masking in logs"
echo "3. Check GHL for contact tags (if configured)"
echo "4. Check email inbox for notifications (if configured)"
