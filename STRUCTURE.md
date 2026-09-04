# Project Structure

This is the folder layout to actually build in. Create it exactly like this so the codebase stays organized and demo-ready.

```
payment-failure-whisperer/
│
├── PRD.md                          # What & why (this doc set)
├── ARCHITECTURE.md                 # How it's built
├── STRUCTURE.md                    # This file
├── LEGAL_COMPLIANCE.md             # Privacy/data-handling notes
├── RAZORPAY_INTEGRATION.md         # Step-by-step Razorpay setup
├── README.md                       # Quick start for judges/reviewers
├── .env.example                    # Template for secrets (never commit real .env)
├── .gitignore
├── requirements.txt                # Python dependencies
│
├── app.py                          # Flask entry point, routes
├── config.py                       # App config (loads from .env)
│
├── services/
│   ├── __init__.py
│   ├── decline_extractor.py        # Parses Razorpay webhook payload
│   ├── rule_engine.py              # RBI/bank-specific decline rules
│   ├── llm_agent.py                # Groq API calls, prompt building
│   ├── notification_service.py     # SMS/WhatsApp sending
│   └── recovery_link.py            # Signed retry-link generation/validation
│
├── models/
│   ├── __init__.py
│   ├── transaction.py              # DB model: transactions table
│   ├── decline_explanation.py      # DB model: explanations table
│   └── recovery_attempt.py         # DB model: retry attempts table
│
├── data/
│   └── decline_rules.json          # Rule engine's knowledge base (RBI limits, bank codes)
│
├── templates/                      # If using Flask's built-in HTML templates
│   ├── recovery_page.html          # Customer-facing "why it failed" page
│   └── dashboard.html              # Merchant analytics view (MVP can be simple)
│
├── static/
│   ├── css/
│   └── js/
│
├── tests/
│   ├── __init__.py
│   ├── test_decline_extractor.py
│   ├── test_rule_engine.py
│   └── test_webhook.py
│
├── scripts/
│   └── mock_webhook.py             # Sends a fake Razorpay webhook for local testing
│
└── demo/
    ├── demo_script.md              # What you'll say during the live/recorded demo
    └── sample_payloads/            # Sample failed-payment JSON payloads to demo with
```

---

## Build Order (do it in this sequence)

1. **`data/decline_rules.json`** — write out 15-20 real Razorpay error codes with explanations first. This is your actual research/domain knowledge — do this before any code.
2. **`services/decline_extractor.py`** — parse a sample webhook payload into a clean object.
3. **`services/rule_engine.py`** — match extracted decline against `decline_rules.json`.
4. **`services/llm_agent.py`** — send decline + rule context to Groq, get back explanation + actions.
5. **`app.py`** — wire up the `/webhook/razorpay/payment` route that calls the above in sequence.
6. **`scripts/mock_webhook.py`** — a script to POST fake payloads to your local Flask server so you can test without a live Razorpay account.
7. **`services/notification_service.py`** — SMS sending (or just print/log it for the demo if Twilio setup is too slow).
8. **`templates/recovery_page.html`** + **`services/recovery_link.py`** — the page a customer lands on.
9. **`templates/dashboard.html`** — simple merchant view, even a static table is fine for MVP.
10. **`demo/demo_script.md`** — write this LAST, once you know exactly what works, so your live demo never touches a broken path.

Don't build the dashboard or the WhatsApp integration until steps 1-6 work end-to-end. A working core beats a half-built full system every time in judging.
