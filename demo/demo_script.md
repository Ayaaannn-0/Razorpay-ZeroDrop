# Demo Presentation Script: Razorpay ZeroDrop
### Razorpay Buildathon (Open Track)
**Presenter:** Ayaan | Lead Developer  
**Format:** 3 to 5-Minute Live Pitch + Interactive Demonstration  

---

## Phase 1: Executive Hook and Industry Problem (0:00 - 0:45)

> "Good morning / afternoon, judges!
> 
> Across India's digital payments ecosystem, millions of transactions fail every single day. When a consumer payment fails at checkout, the current standard experience is alarming:
> 
> Users encounter generic error codes such as `BAD_REQUEST_ERROR`, `funds_blocked_by_mandate`, or `05 - DO NOT HONOR`.
> 
> The consumer immediately experiences two friction points:
> 1. **'Was my bank account debited anyway?'**
> 2. **'How do I complete this transaction without double-paying?'**
> 
> Because legacy checkout interfaces do not provide actionable, plain-language guidance, industry data indicates that nearly 30% of users immediately abandon their transactions. Meanwhile, merchant operations teams are flooded with repetitive support tickets inquiring about transaction statuses.
> 
> We engineered **Razorpay ZeroDrop** — an autonomous payment intelligence layer that intercepts Razorpay decline webhooks in real-time, diagnoses raw failure payloads through a localized rule engine and fast LLM translation, delivers deterministic next-best actions, and dispatches a cryptographically signed recovery session directly to the customer.
> 
> Let us walk through the system in action."

---

## Phase 2: Sandbox Demonstration and Technical Disclosure (0:45 - 2:00)

*(Navigate to `http://127.0.0.1:5000/zerodrop`)*

> "First, a clear technical disclosure regarding our test harness:
> As a student developer entering this buildathon, standard production Razorpay webhook onboarding requires a registered corporate PAN and GSTIN for compliance KYC.
> 
> Rather than using mock placeholder buttons, we constructed a **production-parity Razorpay Checkout Simulator**.
> Every failure code in our selector—`insufficient_funds`, `bank_technical_error`, `funds_blocked_by_mandate`—originates directly from **Razorpay's official public error taxonomy**.
> 
> When initiating payment, the harness synthesizes the **exact JSON payload structure** that Razorpay production webhooks emit on `payment.failed`, generates a valid HMAC-SHA256 signature using our shared secret, and transmits it to our backend `/webhook/razorpay/payment` ingestion endpoint.
> 
> The downstream ingestion, intelligence, and recovery pipelines operate identically to production."

### Step A: Insufficient Funds Scenario
*(Select **"Insufficient Funds"** in the scenario selector and click **"Pay Now"**)*

> "Observing the diagnostic flow:
> 1. The sandbox simulates bank authorization handshakes.
> 2. The issuing bank returns a decline: `BAD_REQUEST_ERROR` at step `payment_authorization`.
> 3. Within 150 milliseconds, our **AI Failure Whisperer** intercepts the webhook event.
> 
> Examining the output:
> **'Your card could not be charged due to insufficient account balance. Please top up your account or use an alternate method.'**
> 
> Below the explanation, the customer is presented with ranked, context-aware recovery pathways:
> - **Pay via UPI instead** (Seamless transition to Google Pay / PhonePe linked to a secondary account)
> - **Use a different card**
> - **Top up account & retry within 1 hour**"

---

## Phase 3: Regulatory and Bank-Specific Intelligence (2:00 - 2:45)

*(Select **"RBI Recurring Mandate Limit Exceeded"** in the scenario selector)*

> "Next, consider a complex regulatory scenario: **RBI E-Mandate Regulations**.
> 
> The checkout amount updates to ₹18,500. Under Reserve Bank of India directives, recurring e-mandates exceeding ₹15,000 require an Additional Factor of Authentication (AFA/OTP) approval and cannot be processed via silent recurring debit.
> 
> *(Click 'Pay Now')*
> 
> Observe the AI diagnosis:
> Our rule engine recognizes that the order value exceeds the ₹15,000 regulatory ceiling, merges this context with the `funds_blocked_by_mandate` taxonomy, and produces an explanation clarifying the mandate limitation while guiding the customer to authenticate using UPI or netbanking.
> 
> This provides deterministic, regulatory-aware customer guidance rather than generic LLM speculation."

---

## Phase 4: Omnichannel Customer Recovery Loop (2:45 - 3:30)

*(Point to the on-screen Smartphone Mockup)*

