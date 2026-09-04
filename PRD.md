# Product Requirements Document: Payment Failure Whisperer

## Executive Summary
Payment Failure Whisperer is an AI-powered agent that intercepts failed Razorpay transactions and translates cryptic error codes into customer-friendly explanations, then recommends the optimal retry method or alternative payment approach. It reduces transaction abandonment and support ticket volume by helping customers self-serve recovery.

---

## Problem Statement

### Current Pain Points
1. **Customer Confusion** — Payment failures show technical error codes (e.g., "BAD_REQUEST_CODE_02") with no explanation
2. **Support Bottleneck** — Merchants receive support tickets from confused customers asking "Why was I declined?"
3. **Revenue Loss** — Customers abandon after a single failure instead of retrying with alternate payment method
4. **Bank-Specific Rules** — RBI mandate limits, velocity blocks, and issuer-specific blocks have no customer guidance

### Market Validation
- Razorpay customer reviews cite "no explanation for declined payments" as top complaint
- Adyen/Stripe only provide merchant-facing decline codes, not customer explanations
- Industry research: ~30% of declined transactions could be recovered with proper customer guidance

---

## Solution Overview

Payment Failure Whisperer provides:
1. **Real-time Decline Translation** — Takes raw Razorpay error code + transaction metadata → generates human-friendly explanation
2. **Bank-Specific Context** — Recognizes RBI rules, HDFC velocity blocks, UPI limits, etc.
3. **Smart Recovery Prompts** — Suggests "try UPI instead," "update your billing address," "call your bank," etc.
4. **Merchant Dashboard** — Shows recovery metrics (e.g., "recovered 23 transactions this week")

---

## Users & Personas

### Primary Users
1. **End Customers** — Receive SMS/WhatsApp link when payment fails → tap to see explanation + retry
2. **Merchants** — Dashboard showing failed transactions, recovery success rate, top failure reasons

### Secondary Users
1. **Razorpay Support Team** — Can reference agent outputs in customer support responses
2. **Razorpay Product Team** — Analytics on common failure patterns feed product roadmap

---

## Key Features

### Feature 1: Decline Code Translator
- **Input:** Razorpay error code, payment method, card network, amount
- **Output:** Plain-English explanation (e.g., "Your bank blocked this because you exceeded daily UPI transaction limit of ₹1,00,000")
- **Tech:** LLM + rule-based logic for RBI/bank-specific rules

### Feature 2: Retry Recommender
- **Logic:** If card declined due to insufficient funds → suggest "Check your balance & retry" or "Try UPI"
- **Logic:** If fraud suspected → suggest "Call your bank to unblock, then retry"
- **Output:** Ranked list of next actions

### Feature 3: Customer Notification Channel
- **SMS/WhatsApp Link** — "Your payment didn't go through. Tap to see why & try again"
- **Embedded Widget** — For merchants using Razorpay Checkout (show on failure screen)
- **Email** — Follow-up recovery email for high-value transactions

### Feature 4: Merchant Analytics Dashboard
- **Metrics:** Total failures, recovery rate by decline reason, refund/retry trends
- **Drill-down:** See top customers affected by each failure reason
- **Export:** CSV of failed transactions + recovery attempts

---

## Technical Architecture

### High-Level Flow
```
Razorpay Payment Fails 
    ↓
Razorpay Webhook → Your Backend (Flask)
    ↓
Extract: Error Code, Card Network, Amount, Customer Email
    ↓
LLM Agent (Groq) + Rule Engine
    ↓
Generate Explanation + Recovery Actions
    ↓
Send SMS/WhatsApp + Update Dashboard
    ↓
Customer Taps Link → Redirected to Payment Retry
    ↓
If Successful → Mark as "Recovered"
```

