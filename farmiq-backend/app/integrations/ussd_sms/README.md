# USSD/SMS Integration Documentation

## Overview

FarmIQ integrates with **Africa's Talking** to provide USSD and SMS services, enabling farmers in rural Kenya to access the platform via basic feature phones. This document describes the complete integration architecture, setup, and usage.

## Architecture

### Components

1. **AfricasTalkingClient** - Unified API client for all Africa's Talking services
2. **USSDService** - Session-based menu navigation with state management
3. **SMSService** - Sending, receiving, and delivery tracking
4. **FastAPI Routes** - Webhook endpoints for Africa's Talking callbacks
5. **Database Schema** - Tables for sessions, messages, and delivery tracking

### Flow

```
User Phone
    ↓ (dials *384*49848#)
Africa's Talking Gateway
    ↓ (POST to webhook)
FastAPI /api/v1/ussd/menu
    ↓
USSDService.handle_ussd_request()
    ↓ (menu navigation)
USSDMenuTree
    ↓ (return "CON" or "END")
Africa's Talking Gateway
    ↓ (displays menu)
User Phone
```

## Environment Setup

### Africa's Talking Credentials

Create or update `.env.africastalking`:

```env
# Africa's Talking Configuration
AFRIKATALK_ENVIRONMENT=sandbox          # or 'production'
AFRIKATALK_USERNAME=sandbox             # Your AT username
AFRIKATALK_API_KEY=atsk_xxxxxxxxxxxx    # Your AT API key
AFRIKATALK_USSD_SERVICE_CODE=*384*49848#
AFRIKATALK_USSD_SHORT_CODE=45986
AFRIKATALK_SMS_SENDER_ID=FarmIQLtd

# Webhook URLs (must be publicly accessible)
USSD_WEBHOOK_URL=https://farmiq-six.vercel.app/api/v1/ussd/menu
SMS_INCOMING_WEBHOOK_URL=https://farmiq-six.vercel.app/api/v1/sms/incoming
SMS_DELIVERY_WEBHOOK_URL=https://farmiq-six.vercel.app/api/v1/sms/delivery

# Feature Flags
ENABLE_USSD=true
ENABLE_SMS=true
ENABLE_BULK_SMS=true

# Timeouts (seconds)
USSD_SESSION_TIMEOUT=600         # 10 minutes
USSD_MENU_RESPONSE_TIMEOUT=30

# SMS Configuration
SMS_BATCH_SIZE=100
SMS_BATCH_DELAY=5
```

### FastAPI App Integration

In your `main.py` or `app.py`:

```python
from app.integrations.ussd_sms.routes import router as ussd_sms_router

app.include_router(ussd_sms_router)
```

### Database Setup

Run the migration:

```bash
psql -d farmiq_db -f supabase/migrations/20260319_ussd_sms_integration.sql
```

This creates:
- `ussd_sessions` - Session state tracking
- `sms_delivery_track` - SMS logs
- `sms_delivery_reports` - Delivery status
- `sms_optouts` - Opt-out tracking
- `ussd_navigation_audit` - Analytics

## API Endpoints

### USSD Endpoints

#### `POST /api/v1/ussd/menu`

**Called by Africa's Talking webhook** when user sends USSD input.

Request (form-encoded):
```
sessionId=c38a2c3d-b2a4-4d23-b5c2-d0c32e4e5f6g
serviceCode=*384*49848#
phoneNumber=%2B254712345678
text=
networkCode=63902
```

Response:
```
CON What would you like to do?
1. Check Balance
2. Buy Tokens
3. Subscribe to Tools
4. Get Help
```

Or on completion:
```
END Thank you for using FarmIQ!
```

#### `GET /api/v1/ussd/session/{session_id}`

**Debug endpoint** - Get session details.

Response:
```json
{
  "session_id": "c38a2c3d-b2a4-4d23-b5c2-d0c32e4e5f6g",
  "phone_number": "+254712345678",
  "current_menu": "balance",
  "input_history": ["1"],
  "created_at": "2024-03-19T10:00:00Z",
  "expires_at": "2024-03-19T10:10:00Z"
}
```

### SMS Endpoints

#### `POST /api/v1/sms/send`

**Send SMS to recipients**.

Request:
```json
{
  "recipients": ["+254712345678", "+254787654321"],
  "message": "Hello, this is a test message",
  "sender_id": "FarmIQLtd"
}
```