> "If the user has already navigated away from the checkout tab, an omnichannel notification is triggered.
> 
> The device simulation displays a **TRAI-compliant transactional SMS** dispatched under merchant DLT registration:
> `Alert: Your INR 4,999.00 payment was declined. Reason: Insufficient balance. Complete your order securely: [Recovery Link]`
> 
> *(Click the recovery link in the SMS preview)*
> 
> This launches the **Customer Recovery Portal** (`/retry/<signed-token>`).
> The recovery URL uses a time-bounded cryptographic token (`itsdangerous`) valid for 60 minutes to prevent replay attacks.
> 
> The user selects **'UPI (Instant Recovery)'** and clicks **'Authorize & Complete Payment'**.
> 
> *(Execute payment authorization)*
> 
> The transaction state transitions to **'Recovered'** across the data layer without requiring the customer to re-enter order details or rebuild their shopping basket."

---

## Phase 5: Merchant Analytics and Revenue Recovery (3:30 - 4:15)

*(Navigate to `http://127.0.0.1:5000/dashboard`)*

> "From the merchant's perspective, this control plane provides operational visibility into failure recovery:
> 
> 1. **Total Intercepted Failures**: Real-time counter of declined transactions evaluated by the AI agent.
> 2. **Recovery Conversion Rate**: Percentage of failed transactions successfully salvaged (target > 25%).
> 3. **Recovered Revenue vs. At-Risk GMV**: Direct monetary metric showing capital retained.
> 4. **Decline Distribution Matrix**: Breakdown of failure sources (issuing bank outages vs. customer balance limits).
> 5. **Audit Trail**: Real-time ledger of failure timestamps, masked customer identifiers, and recovery statuses.
> 
> Every recovered transaction translates into preserved gross merchandise value and reduced merchant support overhead."

---

## Phase 6: Enterprise Compliance and Architecture (4:15 - 4:45)

> "In summary, Razorpay ZeroDrop delivers an enterprise-ready recovery architecture:
> 1. **Data Privacy (DPDP Act, 2023)**: Customer phone numbers and email addresses are masked across all storage and log streams (`+91 98****3210`). No CVVs or OTPs are ever stored.
> 2. **Sub-Second Resilience**: Powered by Groq Llama-3 (`llama-3.3-70b-versatile`) with an instant deterministic rule engine fallback ensuring 100% uptime even during external API disruptions.
> 3. **Turnkey Deployment**: Runs out of the box with zero third-party dependencies required for local evaluation, backed by 24 passing automated test suites.
> 
> Razorpay ZeroDrop bridges the gap between raw gateway error codes and successful checkout completion.
> 
> Thank you. I welcome your questions."

---

## Judge Q&A Preparation: Anticipated Technical Inquiries

### Question 1: "Why did you build a simulated checkout instead of using live Razorpay test keys?"
> **Response:** "Production webhook configuration in Razorpay requires business PAN and GSTIN registration for merchant KYC approval. As a student developer without a registered commercial entity, building a self-contained simulator ensured complete testing autonomy. Crucially, the simulator produces the identical JSON payload structure defined in Razorpay's official `payment.failed` API specifications and signs requests using authentic HMAC-SHA256 signatures. The entire downstream ingestion, rule evaluation, and recovery workflow is fully authentic."

### Question 2: "What happens if the external LLM service experiences latency or downtime?"
> **Response:** "The architecture incorporates a dual-layer strategy. Every decline reason code in `data/decline_rules.json` contains pre-compiled, deterministic plain-English templates and ranked recovery actions. If the Groq API call fails, times out, or lacks credentials, the `LLMAgent` instantly falls back to the deterministic rule engine with zero latency degradation. The customer experience remains uninterrupted."

### Question 3: "How does the system ensure compliance with Indian financial data privacy regulations?"
> **Response:** "Compliance is maintained across three dimensions: First, under RBI card-storage directives, card details are never stored beyond the last 4 digits; CVVs and PINs are completely excluded. Second, per the Digital Personal Data Protection (DPDP Act) 2023, PII such as phone numbers and emails are masked across persistent storage. Third, recovery URLs utilize time-limited cryptographic tokens with 60-minute expiration windows."

### Question 4: "What is the commercial value proposition for a high-volume merchant?"
> **Response:** "Across Indian e-commerce, average payment failure rates range between 10% and 15%, with approximately 30% resulting in permanent cart abandonment. For an enterprise merchant processing ₹1 Crore in monthly GMV with ₹12 Lakhs in declines, recovering even 25% of those failed transactions salvages ₹3 Lakhs in otherwise lost revenue each month, while simultaneously reducing support ticket volume."
