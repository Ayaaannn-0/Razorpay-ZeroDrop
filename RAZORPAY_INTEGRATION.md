# Razorpay Integration Guide

Step-by-step, assuming you've never touched Razorpay's API before.

---

## Step 1: Create a Razorpay Account (Test Mode)

1. Go to https://dashboard.razorpay.com/signup
2. Sign up — you can use **Test Mode** without any real business/KYC docs
3. Once logged in, make sure the toggle in the top-left says **"Test Mode"** (not Live Mode) — this matters, test mode gives you fake API keys you can use safely

---

## Step 2: Get Your API Keys

1. Dashboard → Settings → API Keys
2. Click "Generate Test Key"
3. You'll get:
   - **Key ID** (public, starts with `rzp_test_...`)
   - **Key Secret** (private — never commit this to GitHub)

Save these somewhere safe. You'll put them in a `.env` file (never hardcode them in your code).

---

## Step 3: Understand Webhooks (the core integration point)

A **webhook** is just Razorpay automatically sending a POST request to a URL you control, whenever something happens (like a payment failing). You don't poll Razorpay asking "did anything fail?" — they tell you.

### Setting up a webhook:
1. Dashboard → Settings → Webhooks → Add New Webhook
2. **Webhook URL:** this needs to be a publicly accessible URL. Since you're developing locally, use **ngrok** (see Step 4) to expose your local Flask server temporarily
3. **Active Events:** check `payment.failed`
4. **Secret:** Razorpay generates a webhook secret — save this, you'll use it to verify incoming requests are actually from Razorpay (not a fake attacker request)

---

## Step 4: Expose Your Local Server (ngrok)

Since your Flask app runs on `localhost:5000` and Razorpay can't reach your laptop directly:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000
```

This gives you a public URL like `https://abc123.ngrok.io` — put `https://abc123.ngrok.io/webhook/razorpay/payment` as your webhook URL in Step 3.

**Note:** ngrok URLs change every time you restart it (unless you pay for a static domain). Update the webhook URL in Razorpay's dashboard each time, or use ngrok's free static domain feature.

---

## Step 5: Verify Webhook Signatures (Security)

Every webhook Razorpay sends includes a header `X-Razorpay-Signature`. You MUST verify this to confirm the request is genuinely from Razorpay.

```python
import hmac
import hashlib

def verify_signature(payload_body: str, received_signature: str, webhook_secret: str) -> bool:
    expected_signature = hmac.new(
        key=webhook_secret.encode(),
        msg=payload_body.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, received_signature)
```

If signature doesn't match → reject the request (return 401). This stops anyone from spamming your endpoint with fake "payment failed" events.

---

## Step 6: Trigger a Test Failed Payment

You need actual failed payments to test with. Razorpay provides **test card numbers** that simulate specific failure types:

| Card Number | Simulates |
|---|---|
| 4000 0000 0000 0002 | Generic decline |
| 4000 0000 0000 9995 | Insufficient funds |
| 4000 0000 0000 0069 | Expired card |
| 4000 0000 0000 0119 | Processing error |

Full list: https://razorpay.com/docs/payments/payments/test-card-upi-details/

**How to use them:**
1. Create a test payment link or checkout form using your test Key ID
2. Use one of the above card numbers at checkout
3. The payment fails → Razorpay fires the `payment.failed` webhook → hits your ngrok URL → your Flask app receives it

---

## Step 7: Sample Webhook Payload You'll Receive

```json
{
  "entity": "event",
  "account_id": "acc_ABC123",
  "event": "payment.failed",
  "contains": ["payment"],
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_XYZ789",
        "amount": 50000,
        "currency": "INR",
        "status": "failed",
        "method": "card",
        "card_id": "card_ABC123",
        "email": "test@example.com",
        "contact": "+919876543210",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment failed due to insufficient funds in the customer's account.",
        "error_source": "bank",
        "error_step": "payment_authorization",
        "error_reason": "insufficient_funds",
        "created_at": 1735689600
      }
    }
  }
}
```

This is your ground truth — `error_code`, `error_description`, and `error_reason` are the fields your `decline_extractor.py` needs to pull out.

---

## Step 8: If You Don't Want to Deal With Live Webhooks During the Demo

Live demos are risky. Build `scripts/mock_webhook.py` that POSTs a payload identical to the real Razorpay format directly to your local Flask endpoint — this lets you demo the *entire* pipeline (explanation generation, SMS, dashboard) without depending on ngrok/live Razorpay working perfectly on stage.

```python
import requests
import json

with open('demo/sample_payloads/insufficient_funds.json') as f:
    payload = json.load(f)

response = requests.post(
    'http://localhost:5000/webhook/razorpay/payment',
    json=payload,
    headers={'X-Razorpay-Signature': 'mock_signature_for_local_testing'}
)
print(response.json())
```

For the actual demo, you can show BOTH: a live ngrok-connected test payment failing (impressive if it works), AND have the mock script ready as backup.

---

## Step 9: Official Docs You'll Actually Need

- Webhooks overview: https://razorpay.com/docs/webhooks/
- Payment error codes: https://razorpay.com/docs/errors/payments/list/
- Test card/UPI details: https://razorpay.com/docs/payments/payments/test-card-upi-details/
- Python SDK (optional, you can also just use `requests`): https://github.com/razorpay/razorpay-python

---

## Common Gotchas

1. **Webhook secret ≠ API Key Secret** — these are two different secrets, don't mix them up
2. **ngrok free tier URL changes on restart** — re-update your webhook URL each session, or grab ngrok's free static domain
3. **Test mode webhooks only fire for test mode payments** — make sure you're not accidentally trying to trigger them with live-mode test cards
4. **Flask needs to return a 200 quickly** — Razorpay expects a fast response; do heavy processing (LLM calls, SMS) async/in a background task if possible, otherwise Razorpay may retry the webhook thinking it failed