Response:
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "recipient_count": 2,
  "message_ids": ["ATXid_123", "ATXid_124"],
  "total_cost": 1.6
}
```

#### `POST /api/v1/sms/fetch`

**Poll incoming SMS**.

Query params:
- `last_received_id` (optional): ID of last fetched message

Response:
```json
{
  "success": true,
  "message_count": 2,
  "last_id": 456789,
  "messages": [
    {
      "id": "456789",
      "from": "+254712345678",
      "to": "45986",
      "text": "1",
      "date": "2024-03-19 10:00:00",
      "networkCode": "63902"
    }
  ]
}
```

#### `POST /api/v1/sms/incoming`

**Webhook for incoming SMS** (called by Africa's Talking).

Request (form-encoded):
```
from=%2B254712345678
to=45986
text=Hello+FarmIQ
id=ATXid_789
```

Response:
```json
{"status": "ok"}
```

#### `POST /api/v1/sms/delivery`

**Webhook for SMS delivery reports** (called by Africa's Talking).

Request (form-encoded):
```
id=ATXid_123
status=Success
phoneNumber=%2B254712345678
failureReason=
networkCode=63902
```

Response:
```json
{"status": "ok"}
```

#### `GET /api/v1/ussd-sms/health`

**Health check** - Verify connection and balance.

Response:
```json
{
  "status": "healthy",
  "service": "USSD/SMS",
  "balance": 1234.50,
  "timestamp": "2024-03-19T10:00:00Z"
}
```

## USSD Menu Structure

### Welcome Menu
```
CON What would you like to do?
1. Check Balance
2. Buy Tokens
3. Subscribe to Tools
4. Get Help
```

### Check Balance
```
END Your FarmIQ Balance: 150 FIQ

(Terminal response - session ends)
```

### Buy Tokens
```
CON Select package:
1. 100 FIQ (KES 150)
2. 500 FIQ (KES 750)
3. 1000 FIQ (KES 1,500)
4. 5000 FIQ (KES 7,500)
```

After selection → M-Pesa payment prompt

### Subscribe to Tools
```
CON Select AI tool:
1. Disease Detection (500 FIQ/month)
2. Weather Forecast (300 FIQ/month)
3. Yield Prediction (800 FIQ/month)
4. Market Prices (200 FIQ/month)
```

### Get Help
```
CON Help topics:
1. How to buy tokens
2. FAQ
3. Contact support
```

## Usage Examples

### Python - Send SMS via FastAPI Client

```python
import httpx

async def send_notification():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/sms/send",
            json={
                "recipients": ["+254712345678"],
                "message": "Disease alert: Leaf rust detected near your area",
                "sender_id": "FarmIQLtd"
            }
        )
        result = response.json()
        print(f"SMS sent: {result['success']}")
```

### Python - Send SMS via Service

```python
from app.integrations.ussd_sms import SMSService
from core.database import get_db_pool

# Initialize
pool = await get_db_pool()
sms_service = SMSService(
    api_key="atsk_...",
    username="sandbox",
    environment="sandbox"
)

# Send
result = await sms_service.send_sms(
    recipients=["+254712345678"],
    message="Your farm needs attention",
    sender_id="FarmIQLtd",
    db_pool=pool
)
```

### Python - Check Balance

```python
from app.integrations.ussd_sms import AfricasTalkingClient, AfricasTalkingEnvironment

client = AfricasTalkingClient(
    username="sandbox",
    api_key="atsk_...",
    environment=AfricasTalkingEnvironment.SANDBOX
)

balance = await client.get_balance()
print(f"Remaining balance: KES {balance}")
```

## Integration with Token System

### USSD → Token Purchase Flow

1. User dials `*384*49848#`
2. Selects "Buy Tokens" → Choose package
3. USSD service calls M-Pesa Daraja API
4. User enters M-Pesa PIN on her phone
5. M-Pesa webhook confirms payment
6. Token minting service mints FIQ tokens
7. User receives SMS: "You have received 500 FIQ"
8. User can now subscribe to tools via USSD or web app

### Token Purchase via USSD

```python
# In ussd_service.py

async def _initiate_token_purchase(self, phone_number: str, amount_fiq: int):
    """Initiate token purchase via M-Pesa"""
    
    # Calculate KES amount (1 FIQ = 150 KES)
    amount_kes = amount_fiq * 1.5
    
    # Call M-Pesa Daraja API
    mpesa_result = await initiate_mpesa_payment(
        phone_number=phone_number,
        amount=amount_kes,
        account_reference="FarmIQ",
        transaction_desc="Token Purchase",
    )
    
    if mpesa_result["success"]:
        # Log transaction
        await self._log_transaction(phone_number, amount_fiq)
        return f"CON Enter your M-Pesa PIN to confirm KES {amount_kes}"
    else:
        return "END Error: Could not initiate payment. Try again."
```

## Testing

### 1. Sandbox Testing

