# Architecture: Payment Failure Whisperer

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PAYMENT FAILURE WHISPERER                    │
│                          System Diagram                          │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────────┐
                         │  Razorpay API    │
                         │ (payment.failed  │
                         │   webhook event) │
                         └────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Webhook Receiver         │
                    │   (Flask Route)            │
                    │ /webhook/razorpay/payment  │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────────────────┐
                    │   Decline Code Extractor               │
                    │   - Extract error code                 │
                    │   - Extract payment method             │
                    │   - Extract card network               │
                    │   - Extract amount & currency          │
                    └─────────────┬──────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
    ┌────────┐            ┌──────────────┐         ┌──────────────┐
    │Rule    │            │Groq LLM      │         │Database      │
    │Engine  │            │Agent         │         │(PostgreSQL)  │
    │(RBI    │            │(Generate     │         │Store:        │
    │limits, │            │explanation)  │         │- Transactions│
    │velocity│            │              │         │- Explanations│
    │blocks) │            │              │         │- Recovery    │
    └────────┘            └──────────────┘         │  logs        │
        │                         │                 └──────────────┘
        └─────────────────────────┼─────────────────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │   Notification Service             │
                    │   - Format SMS/WhatsApp message    │
                    │   - Generate retry link            │
                    │   - Send via Twilio/Razorpay SMS   │
                    └─────────────┬──────────────────────┘
                                  │
                    ┌─────────────▼──────────────────┐
                    │   Customer Receives SMS        │
                    │   "Your payment failed. Click: │
                    │    [link] to retry & see why"  │
                    └────────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │   Customer Clicks Link             │
                    │   (Redirects to recovery page)     │
                    │   Shows explanation + next actions │
                    └────────────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────────────┐
                    │   Customer Retries Payment         │
                    │   (Redirect to Razorpay checkout)  │
                    └─────────────┬──────────────────────┘
                                  │
                         ┌────────▼──────────┐
                         │ Payment Succeeds? │
                         │ YES ──► Mark as   │
                         │      "Recovered"  │
                         │ NO  ──► Log retry │
                         │       failure     │
                         └───────────────────┘
```

---

## Component Breakdown

### 1. Webhook Receiver (Flask Backend)

**File:** `app.py` → route `/webhook/razorpay/payment`

**Responsibility:**
- Listen for incoming Razorpay webhooks
- Validate webhook signature (Razorpay secret key)
- Extract payment failure event data
- Route to decline processing pipeline

**Input:**
```json
{
  "event": "payment.failed",
  "payload": {
    "payment": {
      "id": "pay_ABC123",
      "amount": 50000,
      "currency": "INR",
      "method": "card",
      "email": "customer@example.com",
      "contact": "+919876543210",
      "error_code": "BAD_REQUEST_CODE_02",
      "error_description": "Invalid transaction",
      "error_source": "bank",
      "vpa": null,
      "card": {
        "network": "Visa",
        "last4": "1111",
        "issuer": "HDFC",
        "type": "debit"
      }
    }
  }
}
```

**Output:** `{"status": "processing", "request_id": "xyz"}`

---

### 2. Decline Code Extractor

**File:** `services/decline_extractor.py`

**Responsibility:**
- Parse webhook payload
- Extract structured data (error code, method, network, issuer)
- Normalize error codes (handle variations)
- Return standardized decline object

**Methods:**
- `extract_decline_info(webhook_payload)` → DeclineObject
- `normalize_error_code(raw_code)` → StandardCode

**Decline Object Structure:**
```python
{
  "error_code": "BAD_REQUEST_CODE_02",
  "error_reason": "InvalidTransaction",
  "payment_method": "card",
  "card_network": "Visa",
  "card_issuer": "HDFC",
  "card_type": "debit",
  "amount": 50000,
  "currency": "INR",
  "customer_email": "customer@example.com",
  "customer_phone": "+919876543210",
  "timestamp": "2026-09-03T12:30:00Z"
}
```

---

### 3. Rule Engine (Bank-Specific Logic)

**File:** `services/rule_engine.py`

**Responsibility:**
- Apply RBI rules (recurring mandate ₹15K limit, UPI ₹1L limit)
- Apply bank-specific rules (HDFC velocity blocks, Axis fraud checks)
- Classify decline type (soft vs hard, retryable vs terminal)
- Output: Additional context for LLM

**Rules Database** (JSON file):
```json
{
  "RBI_RECURRING_MANDATE_LIMIT": {
    "limit": 150000,
    "unit": "INR",
    "applies_to": ["debit_card", "credit_card"],
    "message_template": "Your bank blocked this because you exceeded the daily recurring payment limit of ₹1,50,000. Try again tomorrow or use a different payment method."
  },
  "UPI_DAILY_LIMIT": {
    "limit": 100000,
    "unit": "INR",
    "applies_to": ["upi"],
    "message_template": "You've hit your daily UPI transfer limit of ₹1,00,000. Try again after 24 hours or use a different payment method."
  },
  "HDFC_DEBIT_CARD_BLOCK": {
    "reason_codes": ["05", "51", "54"],
    "message_template": "HDFC blocked this transaction for security. Call HDFC at 1860-50-50-000 to unblock, then try again.",
    "retry_window_hours": 24
  }
}
```

**Output to LLM:**
```python
{
  "decline_info": {...},
  "applicable_rules": ["RBI_RECURRING_MANDATE_LIMIT"],
  "rule_context": {
    "limit_exceeded": 150000,
    "customer_amount": 180000,
    "recovery_suggestion": "use_different_method_or_wait"
  }
}
```

---

### 4. LLM Agent (Groq)

**File:** `services/llm_agent.py`

**Responsibility:**
- Take decline object + rule context
- Call Groq LLM API to generate explanation
- Format response for customer (SMS-friendly, <160 chars)
- Generate numbered recovery actions

**Prompt Template:**
```
You are a payment expert helping customers understand why their transactions failed.

