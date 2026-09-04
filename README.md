# Razorpay ZeroDrop ⚡

An AI-powered payment intelligence layer that intercepts failed Razorpay transactions, translates cryptic error codes into empathetic plain-English explanations, and guides customers to instant recovery — reducing transaction abandonment to zero and eliminating support ticket overhead.

**Project Name:** Razorpay ZeroDrop (formerly Payment Failure Whisperer)  
**Built for:** Razorpay Buildathon 2026 (Open Track)  
**Status:** ✅ Fully Built & Verified (24/24 Automated Tests Passing)

---

## 🚀 Key Features

1. **Authentic Razorpay Error Taxonomy (`data/decline_rules.json`)**:
   - 20 real error reasons verified directly against Razorpay's official documentation (`https://razorpay.com/docs/errors/payments/list/`).
   - Mapped with official `error_code`, `error_source`, `error_step`, and `error_description`.

2. **Self-Contained Sandbox Checkout Simulation (`/` and `/sandbox`)**:
   - Built specifically for demoing without requiring a registered commercial business PAN/GST KYC.
   - Interactive checkout modal (Card & UPI) with an **Operator Failure Scenario Selector** (9+ presets).
   - Generates and dispatches authentic Razorpay `payment.failed` webhook payloads signed with HMAC-SHA256.
   - Displays real-time bank processing states, gateway decline banners, and AI Whisperer recovery recommendations.

3. **Empathetic AI Intelligence & Regulatory Awareness**:
   - Powered by **Groq Llama-3** (`llama-3.3-70b-versatile`) for sub-second plain-English translations.
   - Bank & regulatory rule engine evaluating **RBI Recurring Mandate Limits** (₹15,000 threshold), UPI daily limits, and bank-specific customer care helplines (HDFC, ICICI, SBI, Axis, Kotak).
   - **Fail-Safe Fallback**: Automatic deterministic fallback if Groq API is unconfigured or unreachable.

4. **Interactive Smartphone Mockup (SMS Preview)**:
   - On-screen phone widget displaying TRAI-compliant transactional SMS (`VK-RZRPAY`) with clickable recovery link.

5. **Customer Recovery Portal (`/retry/<token>`)**:
   - Time-limited cryptographically signed recovery tokens (`itsdangerous`) expiring after 60 minutes.
   - One-click alternate payment retries (e.g. switch to UPI).

6. **Merchant Analytics Dashboard (`/dashboard`)**:
   - Live metrics tracking Total Failures, Recovery Rate %, Recovered Revenue vs At-Risk Revenue, Decline Reason breakdowns, and Transaction Logs.

---

## ⚡ Quick Start (Single Command Run)

### 1. Clone & Installation
```bash
git clone https://github.com/Ayaaannn-0/Razorpay-ZeroDrop.git
cd Razorpay-ZeroDrop
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)
Copy `.env.example` to `.env`. (The app works immediately out-of-the-box with zero-config SQLite and fallback rule generation even without API keys):
```bash
cp .env.example .env
```
Add your `GROQ_API_KEY` for live AI generation if available.

### 3. Run Application
```bash
python app.py
```
Open your browser at:
- **Sandbox Checkout Simulator:** [http://127.0.0.1:5000/zerodrop](http://127.0.0.1:5000/zerodrop)
- **Merchant Analytics Dashboard:** [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
- **Health Check:** [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

---

## 🧪 Running Automated Tests

Run the full pytest suite (24 unit and integration tests):
```bash
pytest tests/ -v
```

---

## 🛠️ CLI Mock Webhook Tester

To test the `/webhook/razorpay/payment` endpoint directly from terminal:
```bash
python scripts/mock_webhook.py --file demo/sample_payloads/insufficient_funds.json
python scripts/mock_webhook.py --file demo/sample_payloads/rbi_mandate_limit.json
```

---

## 🎤 Presentation & Demo Guide

Refer to [`demo/demo_script.md`](demo/demo_script.md) for the complete 3-minute spoken pitch, live demo walkthrough steps, and judge Q&A preparation.

---

## 📜 Legal & Compliance Awareness
- **Data Privacy (DPDP Act, 2023)**: Customer phone and email are masked in storage and logs (`+91 98****3210`).
- **RBI Regulations**: Full card numbers, CVVs, and OTPs are never stored or logged.
- **TRAI Compliance**: Transactional SMS alerts follow DLT formatting guidelines.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).