1. Sign up at [Africa's Talking](https://africastalking.com)
2. Create an app (sandbox)
3. Get credentials (API key, username)
4. Update `.env.africastalking`
5. Set webhook URLs to your localhost (using ngrok or serveo):

```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Update webhook URL in Africa's Talking dashboard
# e.g., https://abc123.ngrok.io/api/v1/ussd/menu
```

### 2. Test USSD

```bash
# Using curl to simulate Africa's Talking webhook

curl -X POST http://localhost:8000/api/v1/ussd/menu \
  -d "sessionId=test-session-1" \
  -d "serviceCode=*384*49848#" \
  -d "phoneNumber=%2B254712345678" \
  -d "text=" \
  -d "networkCode=63902"

# Response:
# CON What would you like to do?
# 1. Check Balance
# 2. Buy Tokens
# 3. Subscribe to Tools
# 4. Get Help
```

### 3. Test SMS Send

```bash
curl -X POST http://localhost:8000/api/v1/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+254712345678"],
    "message": "Test message from FarmIQ",
    "sender_id": "FarmIQLtd"
  }'
```

### 4. Check Health

```bash
curl http://localhost:8000/api/v1/ussd-sms/health
```

## Database Schema

### Key Tables

**ussd_sessions**
- Tracks USSD session state
- Expires after 10 minutes of inactivity
- Stores menu navigation history

**sms_delivery_track**
- Comprehensive SMS log
- Links to users by phone number
- Tracks all SMS operations (sent, received, failed)

**sms_delivery_reports**
- Detailed delivery status from Africa's Talking
- Maps to sms_delivery_track

**sms_optouts**
- Tracks users who opt out from sender ID
- Prevents sending to opted-out numbers

**ussd_navigation_audit**
- Analytics: Tracks all menu navigations
- Useful for A/B testing, UX improvements

### Analytics Views

Query USSD engagement:
```sql
SELECT * FROM ussd_session_summary;
```

Query SMS daily stats:
```sql
SELECT * FROM sms_daily_stats WHERE date = CURRENT_DATE;
```

Query user USSD usage:
```sql
SELECT * FROM user_ussd_usage_stats WHERE id = 'user-uuid';
```

## Security

### Signature Validation

Validate all webhooks from Africa's Talking:

```python
from app.integrations.ussd_sms import AfricasTalkingClient

client = AfricasTalkingClient(username, api_key)

# In route handler:
body = await request.body()
signature = request.headers.get("X-Signature")

if not client.validate_webhook_signature(body.decode(), signature):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

### Phone Number Validation

- All phone numbers must be in international format: +254...
- Validate against user profile
- Check opt-out list before sending bulk SMS

### Rate Limiting

- USSD: 10 seconds between responses
- SMS: Max 100 recipients per batch, 5-second delay
- Account balance check before sending

## Troubleshooting

### Issue: USSD Menu Not Responding

**Check:**
1. Webhook URL is public and accessible
2. Africa's Talking credentials are correct
3. Service code matches configuration
4. Phone number format is international

**Solution:**
```bash
# Test webhook directly
curl -v http://localhost:8000/api/v1/ussd/menu \
  -d "sessionId=test" \
  -d "serviceCode=*384*49848#" \
  -d "phoneNumber=%2B254712345678" \
  -d "text="
```

### Issue: SMS Not Sending

**Check:**
1. Account has sufficient balance
2. Recipients phone numbers are valid
3. Sender ID is whitelisted
4. Message doesn't exceed 160 characters (or is split correctly)

**Solution:**
```bash
# Check balance
curl http://localhost:8000/api/v1/ussd-sms/health
```

### Issue: Delivery Reports Not Updating

**Check:**
1. SMS delivery webhook is registered in Africa's Talking
2. Webhook URL is correct
3. Database table exists
4. Check logs for errors

**Solution:**
```sql
-- Verify table exists
\d sms_delivery_reports

-- Check recent delivery reports
SELECT * FROM sms_delivery_reports 
ORDER BY report_received_at DESC LIMIT 10;
```

## Production Checklist

- [ ] Update `.env.africastalking` with production credentials
- [ ] Set `AFRIKATALK_ENVIRONMENT=production`
- [ ] Update webhook URLs to production domain
- [ ] Register webhooks in Africa's Talking dashboard
- [ ] Test signature validation
- [ ] Set up monitoring/alerts for balance
- [ ] Configure rate limiting
- [ ] Set up SMS opt-out management
- [ ] Document team access procedures
- [ ] Create backup plan for SMS failures

## Support

- Africa's Talking Docs: https://africastalking.com/sms/premium
- USSD Docs: https://africastalking.com/ussd/
- FarmIQ Team: support@farmiq.ke