Given:
- Error Code: {error_code}
- Error Description: {error_description}
- Payment Method: {payment_method}
- Card Network: {card_network}
- Issuer: {card_issuer}
- Applicable Rules: {rule_context}

Generate a customer-friendly explanation (max 150 chars) and 2-3 recovery actions in JSON format.

Format:
{
  "explanation": "Your bank blocked this for security. Call to unblock then retry.",
  "recovery_actions": [
    "action": "call_bank",
    "label": "Call your bank",
    "description": "Contact HDFC at 1860-50-50-000"
  ],
  "retry_recommended": true,
  "estimated_retry_window": "24 hours"
}
```

**Groq API Call:**
```python
import anthropic

client = anthropic.Anthropic(api_key="your-groq-key")
response = client.messages.create(
  model="groq-mixtral-8x7b-32768",  # or claude-sonnet-4-6
  max_tokens=500,
  messages=[{"role": "user", "content": prompt}]
)
```

---

### 5. Notification Service

**File:** `services/notification_service.py`

**Responsibility:**
- Format SMS message (concise, actionable, link)
- Queue SMS sending (async)
- Track delivery status
- Generate recovery link (signed, time-limited)

**SMS Template:**
```
Hey! Your ₹500 payment didn't go through.

Reason: Your bank blocked it for security.

→ Tap here to retry: app.com/retry/abc123xyz?exp=1hr

Questions? Contact us: support.razorpay.com
```

**Twilio Integration:**
```python
from twilio.rest import Client

client = Client(account_sid, auth_token)
message = client.messages.create(
  from_="+1234567890",
  to=customer_phone,
  body=sms_text
)
```

---

### 6. Database (PostgreSQL)

**Tables:**

#### `transactions`
```sql
id | razorpay_payment_id | customer_email | amount | error_code | error_reason | created_at
---|---|---|---|---|---|---
1 | pay_ABC123 | c@ex.com | 50000 | BAD_REQUEST_CODE_02 | InvalidTransaction | 2026-09-03 12:30:00
```

#### `decline_explanations`
```sql
id | transaction_id | explanation | recovery_actions | generated_at
---|---|---|---|---
1 | 1 | "Your bank blocked..." | ["call_bank", "retry_upi"] | 2026-09-03 12:30:05
```

#### `recovery_attempts`
```sql
id | transaction_id | retry_method | success | attempt_time
---|---|---|---|---
1 | 1 | card_retry | false | 2026-09-03 12:31:00
2 | 1 | upi_retry | true | 2026-09-03 12:32:00
```

#### `merchant_analytics`
```sql
merchant_id | date | total_failures | recovered_count | recovery_rate | top_decline_reason
---|---|---|---|---|---
mrn_XYZ | 2026-09-03 | 150 | 32 | 21.3% | BAD_REQUEST_CODE_02
```

---

### 7. Merchant Dashboard (Frontend)

**Technology:** React/Vue (optional for MVP, can use HTML template)

**Pages:**
1. **Dashboard (Home)**
   - Today's failures, recovery rate %, revenue recovered
   - Chart: Failures vs recovery rate (7-day trend)

2. **Decline Reasons (Drill-down)**
   - Top 10 decline reasons with frequency
   - Filter by date range, payment method
   - Click reason to see affected customers

3. **Recovery Analytics**
   - Total recovered transactions
   - Average recovery time
   - Recovery rate by decline reason

4. **Settings**
   - Configure SMS/WhatsApp notification (on/off)
   - Customize SMS message template
   - Webhooks configuration

---

### 8. Recovery Link Handler

**File:** `app.py` → route `/retry/<token>`

**Responsibility:**
- Validate recovery link (signature + expiry)
- Fetch original transaction & explanation
- Display customer-friendly recovery page
- Redirect to Razorpay checkout with pre-filled data

**Recovery Page Content:**
```html
<h1>Payment Recovery</h1>
<p><strong>What went wrong:</strong> Your bank blocked this for security.</p>
<p><strong>What to do:</strong></p>
<ol>
  <li>Call HDFC at 1860-50-50-000</li>
  <li>Ask to unblock international/cross-border transactions</li>
  <li>Come back here and retry</li>