### Technology Stack
- **Backend:** Flask (Python)
- **LLM:** Groq API (fast inference for real-time explanation)
- **Database:** PostgreSQL (store transactions, recovery logs)
- **Webhook Handler:** Razorpay webhooks (payment.failed event)
- **SMS/WhatsApp:** Twilio or Razorpay SMS product
- **Frontend Dashboard:** React/Vue (merchant analytics)

---

## Implementation Phases

### Phase 1: MVP (Buildathon Scope)
- [x] Basic decline code translator (top 20 error codes)
- [x] Groq integration for explanation generation
- [x] Webhook receiver (mock Razorpay events)
- [x] SMS notification sender (template-based)
- [x] Simple metrics dashboard (failures per day, recovery rate %)

### Phase 2: Production (Post-Buildathon)
- [ ] Full decline code library (100+ codes)
- [ ] Bank-specific rule engine (HDFC, ICICI, SBI, Axis)
- [ ] RBI mandate logic (₹15K auto-debit rules)
- [ ] WhatsApp integration via Razorpay
- [ ] Customer retry link (redirects to payment re-attempt)

### Phase 3: Enterprise (Future)
- [ ] Multi-merchant dashboard
- [ ] API for third-party integrations
- [ ] Custom decline explanations per merchant brand

---

## Success Metrics

### For Customers
- **Clarity Score** — Customer understands why payment failed (survey post-notification)
- **Retry Rate** — % of customers who attempt payment again after notification
- **Recovery Rate** — % of retries that succeed (target: 15-25% of failed transactions)

### For Merchants
- **Support Ticket Reduction** — Fewer "Why was I declined?" tickets
- **Revenue Recovery** — $ amount recovered from re-attempted transactions
- **Merchant NPS** — Satisfaction with payment experience

### For Razorpay
- **Platform Metrics** — Settlement success rate, transaction volume, customer satisfaction
- **Competitive Advantage** — Differentiate vs Stripe/Adyen on customer experience

---

## Non-Functional Requirements

### Performance
- **Latency:** Webhook → Explanation ready in <5 seconds
- **Accuracy:** Explanation matches actual decline reason >95% of time
- **Availability:** 99.9% uptime for webhook receiver

### Security & Compliance
- **PII Handling:** Never log full card numbers, only last 4 digits
- **Compliance:** GDPR (customer email), India TRAI (SMS regulations)
- **Audit Trail:** All transactions logged for compliance review

### Scalability
- **Volume:** Handle 1M+ transaction failures/day without degradation
- **Concurrency:** Support 10K+ concurrent webhook payloads

---

## Out of Scope (Phase 1)

- Real-time chat support integration
- Predictive decline (preventing failures before they happen)
- ML model training on Razorpay's historical data
- Multi-language support (English only for MVP)
- White-label for other payment gateways

---

## Acceptance Criteria

### Technical
- [ ] Webhook receiver accepts Razorpay payment.failed events
- [ ] LLM generates explanations for 20+ decline codes within 5s
- [ ] SMS sent successfully to customer email/phone
- [ ] Dashboard shows real-time metrics
- [ ] Code passes security review (no PII leaks)

### Product
- [ ] Explanation clarity >4/5 in user testing
- [ ] Recovery rate >15% in pilot
- [ ] Merchants report reduced support load

### Compliance
- [ ] SMS conforms to TRAI rules (opt-in, unsubscribe link)
- [ ] PII handling meets GDPR/India privacy laws
- [ ] Audit logs available for compliance review

---

## Timeline

- **Week 1:** Setup, architecture design, mock data
- **Week 2:** Flask webhook receiver + Groq integration
- **Week 3:** SMS integration + basic dashboard
- **Week 4:** Testing, demo video, polish + submit

---

## References & Research

- Razorpay Error Codes: https://razorpay.com/docs/errors/payments/list/
- RBI Recurring Mandate Rules: Various merchant complaints on Shopify forums
- Industry Benchmarks: Stripe/Adyen decline research, Ethoca fraud data
- Customer Feedback: Razorpay Trustpilot reviews (payment failure complaints)