</ol>
<button>↻ Retry Payment</button>
```

---

## Data Flow (Detailed)

### Timeline: Payment Fails → Customer Informed → Recovery Attempted

```
T+0s
  ├─ Customer's payment fails at Razorpay
  └─ Razorpay sends webhook to your endpoint

T+0.1s
  ├─ Webhook receiver validates signature
  ├─ Extract error code, payment method, issuer
  └─ Queue for processing

T+0.5s
  ├─ Rule engine checks if RBI/bank-specific rules apply
  ├─ Add context (limits, retry windows) to decline object
  └─ Pass to LLM

T+1-3s
  ├─ Groq LLM generates explanation + recovery actions
  ├─ Store in database (transactions, explanations tables)
  └─ Queue SMS notification

T+3-5s
  ├─ Twilio sends SMS to customer
  └─ Customer receives SMS with link

T+5-10min
  ├─ Customer taps link (expires in 1 hour)
  ├─ Recovery page loads with explanation
  └─ Customer clicks "Retry Payment"

T+10-15min
  ├─ Razorpay checkout opens (pre-filled)
  ├─ Customer enters OTP/3D Secure
  └─ Payment succeeds or fails

T+16min
  ├─ Razorpay webhook (payment.authorized or payment.failed)
  ├─ Update recovery_attempts table (success/failure)
  ├─ Update merchant analytics
  └─ If success: Mark as "Recovered"
```

---

## Integration Points with Razorpay

### 1. Webhook Subscription
**Setup (one-time):**
```
Razorpay Dashboard → Account Settings → Webhooks
→ Add: https://yourapp.com/webhook/razorpay/payment
→ Events: payment.failed
→ Active: Yes
```

### 2. API Keys
**Required:**
- API Key (public)
- API Secret (keep private, use for webhook signature verification)

**Usage:**
```python
import hmac
import json

def verify_webhook_signature(webhook_body, webhook_signature, secret):
    expected_signature = hmac.new(
      key=secret.encode(),
      msg=webhook_body.encode(),
      digestmod="sha256"
    ).hexdigest()
    return hmac.compare_digest(expected_signature, webhook_signature)
```

### 3. Webhook Signature Verification
**Header:** `X-Razorpay-Signature`

**Purpose:** Prove webhook is actually from Razorpay (not attacker)

```python
@app.route('/webhook/razorpay/payment', methods=['POST'])
def razorpay_webhook():
    webhook_body = request.data.decode()
    webhook_signature = request.headers.get('X-Razorpay-Signature')
    
    if not verify_webhook_signature(webhook_body, webhook_signature, RAZORPAY_SECRET):
        return {"error": "Invalid signature"}, 401
    
    # Process webhook...
```

### 4. Optional: Razorpay SMS Integration
**Alternative to Twilio:**
```python
# Use Razorpay SMS instead of Twilio (if merchant has SMS credits)
razorpay_client.sms.create(
  phone=customer_phone,
  message=sms_text
)
```

---

## Deployment & Hosting

### Option A: Heroku (Easiest for hackathon)
```bash
git push heroku main
# Auto-deploys Flask app
# Use PosgreSQL add-on
# Set env vars: RAZORPAY_SECRET, TWILIO_KEY, etc.
```

### Option B: AWS/GCP
```bash
- Lambda (webhook receiver)
- RDS PostgreSQL (database)
- API Gateway (webhook URL)
- CloudWatch (logging)
```

---

## Security Considerations

### 1. Webhook Signature Verification
✓ Always verify `X-Razorpay-Signature` header

### 2. PII Protection
✓ Never log full card numbers (store last 4 digits only)
✓ Encrypt customer email/phone in database
✓ Use HTTPS only

### 3. SMS Compliance
✓ Include "TRAI Compliant" senders
✓ Include unsubscribe option
✓ Honor opt-in preferences

### 4. Rate Limiting
✓ Limit Groq API calls (cost control)
✓ Limit SMS sending (per customer per day)

---

## Monitoring & Logging

### Metrics to Track
- Webhook latency (time to process)
- LLM API latency (Groq response time)
- SMS delivery rate (% successfully sent)
- Recovery rate (% of customers who retried successfully)
- Customer satisfaction (post-SMS survey)

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Webhook received: {payment_id}")
logger.error(f"LLM call failed: {error_message}")
logger.warning(f"SMS delivery failed: {customer_email}")
```

---

## Testing Strategy

### Unit Tests
- Test decline code extraction
- Test rule engine logic (RBI limits, velocity blocks)
- Test LLM prompt formatting

### Integration Tests
- Mock Razorpay webhook → verify SMS sent
- Mock SMS delivery → verify database updated
- Mock customer link click → verify recovery page loads

### End-to-End Tests
- Live webhook (test mode) → full pipeline → SMS received

